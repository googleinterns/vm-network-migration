from copy import deepcopy

from vm_network_migration.module_helpers.subnet_network_helper import SubnetNetworkHelper
from vm_network_migration.modules.regional_forwarding_rule import RegionalForwardingRule


class InternalRegionalForwardingRule(RegionalForwardingRule):
    def __init__(self, compute, project, forwarding_rule_name, network,
                 subnetwork, region):
        super(InternalRegionalForwardingRule, self).__init__(compute,
                                                             project,
                                                             forwarding_rule_name,
                                                             network,
                                                             subnetwork,
                                                             region)
        self.backend_service_selfLink = self.get_backend_service_selfLink()
        self.network_object = self.build_network_object()
        self.new_forwarding_rule_configs = self.get_new_forwarding_rule_with_new_network_info(
            self.forwarding_rule_configs)

    def build_network_object(self):
        subnetwork_factory = SubnetNetworkHelper(self.compute, self.project,
                                                 None, self.region)
        network_object = subnetwork_factory.generate_network(
            self.network,
            self.subnetwork)
        return network_object

    def get_target_pool_selfLink(self):
        """ Get the target pool serving the forwarding rule

        Returns: selfLink

        """
        if 'target' in self.forwarding_rule_configs:
            return self.forwarding_rule_configs['target']

    def get_backend_service_selfLink(self):
        """ Get the backend service serving the forwarding rule

        Returns: selfLink

        """
        if 'backendService' in self.forwarding_rule_configs:
            return self.forwarding_rule_configs['backendService']

    def get_new_forwarding_rule_with_new_network_info(self,
                                                      forwarding_rule_configs):

        new_forwarding_rule_configs = deepcopy(forwarding_rule_configs)
        new_forwarding_rule_configs[
            'network'] = self.network_object.network_link
        new_forwarding_rule_configs[
            'subnetwork'] = self.network_object.subnetwork_link
        return new_forwarding_rule_configs
