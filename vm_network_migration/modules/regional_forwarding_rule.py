from googleapiclient.http import HttpError
from vm_network_migration.modules.forwarding_rule import ForwardingRule
from vm_network_migration.modules.operations import Operations
import warnings

class RegionalForwardingRule(ForwardingRule):
    def __init__(self, compute, project, forwarding_rule_name, network,
                 subnetwork, region):
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
                                                     network, subnetwork)
        self.region = region
        self.forwarding_rule_configs = self.get_forwarding_rule_configs()
        self.operations = Operations(self.compute, self.project, None,
                                     self.region)

    def get_forwarding_rule_configs(self):
        """ Get the configs of the forwarding rule

        Returns: configs

        """
        return self.compute.forwardingRules().get(
            project=self.project,
            region=self.region,
            forwardingRule=self.forwarding_rule_name).execute()

    def delete_forwarding_rule(self) -> dict:
        """ Delete the forwarding rule

             Returns: a deserialized python object of the response

        """
        delete_forwarding_rule_operation = self.compute.forwardingRules().delete(
            project=self.project,
            region=self.region,
            forwardingRule=self.forwarding_rule_name).execute()
        self.operations.wait_for_region_operation(
            delete_forwarding_rule_operation['name'])
        return delete_forwarding_rule_operation

    def insert_forwarding_rule(self, forwarding_rule_config):
        """ Insert the forwarding rule

             Returns: a deserialized python object of the response

        """
        try:
            insert_forwarding_rule_operation = self.compute.forwardingRules().insert(
                project=self.project,
                region=self.region,
                body=forwarding_rule_config).execute()
            self.operations.wait_for_region_operation(
                insert_forwarding_rule_operation['name'])
            return insert_forwarding_rule_operation

        except HttpError as e:
            error_reason = e._get_reason()
            if 'internal IP is outside' in error_reason:
                warnings.warn(error_reason, Warning)
            print(
                'The original IP address of the forwarding rule was an ' \
                'ephemeral one. After the migration, a new IP address is ' \
                'assigned to the forwarding rule.')
            # Set the IPAddress to ephemeral one
            if 'IPAddress' in forwarding_rule_config:
                del forwarding_rule_config['IPAddress']
            insert_forwarding_rule_operation = self.compute.forwardingRules().insert(
                project=self.project,
                region=self.region,
                body=forwarding_rule_config).execute()
            self.operations.wait_for_region_operation(
                insert_forwarding_rule_operation['name'])
            return insert_forwarding_rule_operation
