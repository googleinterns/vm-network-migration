from vm_network_migration.modules.regional_forwarding_rule import RegionalForwardingRule


class ExternalRegionalForwardingRule(RegionalForwardingRule):
    def __init__(self, compute, project, forwarding_rule_name, network,
                 subnetwork, region):
        super(ExternalRegionalForwardingRule, self).__init__(compute, project,
                                                             forwarding_rule_name,
                                                             network,
                                                             subnetwork, region)
        self.target_pool_selfLink = self.get_target_pool_selfLink()

    def get_target_pool_selfLink(self):
        """ Get the target pool serving the forwarding rule

        Returns: selfLink

        """
        if 'target' in self.forwarding_rule_configs:
            return self.forwarding_rule_configs['target']
