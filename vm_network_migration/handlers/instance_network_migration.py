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
from googleapiclient.http import HttpError

class InstanceNetworkMigration:
    def __init__(self, project, zone,  original_instance_name,
                          network_name,
                          subnetwork_name, preserve_external_ip):
        """ Initialize a InstanceNetworkMigration object

        Args:
            project: project ID
            zone: zone of the instance
        """
        self.compute = self.set_compute_engine()
        self.project = project
        self.zone = zone
        self.region = self.get_region()
        self.original_instance_name = original_instance_name
        self.network_name = network_name
        self.subnetwork_name = subnetwork_name
        self.preserve_external_ip = preserve_external_ip
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

    def get_instance_selfLink(self):
        """  Get the selfLink of the instance

        Returns: URL string

        """
        if self.instance != None:
            return self.instance.selfLink

    def network_migration(self):
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
                                                  self.original_instance_name,
                                                  self.region,
                                                  self.zone, None)
            address_factory = AddressHelper(self.compute, self.project, self.region)
            self.instance.address = address_factory.generate_address(
                self.instance.original_instance_configs)

            print('Modifying IP address.')
            self.instance.address.preserve_ip_addresses_handler(
                self.preserve_external_ip)
            subnetwork_factory = SubnetNetworkHelper(self.compute, self.project, self.zone, self.region)
            self.instance.network = subnetwork_factory.generate_network(self.network_name,
                                                              self.subnetwork_name)
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
            if self.instance.original_status == InstanceStatus.TERMINATED:
                print('Since the original instance was terminated, '
                      'the new instance is terminating.')
                self.instance.stop_instance()
            print('The migration is successful.')

        except Exception as e:
            warnings.warn(str(e), Warning)
            #self.rollback_failure_protection()
            self.rollback()
            raise MigrationFailed('Rollback to the original instance.')


    def rollback(self, force=False):
        """ Rollback to the original VM. Reattach the disks to the
        original instance and restart it.

        Args:
            force: force to rollback
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
            if self.instance.migrated and force:
                # The migration has been finished, but force to rollback
                print('Stopping the instance.')
                self.instance.stop_instance()
                print('Detaching the disks.')
                self.instance.detach_disks()
                print('Deleting the instance in the target network.')
                self.instance.delete_instance()
            else:
                return

        instance_status = self.instance.get_instance_status()
        if instance_status == InstanceStatus.NOTEXISTS:
            try:
                print(
                    'Recreating the original instance in the legacy network.')
                self.instance.create_instance(
                    self.instance.original_instance_configs)
            except HttpError as e:
                error_reason = e._get_reason()
                print(error_reason)
                if 'not found in region' in error_reason:
                    # The original external IP can not be preserved.
                    # A new external IP will be picked.
                    self.instance.create_instance_with_ephemeral_external_ip(
                        self.instance.original_instance_configs)
                else:
                    raise e

        else:
            print('Attaching disks back to the original VM.')
            print('attach_disk_operation is running')
            self.instance.attach_disks()
            print('Restarting the original VM')
            print('start_instance_operation is running')
            self.instance.start_instance()

    # def rollback_failure_protection(self) -> bool:
    #     """Try to rollback to the original VM. If the rollback procedure also fails,
    #     then print out the original VM's instance configs in the console
    #
    #         Returns: True/False for successful/failed rollback
    #         Raises: RollbackError
    #     """
    #     try:
    #         self.rollback_original_instance()
    #     except Exception as e:
    #         warnings.warn('Rollback failed.', Warning)
    #         print(e)
    #         print(
    #             'The original VM may have been deleted. '
    #             'The instance configs of the original VM is: ')
    #         print(self.instance.original_instance_configs)
    #         raise RollbackError('Rollback to the original VM is failed.')
    #
    #     print('Rollback finished. The original VM is running.')
    #     return True
