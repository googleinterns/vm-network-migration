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

"""
import warnings

import google.auth
from googleapiclient import discovery
from vm_network_migration.module_helpers.address_helper import AddressHelper
from vm_network_migration.errors import *
from vm_network_migration.modules.instance import (
    Instance,
    InstanceStatus,
)
from vm_network_migration.module_helpers.subnet_network_helper import SubnetNetworkHelper


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
        self.instance = None

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


    def network_migration(self, original_instance_name,
                          network_name,
                          subnetwork_name, preserve_external_ip):
        """ The main method of the instance network migration process

        Args:
            original_instance_name: original instance's name
            network_name: target network name
            subnetwork_name: target subnetwork name
            preserve_external_ip: True/False

        Returns: None

        """

        try:
            print('Retrieving the original instance configs.')
            if self.instance == None:
                self.instance = Instance(self.compute, self.project,
                                                  original_instance_name,
                                                  self.region,
                                                  self.zone, None)
            address_factory = AddressHelper(self.compute, self.project, self.region)
            self.instance.address = address_factory.generate_address(
                self.instance.original_instance_configs)

            print('Modifying IP address.')
            self.instance.address.preserve_ip_addresses_handler(
                preserve_external_ip)
            subnetwork_factory = SubnetNetworkHelper(self.compute, self.project, self.zone, self.region)
            self.instance.network = subnetwork_factory.generate_network(network_name,
                                                              subnetwork_name)
            self.instance.update_instance_configs()

            print('Stopping the VM.')
            print('stop_instance_operation is running.')
            self.instance.stop_instance()

            print('Detaching the disks.')
            self.instance.detach_disks()

            print('Deleting the old VM.')
            print('delete_instance_operation is running.')
            self.instance.delete_instance()

            print('Creating a new VM.')
            print('create_instance_operation is running.')
            print('DEBUGGING:', self.instance.new_instance_configs)
            self.instance.create_instance(self.instance.new_instance_configs)
            self.instance.migrated = True
            if self.instance.original_status == InstanceStatus.TERMINATED:
                print('Since the original instance was terminated, '
                      'the new instance is terminating.')
                self.instance.stop_instance()
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
        if self.instance == None or self.instance.original_instance_configs == None:
            print(
                'Cannot get instance\'s resource. Please check the parameters and try again.')
            return
        instance_status = self.instance.get_instance_status()

        if instance_status == InstanceStatus.RUNNING:
            return
        elif instance_status == InstanceStatus.NOTEXISTS:
            print('Recreating the original VM.')
            self.instance.create_instance(self.instance.original_instance_configs)
        else:
            print('Attaching disks back to the original VM.')
            print('attach_disk_operation is running')
            self.instance.attach_disks()
            print('Restarting the original VM')
            print('start_instance_operation is running')
            self.instance.start_instance()

    def rollback_failure_protection(self) -> bool:
        """Try to rollback to the original VM. If the rollback procedure also fails,
        then print out the original VM's instance configs in the console

            Returns: True/False for successful/failed rollback
            Raises: RollbackError
        """
        try:
            self.rollback_original_instance()
        except Exception as e:
            warnings.warn('Rollback failed.', Warning)
            print(e)
            print(
                'The original VM may have been deleted. '
                'The instance configs of the original VM is: ')
            print(self.instance.original_instance_configs)
            raise RollbackError('Rollback to the original VM is failed.')

        print('Rollback finished. The original VM is running.')
        return True
