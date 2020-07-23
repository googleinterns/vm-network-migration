import warnings

import google.auth
from googleapiclient import discovery
from vm_network_migration.handler_helper.selfLink_executor import SelfLinkExecutor
from vm_network_migration.module_helpers.forwarding_rule_helper import ForwardingRuleHelper
from vm_network_migration.modules.external_regional_forwarding_rule import ExternalRegionalForwardingRule
from vm_network_migration.modules.global_forwarding_rule import GlobalForwardingRule
from vm_network_migration.modules.internal_regional_forwarding_rule import InternalRegionalForwardingRule


class ForwardingRuleMigration(object):
    def __init__(self, project, forwarding_rule_name,
                 network_name,
                 subnetwork_name, preserve_instance_external_ip, region=None
                 ):
        """ Initialize a InstanceNetworkMigration object

        Args:
            project: project ID
            zone: zone of the instance group
            region: region of the forwarding rule
        """
        self.compute = self.set_compute_engine()
        self.project = project
        self.network_name = network_name
        self.subnetwork_name = subnetwork_name
        self.preserve_instance_external_ip = preserve_instance_external_ip
        self.region = region
        self.forwarding_rule_name = forwarding_rule_name
        self.forwarding_rule = self.build_forwarding_rule()
        self.backends_migration_handlers = []

    def set_compute_engine(self):
        """ Credential setup

        Returns:google compute engine

        """
        credentials, default_project = google.auth.default()
        return discovery.build('compute', 'v1', credentials=credentials)

    def build_forwarding_rule(self):
        forwarding_rule_helper = ForwardingRuleHelper(self.compute,
                                                      self.project,
                                                      self.forwarding_rule_name,
                                                      self.network_name,
                                                      self.subnetwork_name,
                                                      self.region)
        return forwarding_rule_helper.build_a_forwarding_rule()

    def migrate_an_external_regional_forwarding_rule(self):
        target_pool_selfLink = self.forwarding_rule.target_pool_selfLink
        if target_pool_selfLink == None:
            print('No backends need to be migrated. Terminating the migration.')
        selfLink_executor = SelfLinkExecutor(target_pool_selfLink,
                                             self.network_name,
                                             self.subnetwork_name,
                                             self.preserve_instance_external_ip)
        backends_migration_handler = selfLink_executor.build_target_pool_migration_handler()
        self.backends_migration_handlers.append(backends_migration_handler)
        print('Migrating the target pool.')
        backends_migration_handler.network_migration()

    def migrate_an_internal_regional_forwarding_rule(self):
        backend_service_selfLink = self.forwarding_rule.backend_service_selfLink
        if backend_service_selfLink == None:
            print('No backends need to be migrated. Terminating the migration.')
        selfLink_executor = SelfLinkExecutor(backend_service_selfLink,
                                             self.network_name,
                                             self.subnetwork_name,
                                             self.preserve_instance_external_ip)
        backends_migration_handler = selfLink_executor.build_target_pool_migration_handler()
        backend_service = backends_migration_handler.backend_service
        # if not isinstance(backend_service, InternalBackendService):

        if not backend_service.has_only_one_forwarding_rules():
            print(
                'The backend service is associated with two or more forwarding rules, so it can not be migrated.')
            print(
                'Unable to handle the one backend service to many forwarding rule case. Terminating. ')
            return
        else:
            print('Deleting the forwarding rule.')
            self.forwarding_rule.delete_forwarding_rule()
            print('Migrating the backend service.')
            backends_migration_handler.network_migration()
            print('Recreating the forwarding rule in the target subnet.')
            self.forwarding_rule.insert_forwarding_rule(
                self.forwarding_rule.new_forwarding_rule_configs)

    def migrate_a_global_forwarding_rule(self):
        backend_service_selfLinks = self.forwarding_rule.backend_service_selfLinks
        for selfLink in backend_service_selfLinks:
            selfLink_executor = SelfLinkExecutor(selfLink, self.network_name,
                                                 self.subnetwork_name,
                                                 self.preserve_instance_external_ip)
            backends_migration_handler = selfLink_executor.build_backend_service_migration_handler()
            # Save handlers for rollback purpose
            self.backends_migration_handlers.append(backends_migration_handler)

        for backends_migration_handler in self.backends_migration_handlers:
            backends_migration_handler.network_migration()

    def rollback_a_global_forwarding_rule(self):
        pass

    def rollback_an_internal_regional_forwarding_rule(self):
        pass

    def rollback_an_external_regional_forwarding_rule(self):
        pass

    def network_migration(self):
        if self.forwarding_rule == None:
            print('Unable to find the forwarding rule. Terminating.')
            return
        try:
            if isinstance(self.forwarding_rule, ExternalRegionalForwardingRule):
                self.migrate_an_external_regional_forwarding_rule()
            elif isinstance(self.forwarding_rule, InternalRegionalForwardingRule):
                self.migrate_an_internal_regional_forwarding_rule()
            elif isinstance(self.forwarding_rule, GlobalForwardingRule):
                self.migrate_a_global_forwarding_rule()
        except Exception as e:
            warnings.warn(e, Warning)
            self.rollback()

    def rollback(self):
        pass
