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

import google.auth
from googleapiclient import discovery
from vm_network_migration.handler_helper.selfLink_executor import SelfLinkExecutor
from vm_network_migration.modules.target_pool import TargetPool


class TargetPoolMigration:
    def __init__(self, project, target_pool_name, network, subnetwork,
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
        self.compute = self.set_compute_engine()
        self.project = project
        self.region = region
        self.network = network
        self.subnetwork = subnetwork
        self.target_pool_name = target_pool_name
        self.preserve_instance_external_ip = preserve_instance_external_ip
        self.target_pool = TargetPool(self.compute, self.project,
                                      self.target_pool_name, self.region,
                                      self.network,
                                      self.subnetwork,
                                      self.preserve_instance_external_ip)
        self.instance_migration_handlers = []
        self.build_instance_migration_handlers()
        self.instance_group_migration_handlers = []
        self.build_instance_group_migration_handlers()

    def set_compute_engine(self):
        """ Credential setup

        Returns:google compute engine

        """
        credentials, default_project = google.auth.default()
        return discovery.build('compute', 'v1', credentials=credentials)

    def build_instance_migration_handlers(self):
        """ Use instance's selfLinks to create a list of InstanceMigrationHandler

        Returns:

        """
        for selfLink in self.target_pool.attached_single_instances_selfLinks:
            executor = SelfLinkExecutor(selfLink,
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
            executor = SelfLinkExecutor(selfLink,
                                        self.network,
                                        self.subnetwork,
                                        self.preserve_instance_external_ip)

            instance_group_migration_handler = executor.build_instance_group_migration_handler()
            self.instance_group_migration_handlers.append(
                instance_group_migration_handler)
        for selfLink in self.target_pool.attached_unmanaged_instance_groups_selfLinks:
            # In the current version, all the instances in the unmanaged instance
            # groups will be migrated to the new network. But in the next version,
            # the tool may give the user's options about how to process
            # these unmanaged instance groups and instance in these groups
            executor = SelfLinkExecutor(selfLink,
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
                print('Reattaching the instance backend')
                self.target_pool.add_instance(
                    instance_migration_handler.get_instance_selfLink())

            print('Migrating instance group backends')
            for instance_group_migration_handler in self.instance_group_migration_handlers:
                print('Migrating:',
                      instance_group_migration_handler.instance_group_name)
                instance_group_migration_handler.network_migration()
                print('Reattaching the instance group to the target pool')
                instance_group_migration_handler.instance_group.set_target_pool(
                    self.target_pool.selfLink)

        except Exception as e:
            warnings.warn(e, Warning)
            self.rollback()

    def rollback(self):
        pass
