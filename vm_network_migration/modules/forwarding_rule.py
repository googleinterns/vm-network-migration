class ForwardingRule(object):
    def __init__(self, compute, project, forwarding_rule_name, network, subnetwork, preserve_instance_external_ip):
        """ Initialization

        Args:
            compute: Google Compute Engine
            project: Project ID
            forwarding_rule_name: name of the forwarding rule
            network: target network
            subnetwork: target subnet
            preserve_instance_external_ip: whether to preserve the IPs of
            the instances serving the backend service
        """
        self.compute = compute
        self.project = project
        self.forwarding_rule_name = forwarding_rule_name
        self.forwarding_rule_configs = None
        self.operations = None
        self.network = network
        self.subnetwork = subnetwork
        self.preserve_instance_external_ip = preserve_instance_external_ip

    def get_forwarding_rule_configs(self):
        pass