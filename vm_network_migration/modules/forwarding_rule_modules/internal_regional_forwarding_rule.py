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
""" The regional forwarding rule which has an 'INTERNAL'
load balancing scheme

"""
from copy import deepcopy

from vm_network_migration.errors import *
from vm_network_migration.module_helpers.subnet_network_helper import SubnetNetworkHelper
from vm_network_migration.modules.forwarding_rule_modules.regional_forwarding_rule import RegionalForwardingRule
from vm_network_migration.utils import is_equal_or_contians


class InternalRegionalForwardingRule(RegionalForwardingRule):

    def __init__(self, compute, project, forwarding_rule_name, network,
                 subnetwork, region):
        super(InternalRegionalForwardingRule, self).__init__(compute,
                                                             project,
                                                             forwarding_rule_name,
                                                             network,
                                                             subnetwork,
                                                             region)
        self.backends_selfLinks = self.get_backends_selfLinks()
        self.network_object = self.build_network_object()
        self.new_forwarding_rule_configs = self.get_new_forwarding_rule_with_new_network_info(
            self.forwarding_rule_configs)
        self.log()

    def build_network_object(self):
        """ Create a SubnetNetwork object using the target subnet info

        Returns: a SubnetNetwork object

        """
        subnetwork_factory = SubnetNetworkHelper(self.compute, self.project,
                                                 None, self.region)
        network_object = subnetwork_factory.generate_network(
            self.network,
            self.subnetwork)
        return network_object

    def get_backend_service_selfLink(self):
        """ Get the backend service serving the forwarding rule

        Returns: selfLink

        """
        if 'backendService' in self.forwarding_rule_configs:
            return self.forwarding_rule_configs['backendService']
        elif 'target' in self.forwarding_rule_configs:
            return self.forwarding_rule_configs['target']

    def get_new_forwarding_rule_with_new_network_info(self,
                                                      forwarding_rule_configs):
        """

        Args:
            forwarding_rule_configs:

        Returns:

        """
        new_forwarding_rule_configs = deepcopy(forwarding_rule_configs)
        new_forwarding_rule_configs[
            'network'] = self.network_object.network_link
        new_forwarding_rule_configs[
            'subnetwork'] = self.network_object.subnetwork_link
        return new_forwarding_rule_configs

    def compare_original_network_and_target_network(self):
        if self.network_object == None or self.network_object.subnetwork_link == None:
            raise InvalidTargetNetworkError
        if 'subnetwork' not in self.forwarding_rule_configs:
            return False
        elif is_equal_or_contians(
                self.forwarding_rule_configs['subnetwork'],
                self.network_object.subnetwork_link):
            return True
        else:
            return False
