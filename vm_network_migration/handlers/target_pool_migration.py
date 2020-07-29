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
""" TargetPoolMigration class: Handle the migration of a target pool.

"""
import warnings

from vm_network_migration.errors import *
from vm_network_migration.handler_helper.selfLink_executor import SelfLinkExecutor
from vm_network_migration.modules.target_pool_modules.target_pool import TargetPool
from vm_network_migration.utils import initializer


class TargetPoolMigration:
    @initializer
    def __init__(self, compute, project, target_pool_name, network, subnetwork,
                 preserve_instance_external_ip, region):
        """ Initialize a BackendServiceMigration object

        Args:
            project: project ID
            backend_service_name: name of the backend service
            network: target network
            subnetwork: target subnet
            preserve_instance_external_ip: whether preserve the external IP
            of the instances which serves this load balancer
            region: region of the internal load balancer
        """
        self.target_pool = TargetPool(self.compute, self.project,
                                      self.target_pool_name, self.region,
                                      self.network,
                                      self.subnetwork,
                                      self.preserve_instance_external_ip)
        self.instance_migration_handlers = []
        self.build_instance_migration_handlers()
        self.instance_group_migration_handlers = []
        self.build_instance_group_migration_handlers()

    def build_instance_migration_handlers(self):
        """ Use instance's selfLinks to create a list of InstanceMigrationHandler

        Returns:

        """
        for selfLink in self.target_pool.attached_single_instances_selfLinks:
            executor = SelfLinkExecutor(self.compute, selfLink,
                                        self.network,
                                        self.subnetwork,
                                        self.preserve_instance_external_ip)

            instance_migration_handler = executor.build_instance_migration_handler()
            self.instance_migration_handlers.append(instance_migration_handler)

    def build_instance_group_migration_handlers(self):
        """ Use instance group's selfLinks to create a list of
        InstanceGroupMigrationHandler

        Returns:

        """
        for selfLink in self.target_pool.attached_managed_instance_groups_selfLinks:
            executor = SelfLinkExecutor(self.compute, selfLink,
                                        self.network,
                                        self.subnetwork,
                                        self.preserve_instance_external_ip)

            instance_group_migration_handler = executor.build_instance_group_migration_handler()
            self.instance_group_migration_handlers.append(
                instance_group_migration_handler)

    def network_migration(self):
        """ Migrate the backends of the target pool one by one from a legacy
            network to the target subnet.

        """
        try:
            print('Migrating single instance backends')
            for instance_migration_handler in self.instance_migration_handlers:
                print('Migrating: ',
                      instance_migration_handler.original_instance_name)
                instance_migration_handler.network_migration()
                print('Reattaching the instance to the target pool')
                self.target_pool.add_instance(
                    instance_migration_handler.get_instance_selfLink())

            print('Migrating managed instance group backends')
            for instance_group_migration_handler in self.instance_group_migration_handlers:
                print('Migrating:',
                      instance_group_migration_handler.instance_group_name)
                instance_group_migration_handler.network_migration()
                print('Reattaching the instance group to the target pool')
                instance_group_migration_handler.instance_group.set_target_pool(
                    self.target_pool.selfLink)

        except Exception as e:
            warnings.warn(e, Warning)
            print(
                'The backend service migration was failed. '
                'Rolling back all the backends to its original network.')
            self.rollback()
            raise MigrationFailed('Rollback has been finished.')

    def rollback(self):
        """ Rollback

        Returns:

        """
        print('Rolling back the single instance backends')
        for instance_migration_handler in self.instance_migration_handlers:
            print('Target: ',
                  instance_migration_handler.original_instance_name)
            instance_migration_handler.rollback()
            print('Reattaching the instance to the target pool')
            self.target_pool.add_instance(
                instance_migration_handler.get_instance_selfLink())

        print('Migrating instance group backends')
        for instance_group_migration_handler in self.instance_group_migration_handlers:
            print('Target:',
                  instance_group_migration_handler.instance_group_name)
            instance_group_migration_handler.rollback()
            print('Reattaching the instance group to the target pool')
            instance_group_migration_handler.instance_group.set_target_pool(
                self.target_pool.selfLink)
