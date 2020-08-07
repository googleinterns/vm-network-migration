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
""" GlobalForwardingRule class: external global forwarding rule
The supported target proxies are: targetHttpProxy,
targetHttpsProxy, targetTcpProxy, targetSslProxy.

"""
from vm_network_migration.errors import *
from vm_network_migration.modules.forwarding_rule_modules.forwarding_rule import ForwardingRule
from vm_network_migration.utils import find_all_matching_strings_from_a_dict
from vm_network_migration.handler_helper.selfLink_executor import SelfLinkExecutor

class ExternalGlobalForwardingRule(ForwardingRule):

    def __init__(self, compute, project, forwarding_rule_name, network,
                 subnetwork):
        super(ExternalGlobalForwardingRule, self).__init__(compute, project,
                                                   forwarding_rule_name,
                                                   network, subnetwork)
        self.forwarding_rule_configs = self.get_forwarding_rule_configs()
        self.backends_selfLinks = self.get_backends_selfLinks()
        self.log()

    def get_forwarding_rule_configs(self):
        """ Get configuration of the forwarding rule.

        Returns:

        """
        return self.compute.globalForwardingRules().get(
            project=self.project,
            forwardingRule=self.forwarding_rule_name).execute()


