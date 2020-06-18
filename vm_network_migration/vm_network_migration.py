# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" This script is used to migrate a GCP instance from its legacy network to a
subnetwork mode network.

Ihe Google API python client module is imported to manage the GCP Compute Engine
 resources.

Before running:
    1. If not already done, enable the Compute Engine API
       and check the quota for your project at
       https://console.developers.google.com/apis/api/compute
    2. This sample uses Application Default Credentials for authentication.
       If not already done, install the gcloud CLI from
       https://cloud.google.com/sdk and run
       `gcloud beta auth application-default login`.
       For more information, see
       https://developers.google.com/identity/protocols/application-default-credentials
    3. Install the Python client library for Google APIs by running
       `pip install --upgrade google-api-python-client`

Run the script by terminal, for example:
     python3 vm_network_migration.py --project_id=test-project
     --zone=us-central1-a --original_instance_name=instance-legacy
     --new_instance_name=vm_network_migration-new --network=tests-network
     --subnetwork=tests-network --preserve_internal_ip=False
     --preserve_external_ip = False --preserve_alias_ip_ranges=False

"""
import copy
import time
import warnings

import google.auth
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from vm_network_migration.errors import *


def stop_instance(compute, project, zone, instance) -> dict:
    """ Stop the instance.

    Args:
        compute: google API compute engine service
        project: project ID
        zone: zone of the VM
        instance: name of the VM

    Returns:
        a deserialized object of the response

    Raises:
        googleapiclient.errors.HttpError: invalid request
    """
    return compute.instances().stop(
        project=project,
        zone=zone,
        instance=instance).execute()


def start_instance(compute, project, zone, instance) -> dict:
    """ Start the instance.

    Args:
        compute: google API compute engine service
        project: project ID
        zone: zone of the VM
        instance: name of the VM

    Returns:
        a deserialized object of the response

    Raises:
        googleapiclient.errors.HttpError: invalid request
    """
    return compute.instances().start(
        project=project,
        zone=zone,
        instance=instance).execute()


def retrieve_instance_template(compute, project, zone, instance) -> dict:
    """ Get the instance template from an instance.

    Args:
        compute: google API compute engine service
        project: project ID
        zone: zone of the VM
        instance: name of the VM

    Returns:
        instance template

    Raises:
        googleapiclient.errors.HttpError: invalid request
    """
    return compute.instances().get(
        project=project,
        zone=zone,
        instance=instance).execute()


def get_disks_info_from_instance_template(instance_template) -> list:
    """ Get disks' info from the instance template.

    Args:
        instance_template: a dict of the instance template

    Returns:
        a list of disks' info

    Raises:
        AttributeNotExistError: No disks on the VM
    """
    if 'disks' not in instance_template:
        raise AttributeNotExistError('No disks are attached on the VM')
    return instance_template['disks']


def detach_disk(compute, project, zone, instance, disk) -> dict:
    """ Detach a disk from the instance

    Args:
        compute: google API compute engine service
        project: project ID
        zone: zone of the VM
        instance: name of the VM
        disk: name of the disk

    Returns:
        a deserialized object of the response

    Raises:
        googleapiclient.errors.HttpError: invalid request
    """
    return compute.instances().detachDisk(
        project=project,
        zone=zone,
        instance=instance,
        deviceName=disk).execute()


def attach_disk(compute, project, zone, instance, disk_info):
    """Attach a disk to the instance

    Args:
        compute: google API compute engine service
        project: project ID
        zone: zone of the VM
        instance: name of the VM
        disk_info: deserialized info of the disk

    Returns:
        a deserialized object of the response

    Raises:
        googleapiclient.errors.HttpError: invalid request
    """
    return compute.instances().attachDisk(
        project=project,
        zone=zone,
        instance=instance,
        forceAttach=True,
        body=disk_info).execute()


def get_network(compute, project, network) -> dict:
    """ Get the network information.

        Args:
            compute: google API compute engine service
            project: project ID
            network: name of the network

        Returns:
            a dict of the network information

        Raises:
            googleapiclient.errors.HttpError: invalid request
    """
    return compute.networks().get(
        project=project,
        network=network).execute()


def generate_new_network_info(compute, project, region, network,
                              subnetwork) -> dict:
    """ Generate a network information dict
        based on the provided network and subnetwork

        Args:
            compute: google API compute engine service
            project: project ID
            region: region of the subnetwork
            network: network name
            subnetwork: subnetwork name

        Returns:
            a dict of the new network interface

        Raises:
            googleapiclient.errors.HttpError: invalid request
    """
    network_parameters = get_network(compute, project, network)
    network_link = network_parameters['selfLink']
    subnetwork_link = region + '/subnetworks/' + subnetwork
    network_info = {}
    network_info['network'] = network_link
    network_info['subnetwork'] = subnetwork_link
    return network_info


def modify_instance_template_with_new_network(instance_template, new_instance,
                                              new_network_info) -> dict:
    """ Modify the instance template with the new network interface

        Args:
            instance_template: dictionary of the instance template
            new_instance: name of the new VM
            new_network_info: dictionary of the new network interface

        Returns:
            a dict of the new network interface
    """
    if 'networkInterfaces' not in instance_template:
        raise AttributeNotExistError(
            'networkInterfaces is not in instance_template')
    elif not isinstance(instance_template['networkInterfaces'], list):
        raise InvalidTypeError('Invalid value type')
    if 'name' not in instance_template:
        raise AttributeNotExistError('name is not in instance_template')
    instance_template['networkInterfaces'][0] = new_network_info
    instance_template['name'] = new_instance
    return instance_template


def create_instance(compute, project, zone, instance_template) -> dict:
    """ Create the instance using instance template

        Args:
            compute: google API compute engine service
            project: project ID
            zone: zone of the VM
            instance_template: instance template

        Returns:
            a dict of the new network interface

        Raises:
            googleapiclient.errors.HttpError: invalid request
    """
    return compute.instances().insert(
        project=project,
        zone=zone,
        body=instance_template).execute()


def delete_instance(compute, project, zone, instance) -> dict:
    """ delete the instance

        Args:
            compute: google API compute engine service
            project: project ID
            zone: zone of the VM
            instance: name of the instance

        Returns:
            a deserialized object of the response

        Raises:
            googleapiclient.errors.HttpError: invalid request
    """
    return compute.instances().delete(
        project=project,
        zone=zone,
        instance=instance).execute()


def wait_for_zone_operation(compute, project, zone, operation):
    """ Keep waiting for a zone operation until it finishes

        Args:
            compute: google API compute engine service
            project: project ID
            zone: zone of the VM
            operation: name of the Operations resource to return

        Returns:
            a deserialized object of the response

        Raises:
            ZoneOperationsError: if the operation has an error
            googleapiclient.errors.HttpError: invalid request
    """
    print('Waiting ...')
    while True:
        result = compute.zoneOperations().get(
            project=project,
            zone=zone,
            operation=operation).execute()
        if result['status'] == 'DONE':
            print("The current operation is done.")
            if 'error' in result:
                raise ZoneOperationsError(result['error'])
            return result
        time.sleep(1)


def wait_for_region_operation(compute, project, region, operation):
    """ Keep waiting for a region operation until it finishes

        Args:
            compute: google API compute engine service
            project: project ID
            region: zone of the VM
            operation: name of the Operations resource to return

        Returns:
            a deserialized object of the response

        Raises:
            RegionOperationsError: if the operation has an error
            googleapiclient.errors.HttpError: invalid request
    """
    print('Waiting ...')
    while True:
        result = compute.regionOperations().get(
            project=project,
            region=region,
            operation=operation).execute()
        if result['status'] == 'DONE':
            print("The current operation is done.")
            if 'error' in result:
                print('Region operations error', result['error'])
                raise RegionOperationsError(result['error'])
            return result
        time.sleep(1)


def get_zone(compute, project, zone) -> dict:
    """ Get zone information

        Args:
            compute: google API compute engine service
            project: project ID
            zone: zone of the VM

        Returns:
            deserialized zone information

        Raises:
            googleapiclient.errors.HttpError: invalid request
    """
    return compute.zones().get(
        project=project,
        zone=zone).execute()


def check_network_auto_mode(compute, project, network) -> bool:
    """ Check if the network is in auto mode

    Args:
        compute: google API compute engine service
        project: project ID
        network: name of the network

    Returns:
        true or false

    Raises:
        InvalidTargetNetworkError: if the network is not a subnetwork mode network
        googleapiclient.errors.HttpError: invalid request
    """
    network_info = get_network(compute, project, network)
    if 'autoCreateSubnetworks' not in network_info:
        raise InvalidTargetNetworkError(
            'The target network is not a subnetwork mode network')
    auto_mode_status = network_info['autoCreateSubnetworks']
    return auto_mode_status


def preserve_external_ip_address(compute, project, region, address_body):
    """ Preserve the external IP address.

    Args:
        compute: google API compute engine service
        project: project ID
        region: project region
        address_body: internal IP address information, such as
           {
              name: "ADDRESS_NAME",
              address: "IP_ADDRESS"
            }
    Returns: a deserialized object of the response

    Raises:
        googleapiclient.errors.HttpError: If the IP
        address is already a static one, or if the IP is not being
        used by any instance, or invalid request, it will raise an Http error
    """
    return compute.addresses().insert(project=project, region=region,
                                      body=address_body).execute()


def release_static_ip_address(compute, project, region, address_name):
    """ Release a static external or internal IP address.

     Args:
         compute: google API compute engine service
         project: project ID
         region: project region
         address_name: name of the address resource to delete
     Returns: a deserialized object of the response

     Raises:
         googleapiclient.errors.HttpError: invalid request
     """
    return compute.addresses().delete(project=project, region=region,
                                      address=address_name).execute()


def rollback_failure_protection(compute, project, zone, instance,
                                original_instance_template, all_disks_info=[],
                                instance_deleted=False)->bool:
    """Try to rollback to the original VM. If the rollback procedure also fails,
    then print out the original VM's instance template in the console

        Args:
            compute: google API compute engine service
            project: project ID
            zone: zone of the VM
            instance: name of the VM
            all_disks_info: a list of disks' info. Default value is [].
            instance_deleted: whether the original VM has been deleted

        Returns: True/False for successful/failed rollback

    """
    try:
        rollback_original_instance(compute, project, zone, instance,
                                   original_instance_template,
                                   all_disks_info, instance_deleted)
    except Exception as e:
        warnings.warn("Rollback failed.", Warning)
        print(e)
        print(
            "The original VM may have been deleted. "
            "The instance template of the original VM is: ")
        print(original_instance_template)
        return False

    print('Rollback finished. The original VM is running.')
    return True


def rollback_original_instance(compute, project, zone, instance,
                               original_instance_template,
                               all_disks_info, instance_deleted):
    """ Roll back to the original VM. Reattach the disks to the
    original VM and restart it.

        Args:
            compute: google API compute engine service
            project: project ID
            zone: zone of the VM
            instance: name of the VM
            all_disks_info: a list of disks' info. Default value is [].
            instance_deleted: whether the original VM has been deleted

        Raises:
            googleapiclient.errors.HttpError: invalid request
    """
    warnings.warn(
        'VM network migration is failed. Rolling back to the original VM.',
        Warning)

    print(original_instance_template)

    if not instance_deleted:
        for disk_info in all_disks_info:
            print('attach_disk_operation is running')
            attach_disk_operation = attach_disk(compute, project, zone,
                                                instance, disk_info)
            wait_for_zone_operation(compute, project, zone,
                                    attach_disk_operation['name'])
        print('Restarting the original VM')
        print('start_instance_operation is running')
        start_instance_operation = start_instance(compute, project, zone,
                                                  instance)
        wait_for_zone_operation(compute, project, zone,
                                start_instance_operation['name'])
    else:
        recreate_original_instance_operation = create_instance(compute, project,
                                                               zone,
                                                               original_instance_template)
        wait_for_zone_operation(compute, project, zone,
                                recreate_original_instance_operation['name'])



def preserve_ip_addresses_handler(compute, project, new_instance_name,
                                  new_network_info, original_network_interface,
                                  region,
                                  preserve_external_ip) -> dict:
    """Preserve the external IP address.

    Args:
        compute: google API compute engine service
        project: project ID
        new_instance_name: name of the new VM
        new_network_info: selfLinks of current network and subnet
        original_network_interface: network interface of the original VM
        region: region of original VM
        preserve_external_ip: preserve the external ip or not

    Returns:
        network interface of the new VM
    """
    new_network_interface = copy.deepcopy(original_network_interface)
    new_network_interface['network'] = new_network_info['network']
    new_network_interface['subnetwork'] = new_network_info['subnetwork']
    if preserve_external_ip:
        print('Preserving the external IP address')
        # There is no external ip assigned to the original VM
        # An ephemeral external ip will be assigned to the new VM
        if 'accessConfigs' not in new_network_interface or 'natIP' not in \
                new_network_interface['accessConfigs'][0]:
            warnings.warn(
                'The current VM has no external IP address. \
                An ephemeral external IP address will be assigned to the new VM',
                Warning)
            pass
        else:
            external_ip_address = new_network_interface['accessConfigs'][0][
                'natIP']
            external_ip_address_body = generate_external_ip_address_body(
                external_ip_address, new_instance_name)
            try:
                preserve_external_ip_operation = preserve_external_ip_address(
                    compute, project, region,
                    external_ip_address_body)
                wait_for_region_operation(compute, project, region,
                                          preserve_external_ip_operation[
                                              'name'])
            except HttpError as e:
                error_reason = e._get_reason()
                # The external IP is already preserved as a static IP,
                # or the current name of the external IP already exists
                if 'already' in error_reason:
                    warnings.warn(error_reason, Warning)
                else:
                    warnings.warn(
                        'Failed to preserve the external IP address as a static IP.',
                        Warning)
                    print(e._get_reason())
                    print('An ephemeral external IP address will be assigned.')
                    del new_network_interface['accessConfigs']
            else:
                print(
                    'The external IP address is reserved as a static IP address.')

    elif 'accessConfigs' in new_network_interface:
        del new_network_interface['accessConfigs']
    # Use an ephemeral internal IP for the new VM
    del new_network_interface['networkIP']

    return new_network_interface


def generate_external_ip_address_body(external_ip_address, new_instance_name):
    """Generate external IP address.

    Args:
        external_ip_address: IPV4 format address
        new_instance_name: name of the new VM

    Returns:
          {
          name: "ADDRESS_NAME",
          address: "IP_ADDRESS"
        }
    """
    external_ip_address_body = {}
    external_ip_address_body[
        'name'] = new_instance_name + '-' + generate_timestamp_string()
    external_ip_address_body['address'] = external_ip_address
    return external_ip_address_body


def generate_timestamp_string() -> str:
    """Generate the current timestamp.

    Returns: current timestamp string

    """
    return str(time.strftime("%s", time.gmtime()))


def main(project, zone, original_instance, new_instance, network, subnetwork,
         preserve_external_ip=False):
    """ Execute the migration process.

        Args:
            project: project ID
            zone: zone of the VM
            original_instance: name of the original VM
            new_instance: name of the new VM
            network: name of the target network
            subnetwork: name of the target subnet
            preserve_external_ip: preserve the current external IP or not

        Raises:
            UnchangedInstanceNameError: if the network mode is not auto and
             the subnetwork is not specified
            MissingSubnetworkError: if new_instance == orignal_instance
            googleapiclient.errors.HttpError: invalid request
    """

    credentials, default_project = google.auth.default()
    compute = discovery.build('compute', 'v1', credentials=credentials)
    if preserve_external_ip:
        warnings.warn(
            'You choose to preserve the external IP. If the original instance '
            'has an ephemeral IP, it will be reserved as a static IP after the '
            'execution,',
            Warning)
        continue_execution = input(
            'Do you still want to preserve the external IP? y/n')
        if continue_execution == 'n':
            preserve_external_ip = False

    if new_instance == original_instance:
        raise UnchangedInstanceNameError(
            'The new VM should not have the same name as the original VM')

    # If the network is auto, then the subnetwork name is optional.
    # Otherwise it should be specified
    automode_status = check_network_auto_mode(compute, project, network)
    if subnetwork is None:
        if not automode_status:
            raise MissingSubnetworkError('No specified subnetwork')
        else:
            # the network is in auto mode, the default subnetwork name is the
            # same as the network name
            subnetwork = network

    instance_template = retrieve_instance_template(compute, project, zone,
                                                   original_instance)
    try:
        all_disks_info = get_disks_info_from_instance_template(
            instance_template)


        original_instance_template = copy.deepcopy(instance_template)
        region = get_zone(compute, project, zone)['region']
        region_name = region.split('regions/')[1]

        new_network_info = generate_new_network_info(compute, project, region,
                                                     network, subnetwork)
        original_network_interface = instance_template['networkInterfaces'][0]
        new_network_interface = preserve_ip_addresses_handler(compute, project,
                                                              new_instance,
                                                              new_network_info,
                                                              original_network_interface,
                                                              region_name,
                                                              preserve_external_ip)

        print('Modifying instance template')
        new_instance_template = modify_instance_template_with_new_network(
            instance_template, new_instance, new_network_interface)
    except Exception as e:
        print(e)
        print('An error happens. '
              'Migration is terminated. '
              'The original VM is running.')
        return

    try:
        print('Stopping the VM')
        print('stop_instance_operation is running')
        stop_instance_operation = stop_instance(compute, project, zone,
                                                original_instance)
        wait_for_zone_operation(compute, project, zone,
                                stop_instance_operation['name'])
    except:
        rollback_failure_protection(compute, project, zone, original_instance,
                                    original_instance_template, [], False)
        return


    try:
        print('Detaching the disks')
        for disk_info in all_disks_info:
            disk = disk_info['deviceName']
            print('detach_disk_operation is running')
            detach_disk_operation = detach_disk(compute, project, zone,
                                                original_instance, disk)
            wait_for_zone_operation(compute, project, zone,
                                    detach_disk_operation['name'])

        print('Deleting the old VM')
        print('delete_instance_operation is running')
        delete_instance_operation = delete_instance(compute, project, zone,
                                                    original_instance)
        wait_for_zone_operation(compute, project, zone,
                                delete_instance_operation['name'])
    except:

        rollback_failure_protection(compute, project, zone, original_instance,
                                    original_instance_template,
                                    all_disks_info, False)
        return

    try:
        print('Creating a new VM')
        print('create_instance_operation is running')
        create_instance_operation = create_instance(compute, project, zone,
                                                    new_instance_template)
        wait_for_zone_operation(compute, project, zone,
                                create_instance_operation['name'])
    except:
        rollback_failure_protection(compute, project, zone, original_instance,
                                    original_instance_template, all_disks_info,
                                    True)
        return
    print('Success')
