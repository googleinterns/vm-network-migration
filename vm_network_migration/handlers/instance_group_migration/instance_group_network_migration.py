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

""" This script is used to migrate an instance group from its legacy network to a
subnetwork mode network.
"""

import warnings
from warnings import warn

from vm_network_migration.errors import *
from vm_network_migration.handlers.compute_engine_resource_migration import ComputeEngineResourceMigration
from vm_network_migration.handlers.instance_group_migration.managed_instance_group_migration import ManagedInstanceGroupMigration
from vm_network_migration.handlers.instance_group_migration.unmanaged_instance_group_migration import UnmanagedInstanceGroupMigration
from vm_network_migration.module_helpers.instance_group_helper import InstanceGroupHelper
from vm_network_migration.modules.instance_group_modules.unmanaged_instance_group import UnmanagedInstanceGroup
from vm_network_migration.utils import initializer


class InstanceGroupNetworkMigration(ComputeEngineResourceMigration):
    @initializer
    def __init__(self, compute, project,
                 network_name,
                 subnetwork_name, preserve_external_ip, zone, region,
                 instance_group_name):
        """Initialize a InstanceNetworkMigration object

        Args:
          compute: google compute engine API
          project: project id
          network_name: target network
          subnetwork_name: target subnetwork
          preserve_external_ip: whether to preserve instances' external IPs
          zone: zone of a zonal instance group
          region: region of regional instance group
          instance_group_name: name
        """
        super(InstanceGroupNetworkMigration, self).__init__()
        self.instance_group = self.build_instance_group()
        self.instance_group_migration_handler = self.build_instance_group_handler()

    def build_instance_group(self) -> object:
        """ Create an InstanceGroup object.

        Args:
            instance_group_name: the name of the instance group

        Returns: an InstanceGroup object

        """
        instance_group_helper = InstanceGroupHelper(self.compute,
                                                    self.project,
                                                    self.instance_group_name,
                                                    self.region,
                                                    self.zone,
                                                    self.network_name,
                                                    self.subnetwork_name,
                                                    self.preserve_external_ip)
        instance_group = instance_group_helper.build_instance_group()
        return instance_group

    def build_instance_group_handler(self):
        """ Build instance group handler based on the type of the instance group

        Returns:

        """
        if self.instance_group == None:
            self.instance_group = self.build_instance_group()

        if isinstance(self.instance_group, UnmanagedInstanceGroup):

            self.instance_group_migration_handler = UnmanagedInstanceGroupMigration(
                self.compute, self.project,
                self.network_name,
                self.subnetwork_name, self.preserve_external_ip, self.zone,
                self.region,
                self.instance_group_name
            )
        else:

            self.instance_group_migration_handler = ManagedInstanceGroupMigration(
                self.compute, self.project,
                self.network_name,
                self.subnetwork_name, self.preserve_external_ip, self.zone,
                self.region,
                self.instance_group_name)
        return self.instance_group_migration_handler

    def network_migration(self):
        """ Network migration
        """
        if self.instance_group_migration_handler == None:
            warnings.warn('Unable to get the instance group resource.')
            return
        try:
            self.instance_group_migration_handler.network_migration()

        except Exception as e:
            warn(str(e), Warning)
            print(
                'The migration was failed. Rolling back to the original network.')
            try:
                self.rollback()
            except Exception as e:
                warnings.warn(str(e), Warning)
                raise RollbackError(
                    'Rollback failed. You may lose your original resource. Please refer \'backup.log\' file.')
            raise MigrationFailed('Rollback finished.')

    def rollback(self):
        """ Rollback to the original instance group
        """
        if self.instance_group == None or self.instance_group_migration_handler == None:
            print('Unable to fetch the instance group: %s.' % (
                self.instance_group_name))
            return
        else:
            self.instance_group_migration_handler.rollback()
