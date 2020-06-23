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
from enum import Enum

import google.auth
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from vm_network_migration.errors import *
from vm_network_migration.operations import Operations
class InstanceStatus(Enum):
    NOTEXISTS = None
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    TERMINATED = "TERMINATED"
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
    instance_template['networkInterfaces'][0]['network'] = new_network_info['network']
    instance_template['networkInterfaces'][0]['subnetwork'] = new_network_info[
        'subnetwork']

    return instance_template

def modify_instance_template_with_new_name(instance_template, new_instance):
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
                                original_instance_template,
                                all_disks_info=[]) ->bool:
    """Try to rollback to the original VM. If the rollback procedure also fails,
    then print out the original VM's instance template in the console

        Args:
            compute: google API compute engine service
            project: project ID
            zone: zone of the VM
            instance: name of the VM
            all_disks_info: a list of disks' info. Default value is [].

        Returns: True/False for successful/failed rollback

    """
    try:
        rollback_original_instance(compute, project, zone, instance,
                                   original_instance_template, all_disks_info)
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
                               original_instance_template, all_disks_info):
    operations = Operations(compute, project, zone, "")
    """ Roll back to the original VM. Reattach the disks to the
    original VM and restart it.

        Args:
            compute: google API compute engine service
            project: project ID
            zone: zone of the VM
            instance: name of the VM
            all_disks_info: a list of disks' info. Default value is [].

        Raises:
            googleapiclient.errors.HttpError: invalid request
    """

    warnings.warn(
        'VM network migration is failed. Rolling back to the original VM.',
        Warning)
    instance_status = get_instance_status(compute, project, zone, instance)
    if instance_status == InstanceStatus.RUNNING:
        pass
    elif instance_status == InstanceStatus.NOTEXISTS:
        recreate_original_instance_operation = create_instance(compute, project,
                                                               zone,
                                                               original_instance_template)
        operations.wait_for_zone_operation(recreate_original_instance_operation['name'])
    else:
        for disk_info in all_disks_info:
            print('attach_disk_operation is running')
            attach_disk_operation = attach_disk(compute, project, zone,
                                                instance, disk_info)
            operations.wait_for_zone_operation(attach_disk_operation['name'])
        print('Restarting the original VM')
        print('start_instance_operation is running')
        start_instance_operation = start_instance(compute, project, zone,
                                                  instance)
        operations.wait_for_zone_operation(start_instance_operation['name'])




def preserve_ip_addresses_handler(compute, project, new_instance_name,
                                  new_network_info, original_network_interface,
                                  region,
                                  preserve_external_ip) -> dict:
    operations = Operations(compute, project, "", region)
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
                operations.wait_for_region_operation(preserve_external_ip_operation[
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


def preserve_ip_addresses_handler2(compute, project, new_instance_name,
                                  external_ip,
                                  region,
                                  preserve_external_ip) -> dict:
    operations = Operations(compute, project, "", region)
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


    if preserve_external_ip:
        print('Preserving the external IP address')
        # There is no external ip assigned to the original VM
        # An ephemeral external ip will be assigned to the new VM

        external_ip_address_body = generate_external_ip_address_body(
            external_ip, new_instance_name)
        try:
            preserve_external_ip_operation = preserve_external_ip_address(
                compute, project, region,
                external_ip_address_body)
            operations.wait_for_region_operation(preserve_external_ip_operation[
                                          'name'])
        except HttpError as e:
            error_reason = e._get_reason()
            # The external IP is already preserved as a static IP,
            # or the current name of the external IP already exists
            if 'already' in error_reason:
                warnings.warn(error_reason, Warning)
                return external_ip
            else:
                warnings.warn(
                    'Failed to preserve the external IP address as a static IP.',
                    Warning)
                print(e._get_reason())
                print('An ephemeral external IP address will be assigned.')
                return None
        else:
            print(
                'The external IP address is reserved as a static IP address.')
            return external_ip


    return None

def get_instance_status(compute, project, zone, instance):
    try:
        instance_template = retrieve_instance_template(compute, project, zone,
                                   instance)
    except HttpError as e:
        error_reason = e._get_reason()
        print(error_reason)
        if "not found" in error_reason:
            return InstanceStatus.NOTEXISTS
        else:
            raise e
    return InstanceStatus(instance_template['status'])

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

def modify_instance_template_with_external_ip(instance_template, external_ip) -> dict:
    #no unittest
    if external_ip == None:
        if 'accessConfigs' in instance_template['networkInterfaces'][0]:
            del instance_template['networkInterfaces'][0]['accessConfigs']
    else:
        instance_template['networkInterfaces'][0]['accessConfigs'][0][
            'natIP'] = external_ip
    return instance_template

def get_external_ip(instance_template)->str:
    #no unittest
    try:
        return instance_template['networkInterfaces'][0]['accessConfigs'][0]['natIP']
    except:
        return None

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


    original_instance_template = {}
    all_disks_info = []
    try:
        instance_template = retrieve_instance_template(compute, project, zone,
                                                       original_instance)
        original_instance_template = copy.deepcopy(instance_template)
        all_disks_info = get_disks_info_from_instance_template(
            instance_template)

        region = get_zone(compute, project, zone)['region']

        new_network_info = generate_new_network_info(compute, project, region,
                                                     network, subnetwork)
        # new_network_interface = preserve_ip_addresses_handler(compute, project,
        #                                                       new_instance,
        #                                                       new_network_info,
        #                                                       original_network_interface,
        #                                                       region_name,
        #                                                       preserve_external_ip)
        external_ip = get_external_ip(instance_template)

        new_address = preserve_ip_addresses_handler2(compute, project, new_instance, external_ip, region, preserve_external_ip)

        modify_instance_template_with_external_ip(instance_template, new_address)

        print('Modifying instance template')
        new_instance_template = modify_instance_template_with_new_network(
            instance_template, new_instance, new_network_info)
        modify_instance_template_with_new_name(instance_template, new_instance)
        operations = Operations(compute, project, zone, region)
        print('Stopping the VM')
        print('stop_instance_operation is running')
        stop_instance_operation = stop_instance(compute, project, zone,
                                                original_instance)
        operations.wait_for_zone_operation(stop_instance_operation['name'])

        print('Detaching the disks')
        for disk_info in all_disks_info:
            disk = disk_info['deviceName']
            print('detach_disk_operation is running')
            detach_disk_operation = detach_disk(compute, project, zone,
                                                original_instance, disk)
            operations.wait_for_zone_operation(detach_disk_operation['name'])

        print('Deleting the old VM')
        print('delete_instance_operation is running')
        delete_instance_operation = delete_instance(compute, project, zone,
                                                    original_instance)
        operations.wait_for_zone_operation(delete_instance_operation['name'])
        print('Creating a new VM')
        print('create_instance_operation is running')
        create_instance_operation = create_instance(compute, project, zone,
                                                    new_instance_template)
        operations.wait_for_zone_operation(create_instance_operation['name'])
    except:
        rollback_failure_protection(compute, project, zone, original_instance,
                                    original_instance_template, all_disks_info)
        return
    print('The migration is successful.')
