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
""" This class is used to build a migration handler
through a resource's selfLink.

"""
import re

from vm_network_migration.handlers.instance_group_network_migration import InstanceGroupNetworkMigration
from vm_network_migration.handlers.instance_network_migration import InstanceNetworkMigration


class MigrationHelper:
    def __init__(self, selfLink, network, subnetwork,
                 preserve_instance_external_ip):
        """ Initialization

        Args:
            selfLink: selfLink of the compute engine resource
            network: target network
            subnetwork: target subnet
            preserve_instance_external_ip: whether to preserve the external ip
            of the instances in this resource
        """
        self.selfLink = selfLink
        self.project = self.extract_project()
        self.zone = self.extract_zone()
        self.region = self.extract_region()
        self.instance = self.extract_instance()
        self.instance_group = self.extract_instance_group()
        self.backend_service = self.extract_backend_service()
        self.target_pool = self.extract_target_pool()
        self.forwarding_rule = self.extract_forwarding_rule()
        self.network = network
        self.subnetwork = subnetwork
        self.preserve_instance_external_ip = preserve_instance_external_ip

    def extract_project(self) -> str:
        """ Extract project id

        Returns: project id

        """
        project_match = re.search(r'\/projects\/(.*)\/', self.selfLink)
        if project_match != None:
            self.project = project_match[1]
        return self.project

    def extract_zone(self) -> str:
        """ Extract zone

        Returns: zone name

        """
        zone_match = re.search(r'\/zones\/(.*)\/', self.selfLink)
        if zone_match != None:
            self.zone = zone_match[1]
        return self.zone

    def extract_region(self) -> str:
        """ Extract region

        Returns: region name

        """
        region_match = re.search(r'\/regions\/(.*)\/',
                                 self.selfLink)
        if region_match != None:
            self.region = region_match[1]
        return self.region

    def extract_instance(self) -> str:
        """ Extract instance

        Returns: instance name

        """
        instance_match = re.search(r'\/instances\/(.*)\/',
                                   self.selfLink)
        if instance_match != None:
            self.instance = instance_match[1]
        return self.instance

    def extract_instance_group(self) -> str:
        """ Extract instance group name

        Returns: instance group name

        """
        instance_group_match = re.search(r'\/instanceGroups\/(.*)\/',
                                         self.selfLink)
        if instance_group_match != None:
            self.instance_group = instance_group_match[1]
        return self.instance_group

    def extract_backend_service(self) -> str:
        # TODO
        pass

    def extract_target_pool(self) -> str:
        # TODO
        pass

    def extract_forwarding_rule(self) -> str:
        # TODO
        pass

    def build_migration_handler(self) -> object:
        """ Build a migration handler

        Returns: a migration handler

        """
        if self.instance != None:
            return self.build_instance_migration_handler()
        elif self.instance_group != None:
            return self.build_instance_group_migration_handler()
        elif self.backend_service != None:
            return self.build_backend_service_migration_handler()
        elif self.target_pool != None:
            return self.build_target_pool_migration_handler()
        elif self.forwarding_rule != None:
            return self.build_forwarding_rule_migration_handler()

    def build_instance_group_migration_handler(self):
        """ Build an instance group migration handler

        Returns: InstanceGroupNetworkMigration

        """
        if self.instance_group != None:
            instance_group_migration_handler = InstanceGroupNetworkMigration(
                self.project,
                self.network,
                self.subnetwork,
                self.preserve_instance_external_ip,
                self.zone,
                self.region,
                self.instance_group)
            return instance_group_migration_handler

    def build_instance_migration_handler(self):
        """ Build an instance migration handler

        Returns: InstanceNetworkMigration

        """
        if self.instance != None:
            instance_migration_handler = InstanceNetworkMigration(
                self.project,
                self.zone,
                self.instance,
                self.network,
                self.subnetwork,
                self.preserve_instance_external_ip
            )
            return instance_migration_handler

    def build_backend_service_migration_handler(self):
        # TODO
        pass

    def build_forwarding_rule_migration_handler(self):
        # TODO
        pass

    def build_target_pool_migration_handler(self):
        # TODO
        pass
