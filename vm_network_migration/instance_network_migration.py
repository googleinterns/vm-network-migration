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
import warnings

import google.auth
from googleapiclient import discovery
from vm_network_migration.address import Address
from vm_network_migration.errors import *
from vm_network_migration.instance import (
    Instance,
    InstanceStatus,
)
from vm_network_migration.subnet_network import SubnetNetwork


class InstanceNetworkMigration:
    def __init__(self, project, zone):
        """ Initialize a InstanceNetworkMigration object

        Args:
            project: project ID
            zone: zone of the instance
        """
        self.compute = self.set_compute_engine()
        self.project = project
        self.zone = zone
        self.region = self.get_region()
        self.original_instance = None
        self.new_instance = None

    def set_compute_engine(self):
        """ Credential setup

        Returns:google compute engine

        """
        credentials, default_project = google.auth.default()
        return discovery.build('compute', 'v1', credentials=credentials)

    def get_region(self) -> dict:
        """ Get region information

            Returns:
                region name of the self.zone

            Raises:
                googleapiclient.errors.HttpError: invalid request
        """
        return self.compute.zones().get(
            project=self.project,
            zone=self.zone).execute()['region'].split('regions/')[1]

    def generate_address(self, instance_template):
        """ Generate an address object

        Args:
            instance_template: the instance template which contains the IP address information

        Returns: an Address object

        """
        address = Address(self.compute, self.project, self.region)
        address.retrieve_ip_from_network_interface(
            instance_template['networkInterfaces'][0])
        return address

    def generate_network(self, network, subnetwork):
        """ Generate a network object

        Args:
            network: network name
            subnetwork: subnetwork name

        Returns: a SubnetNetwork object

        """
        network = SubnetNetwork(self.compute, self.project, self.zone,
                                self.region, network, subnetwork)
        network.check_subnetwork_validation()
        network.generate_new_network_info()

        return network

    def network_migration(self, original_instance_name, new_instance_name,
                          network_name,
                          subnetwork_name, preserve_external_ip):
        """ The main method of the instance network migration process

        Args:
            original_instance_name: original instance's name
            new_instance_name: new instance's name
            network_name: target network name
            subnetwork_name: target subnetwork name
            preserve_external_ip: True/False

        Returns: None

        """
        if preserve_external_ip:
            warnings.warn(
                'You choose to preserve the external IP. If the original instance '
                'has an ephemeral IP, it will be reserved as a static external IP after the '
                'execution.',
                Warning)
            continue_execution = input(
                'Do you still want to preserve the external IP? y/n: ')
            if continue_execution == 'n':
                preserve_external_ip = False
        try:
            if new_instance_name == original_instance_name:
                raise UnchangedInstanceNameError(
                    'The new VM should not have the same name as the original VM. The migration process didn\'t start')
            print('Retrieving the original instance template.')
            self.original_instance = Instance(self.compute, self.project,
                                              original_instance_name,
                                              self.region,
                                              self.zone, None)

            self.new_instance = Instance(self.compute, self.project,
                                         new_instance_name,
                                         self.region, self.zone, copy.deepcopy(
                    self.original_instance.instance_template))
            self.new_instance.address = self.generate_address(
                self.new_instance.instance_template)

            print('Modifying IP address.')
            self.new_instance.address.preserve_ip_addresses_handler(
                preserve_external_ip)
            self.new_instance.network = self.generate_network(network_name,
                                                              subnetwork_name)
            self.new_instance.update_instance_template()

            print('Stopping the VM.')
            print('stop_instance_operation is running.')
            self.original_instance.stop_instance()

            print('Detaching the disks.')
            self.original_instance.detach_disks()

            print('Deleting the old VM.')
            print('delete_instance_operation is running.')
            self.original_instance.delete_instance()

            print('Creating a new VM.')
            print('create_instance_operation is running.')
            print('DEBUGGING:', self.new_instance.instance_template)
            self.new_instance.create_instance()

            print('The migration is successful.')

        except Exception as e:
            warnings.warn(str(e), Warning)
            self.rollback_failure_protection()
            return

    def rollback_original_instance(self):
        """ Roll back to the original VM. Reattach the disks to the
        original instance and restart it.

            Raises:
                googleapiclient.errors.HttpError: invalid request
        """

        warnings.warn(
            'VM network migration is failed. Rolling back to the original VM.',
            Warning)
        if self.original_instance == None or self.original_instance.instance_template == None:
            print(
                'Cannot get instance\'s resource. Please check the parameters and try again.')
            return
        instance_status = self.original_instance.get_instance_status()

        if instance_status == InstanceStatus.RUNNING:
            return
        elif instance_status == InstanceStatus.NOTEXISTS:
            print('Recreating the original VM.')
            self.original_instance.create_instance()
        else:
            print('Attaching disks back to the original VM.')
            print('attach_disk_operation is running')
            self.original_instance.attach_disks()
            print('Restarting the original VM')
            print('start_instance_operation is running')
            self.original_instance.start_instance()

    def rollback_failure_protection(self) -> bool:
        """Try to rollback to the original VM. If the rollback procedure also fails,
        then print out the original VM's instance template in the console

            Returns: True/False for successful/failed rollback

        """
        try:
            self.rollback_original_instance()
        except Exception as e:
            warnings.warn("Rollback failed.", Warning)
            print(e)
            print(
                "The original VM may have been deleted. "
                "The instance template of the original VM is: ")
            print(self.original_instance.instance_template)
            return False

        print('Rollback finished. The original VM is running.')
        return True
