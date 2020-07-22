from vm_network_migration.modules.forwarding_rule import ForwardingRule


class RegionalForwardingRule(ForwardingRule):
    def __init__(self, compute, project, forwarding_rule_name, network,
                 subnetwork, preserve_instance_external_ip, region):
        """ Initialization

        Args:
            compute: google compute engine
            project: project id
            forwarding_rule_name: the name of the forwarding rule
            network: target network
            subnetwork: target subnet
            preserve_instance_external_ip: whether to preserve the IPs of
                the instances serving the backend service
            region: region of the forwarding rule
        """
        super(RegionalForwardingRule, self).__init__(compute, project,
                                                     forwarding_rule_name,
                                                     network, subnetwork,
                                                     preserve_instance_external_ip)
        self.region = region
        self.forwarding_rule_configs = self.get_forwarding_rule_configs()
        self.backend_service_selfLink = self.get_backend_service_selfLink()
        self.target_pool_selfLink = self.get_target_pool_selfLink()

    def get_forwarding_rule_configs(self):
        """ Get the configs of the forwarding rule

        Returns: configs

        """
        return self.compute.forwardingRules().get(
            project=self.project,
            region=self.region,
            forwardingRule=self.forwarding_rule_name).execute()

    def get_backend_service_selfLink(self):
        """ Get the backend service serving the forwarding rule

        Returns: selfLink

        """
        if 'backendService' in self.forwarding_rule_configs:
            return self.forwarding_rule_configs['backendService']

    def get_target_pool_selfLink(self):
        """ Get the target pool serving the forwarding rule

        Returns: selfLink

        """
        if 'target' in self.forwarding_rule_configs:
            return self.forwarding_rule_configs['target']
