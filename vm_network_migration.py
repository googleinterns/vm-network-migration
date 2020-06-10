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
     python3 vm_network_migration.py --project_id=dakeying-devconsole
     --zone=us-central1-a --original_instance_name=instance-legacy
     --new_instance_name=vm-new --network=test-network --subnetwork=test-network

"""
import argparse
import time

from googleapiclient import discovery
from googleapiclient import http
import google.auth


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
        KeyError: No disks on the VM
    """
    if 'disks' not in instance_template:
        raise KeyError('No disks are attached on the VM')
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
        raise KeyError('networkInterfaces is not in instance_template')
    elif not isinstance(instance_template['networkInterfaces'], list):
        raise TypeError('Invalid value type')
    if 'name' not in instance_template:
        raise KeyError('name is not in instance_template')
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


def wait_for_operation(compute, project, zone, operation):
    """ Create the instance using instance template

        Args:
            compute: google API compute engine service
            project: project ID
            zone: zone of the VM
            operation: name of the Operations resource to return

        Returns:
            a deserialized object of the response

        Raises:
            Exception: if the operation has an error
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
                raise Exception(result['error'])
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
            IOError: if the network is not a subnetwork mode network
            googleapiclient.errors.HttpError: invalid request
    """
    request = compute.networks().get(project=project, network=network)
    response = request.execute()
    if 'autoCreateSubnetworks' not in response:
        raise IOError('The target network is not a subnetwork mode network')
    auto_mode_status = response['autoCreateSubnetworks']
    return auto_mode_status


def roll_back_original_instance(compute, project, zone, instance,
                                all_disks_info):
    """ Roll back to the original VM. Reattach the disks to the
    original VM and restart it.

        Args:
            compute: google API compute engine service
            project: project ID
            zone: zone of the VM
            instance: name of the VM
            all_disks_info: a list of disks' info

        Raises:
            googleapiclient.errors.HttpError: invalid request
    """
    print('VM network migration is failed. '
          'Rolling back to the original VM')
    print('Attacking disks back to the original VM')
    for disk_info in all_disks_info:
        print('attach_instance_operation is running')
        attach_disk_operation = attach_disk(compute, project, zone,
                                            instance, disk_info)
        wait_for_operation(compute, project, zone,
                       attach_disk_operation['name'])
    print('Restarting the original VM')
    print('start_instance_operation is running')
    start_instance_operation = start_instance(compute, project, zone, instance)
    wait_for_operation(compute, project, zone,
                       start_instance_operation['name'])
    print('The migration process is failed. The original VM is running.')


def main(project, zone, original_instance, new_instance, network, subnetwork):
    """ Execute the migration process.

        Args:
            project: project ID
            zone: zone of the VM
            original_instance: name of the original VM

        Returns:
            true or false

        Raises:
            IOError: if the network mode is not auto and
             the subnetwork is not specified
            IOError: if new_instance == orignal_instance
            googleapiclient.errors.HttpError: invalid request
    """
    credentials, default_project = google.auth.default()
    compute = discovery.build('compute', 'v1', credentials=credentials)

    if new_instance == original_instance:
        raise IOError('The new VM should not have the same name as '
                      'the original VM')

    # If the network is auto, then the subnetwork name is optional.
    # Otherwise it should be specified
    automode_status = check_network_auto_mode(compute, project, network)
    if subnetwork is None:
        if not automode_status:
            raise IOError('No specified subnetwork')
        else:
            # the network is in auto mode, the default subnetwork name is the
            # same as the network name
            subnetwork = network

    print('Stopping the VM instance')
    print('stop_instance_operation is running')
    stop_instance_operation = stop_instance(compute, project, zone,
                                            original_instance)
    wait_for_operation(compute, project, zone, stop_instance_operation['name'])

    instance_template = retrieve_instance_template(compute, project, zone,
                                                   original_instance)

    all_disks_info = get_disks_info_from_instance_template(instance_template)
    print('Detaching the disks')
    for disk_info in all_disks_info:
        disk = disk_info['deviceName']
        print('detach_disk_operation is running')
        detach_disk_operation = detach_disk(compute, project, zone,
                                            original_instance, disk)
        wait_for_operation(compute, project, zone,
                           detach_disk_operation['name'])

    region = get_zone(compute, project, zone)['region']
    try:
        new_network_info = generate_new_network_info(compute, project, region,
                                                     network, subnetwork)
    except http.HttpError as err:
        print('An HttpError occurs: ', err)
        roll_back_original_instance(compute, project, zone, original_instance, all_disks_info)
        return

    print('Modifying instance template')
    new_instance_template = modify_instance_template_with_new_network(
        instance_template, new_instance, new_network_info)

    print('Creating a new VM instance')
    print('create_instance_operation is running')
    try:
        create_instance_operation = create_instance(compute, project, zone,
                                                    new_instance_template)
    except http.HttpError as err:
        print('An HttpError occurs: ', err)
        roll_back_original_instance(compute, project, zone, original_instance, all_disks_info)
        return
    wait_for_operation(compute, project, zone,
                       create_instance_operation['name'])

    print('Deleting the old VM instance')
    print('delete_instance_operation is running')
    delete_instance_operation = delete_instance(compute, project, zone,
                                                original_instance)
    wait_for_operation(compute, project, zone,
                       delete_instance_operation['name'])

    print('Success')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--project_id',
                        help='The project ID of the original VM.')
    parser.add_argument('--zone', help='The zone name of the original VM.')
    parser.add_argument('--original_instance_name',
                        help='The name of the original VM')
    parser.add_argument('--new_instance_name',
                        help='The name of the new VM. It should be'
                             ' different from the original VM')
    parser.add_argument('--network', help='The name of the new network')
    parser.add_argument(
        '--subnetwork',
        default=None,
        help='The name of the subnetwork. For auto mode networks,'
             ' this field is optional')
    args = parser.parse_args()
    main(args.project_id, args.zone, args.original_instance_name,
         args.new_instance_name, args.network, args.subnetwork)
