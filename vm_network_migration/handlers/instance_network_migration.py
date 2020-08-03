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

from googleapiclient.http import HttpError
from vm_network_migration.errors import *
from vm_network_migration.modules.instance_modules.instance import (
    Instance,
    InstanceStatus,
)
from vm_network_migration.utils import initializer
from vm_network_migration.handlers.compute_engine_resource_migration import ComputeEngineResourceMigration


class InstanceNetworkMigration(ComputeEngineResourceMigration):
    @initializer
    def __init__(self, compute, project, zone, original_instance_name,
                 network_name,
                 subnetwork_name, preserve_external_ip):
        """ Initialize a InstanceNetworkMigration object

        Args:
            project: project ID
            zone: zone of the instance
        """
        super(InstanceNetworkMigration, self).__init__()
        self.region = self.get_region()
        self.instance = Instance(self.compute, self.project,
                                 self.original_instance_name,
                                 self.region,
                                 self.zone, self.network_name,
                                 self.subnetwork_name,
                                 preserve_instance_ip=self.preserve_external_ip)

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
        referrer_links = self.instance.get_referrer_selfLinks()
        if len(referrer_links) > 0:
            raise AmbiguousTargetResource(
                'The instance %s is a member of %s, please detach the instance from its referrer and try again. '
                'Or you can try to migrate its referrer directly.' % (
                    self.original_instance_name, ','.join(referrer_links)))

        try:
            print('Checking the external IP address of the VM %s.' % (
                self.original_instance_name))
            self.instance.address_object.preserve_ip_addresses_handler(
                self.preserve_external_ip)

            print('Stopping the VM %s.' % (self.original_instance_name))
            print('stop_instance_operation is running.')
            self.instance.stop_instance()

            print('Detaching the disks.')
            self.instance.detach_disks()

            print('Deleting the old VM %s.' % (self.original_instance_name))
            print('delete_instance_operation is running.')
            self.instance.delete_instance()

            print('Creating a new VM %s.' % (self.original_instance_name))
            print('create_instance_operation is running.')
            print('Modified instance configuration:',
                  self.instance.new_instance_configs)
            self.instance.create_instance(self.instance.new_instance_configs)
            print('The migration is successful.')

        except Exception as e:
            warnings.warn(str(e), Warning)
            self.rollback()
            raise MigrationFailed('Rollback to the original instance %s.' % (
                self.original_instance_name))
        # If the original status is terminated, the tool will try to terminate
        # the migrated instance
        if self.instance.original_status == InstanceStatus.TERMINATED:
            print('Since the original instance %s was terminated, '
                  'the new instance is going to be terminated.' % (
                      self.original_instance_name))
            try:
                self.instance.stop_instance()
            except:
                print('Unable to terminate the new instance, but the migration'
                      'has been finished.')

    def rollback(self):
        """ Rollback to the original VM. Reattach the disks to the
        original instance and restart it.
        """
        warnings.warn(
            'VM network migration was failed. Rolling back to the original VM %s.' % (
                self.original_instance_name),
            Warning)
        if self.instance == None or self.instance.original_instance_configs == None:
            print(
                'Cannot get the instance\'s resource. Please check the parameters and try again.')
            return
        instance_status = self.instance.get_instance_status()

        if instance_status == InstanceStatus.RUNNING:
            if self.instance.migrated:
                # The migration has been finished, but force to rollback
                print(
                    'Stopping the instance %s.' % (self.original_instance_name))
                self.instance.stop_instance()
                print('Detaching the disks.')
                self.instance.detach_disks()
                print('Deleting the instance %s in the target network.' % (
                    self.original_instance_name))
                self.instance.delete_instance()
            else:
                return

        instance_status = self.instance.get_instance_status()
        if instance_status == InstanceStatus.NOTEXISTS:
            try:
                print(
                    'Recreating the original instance %s in the legacy network.' % (
                        self.original_instance_name))
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
            print('Attaching disks back to the original VM %s.' % (
                self.original_instance_name))
            print('attach_disk_operation is running')
            self.instance.attach_disks()
            print(
                'Restarting the original VM %s' % (self.original_instance_name))
            print('start_instance_operation is running')
            self.instance.start_instance()
        self.instance.migrated = False

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
