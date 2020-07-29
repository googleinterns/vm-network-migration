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

""" ForwardingRuleMigration class: It is the handler to migrate
a forwarding rule based on the type of it.

"""
import warnings

from vm_network_migration.errors import *
from vm_network_migration.handler_helper.selfLink_executor import SelfLinkExecutor
from vm_network_migration.module_helpers.forwarding_rule_helper import ForwardingRuleHelper
from vm_network_migration.modules.forwarding_rule_modules.external_regional_forwarding_rule import ExternalRegionalForwardingRule
from vm_network_migration.modules.forwarding_rule_modules.global_forwarding_rule import GlobalForwardingRule
from vm_network_migration.modules.forwarding_rule_modules.internal_regional_forwarding_rule import InternalRegionalForwardingRule
from vm_network_migration.utils import initializer
from vm_network_migration.handlers.compute_engine_resource_migration import ComputeEngineResourceMigration

class ForwardingRuleMigration(ComputeEngineResourceMigration):
    @initializer
    def __init__(self, compute, project, forwarding_rule_name,
                 network_name, subnetwork_name,
                 preserve_instance_external_ip, region=None):
        """ Initialize a InstanceNetworkMigration object

        Args:
            project: project ID
            forwarding_rule_name: name of the forwarding rule
            network: target network
            subnetwork: target subnet
            preserve_instance_external_ip: whether preserve the external IP
            of the instances which serves this load balancer
            region: region of the internal load balancer
        """
        super(ForwardingRuleMigration, self).__init__()
        self.forwarding_rule = self.build_forwarding_rule()
        self.backends_migration_handlers = []

    def build_forwarding_rule(self):
        """ Use a helper class to create a ForwardingRule object

        Returns: a ForwardingRule object

        """
        forwarding_rule_helper = ForwardingRuleHelper(self.compute,
                                                      self.project,
                                                      self.forwarding_rule_name,
                                                      self.network_name,
                                                      self.subnetwork_name,
                                                      self.region)
        return forwarding_rule_helper.build_a_forwarding_rule()

    def migrate_an_external_regional_forwarding_rule(self):
        """ Network migration for an external regional forwarding rule.
        The external regional forwarding rule is in use by a target pool.
        So the tool will run the target pool migration.

        Returns:

        """
        target_pool_selfLink = self.forwarding_rule.target_pool_selfLink
        if target_pool_selfLink == None:
            print('No backends need to be migrated. Terminating the migration.')
            return
        selfLink_executor = SelfLinkExecutor(self.compute, target_pool_selfLink,
                                             self.network_name,
                                             self.subnetwork_name,
                                             self.preserve_instance_external_ip)
        backends_migration_handler = selfLink_executor.build_target_pool_migration_handler()
        self.backends_migration_handlers.append(backends_migration_handler)
        print('Migrating the target pool.')
        backends_migration_handler.network_migration()

    def migrate_an_internal_regional_forwarding_rule(self):
        """ Network migration for an internal regional forwarding rule.
        The internal regional forwarding rule will be in use by a single
        backend service. The forwarding rule will be deleted first.
        Then, the tool will migrate the backend service.
        Finally, recreate the forwarding rule in the target subnet.

        Returns:

        """
        backend_service_selfLink = self.forwarding_rule.backend_service_selfLink
        if backend_service_selfLink != None:

            selfLink_executor = SelfLinkExecutor(self.compute,
                                                 backend_service_selfLink,
                                                 self.network_name,
                                                 self.subnetwork_name,
                                                 self.preserve_instance_external_ip)
            backends_migration_handler = selfLink_executor.build_backend_service_migration_handler()
            self.backends_migration_handlers.append(backends_migration_handler)
            backend_service = backends_migration_handler.backend_service

            if backend_service.count_forwarding_rules() > 1:
                print(
                    'The backend service is associated with two or more forwarding rules, so it can not be migrated.')
                print(
                    'Unable to handle the one backend service to many forwarding rule case. Terminating. ')
                return

        print('Deleting the forwarding rule.')
        self.forwarding_rule.delete_forwarding_rule()
        for backend_service_migration_handler in self.backends_migration_handlers:
            print('Migrating the backend service.')
            backend_service_migration_handler.network_migration()
        print('Recreating the forwarding rule in the target subnet.')
        self.forwarding_rule.insert_forwarding_rule(
            self.forwarding_rule.new_forwarding_rule_configs)

    def migrate_a_global_forwarding_rule(self):
        """ Network migration for a global forwarding rule. The global
        forwarding rule points to a target proxy. Through the target proxy,
        the tool can find the backend services information.
        The tool will migrate these backends one by one without deleting
        and recreating.

        Returns:

        """
        backend_service_selfLinks = self.forwarding_rule.backend_service_selfLinks
        if backend_service_selfLinks == []:
            print('No backends need to be migrated. Terminating the migration.')
            return
        for selfLink in backend_service_selfLinks:
            selfLink_executor = SelfLinkExecutor(self.compute, selfLink,
                                                 self.network_name,
                                                 self.subnetwork_name,
                                                 self.preserve_instance_external_ip)
            backend_service_migration_handler = selfLink_executor.build_backend_service_migration_handler()
            # Save handlers for rollback purpose
            self.backends_migration_handlers.append(
                backend_service_migration_handler)
            backend_service_migration_handler.network_migration()

    def rollback_a_global_forwarding_rule(self):
        """ Rollback a global forwarding rule

        Returns:

        """
        for backend_service_migration_handler in self.backends_migration_handlers:
            backend_service_migration_handler.rollback()

    def rollback_an_internal_regional_forwarding_rule(self):
        """ Rollback an internal regional forwarding rule

        Returns:

        """
        if not self.forwarding_rule.migrated and \
                self.forwarding_rule.check_forwarding_rule_exists():
            return
        if self.forwarding_rule.migrated:
            print('Deleting the migrated forwarding rule.')
            self.forwarding_rule.delete_forwarding_rule()
            for backend_service_migration_handler in self.backends_migration_handlers:
                backend_service_migration_handler.rollback()
            self.forwarding_rule.insert_forwarding_rule(
                self.forwarding_rule.forwarding_rule_configs)
        else:
            for backend_service_migration_handler in self.backends_migration_handlers:
                backend_service_migration_handler.rollback()
            self.forwarding_rule.insert_forwarding_rule(
                self.forwarding_rule.forwarding_rule_configs)

    def rollback_an_external_regional_forwarding_rule(self):
        """ Rollback an external regional forwarding rule

        Returns:

        """
        for target_pool_migration_handler in self.backends_migration_handlers:
            target_pool_migration_handler.rollback()

    def network_migration(self):
        """ Select correct network migration functions based on the type of the
        forwarding rule.

        Returns:

        """
        print('Migrating: %s' %(self.forwarding_rule_name))
        try:
            if isinstance(self.forwarding_rule, ExternalRegionalForwardingRule):
                self.migrate_an_external_regional_forwarding_rule()
            elif isinstance(self.forwarding_rule,
                            InternalRegionalForwardingRule):
                self.migrate_an_internal_regional_forwarding_rule()
            elif isinstance(self.forwarding_rule, GlobalForwardingRule):
                self.migrate_a_global_forwarding_rule()
        except Exception as e:
            warnings.warn(e, Warning)
            self.rollback()
            raise MigrationFailed('Rollback has been finished.')

    def rollback(self):
        """ Error happens. Rollback to the original status.

        """
        print(
            'The migration was failed. Rolling back to the original forwarding rule settings.')
        if isinstance(self.forwarding_rule, ExternalRegionalForwardingRule):
            self.rollback_an_external_regional_forwarding_rule()
        elif isinstance(self.forwarding_rule, InternalRegionalForwardingRule):
            self.rollback_an_internal_regional_forwarding_rule()
        elif isinstance(self.forwarding_rule, GlobalForwardingRule):
            self.rollback_a_global_forwarding_rule()
        print('Rollback has been finished.')
