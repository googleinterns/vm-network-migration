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
""" GlobalForwardingRule class: a global forwarding rule which is in use by a
Target proxy. The supported target proxies are: targetHttpProxy,
targetHttpsProxy, targetTcpProxy, targetSslProxy.

"""
from vm_network_migration.errors import *
from vm_network_migration.modules.forwarding_rule_modules.forwarding_rule import ForwardingRule
from vm_network_migration.utils import find_all_matching_strings_from_a_dict

class GlobalForwardingRule(ForwardingRule):
    proxy_type_to_proxy_keyword = {
        'targetHttpProxies': 'targetHttpProxy',
        'targetHttpsProxies': 'targetHttpsProxy',
        'targetTcpProxies': 'targetTcpProxy',
        'targetSslProxies': 'targetSslProxy'
    }

    def __init__(self, compute, project, forwarding_rule_name, network,
                 subnetwork):
        super(GlobalForwardingRule, self).__init__(compute, project,
                                                   forwarding_rule_name,
                                                   network, subnetwork)
        self.forwarding_rule_configs = self.get_forwarding_rule_configs()
        self.backend_service_selfLinks = self.get_backend_service_selfLinks()

    def get_forwarding_rule_configs(self):
        """ Get configuration of the forwarding rule.

        Returns:

        """
        return self.compute.globalForwardingRules().get(
            project=self.project,
            forwardingRule=self.forwarding_rule_name).execute()

    def get_target_proxy_type(self) -> str:
        """ Get the type of the target proxy

        Returns: type of the target proxy

        """
        if 'target' in self.forwarding_rule_configs:
            return self.forwarding_rule_configs['target'].split('/')[-2]

    def get_target_proxy_name(self) -> str:
        """ Get the name of the target proxy

        Returns: name of the target proxy

        """
        if 'target' in self.forwarding_rule_configs:
            return self.forwarding_rule_configs['target'].split('/')[-1]

    def get_target_proxy_configs(self, target_proxy_type, target_proxy_name):
        """ Get the target proxy configs

        Args:
            target_proxy_type: type of the target proxy
            target_proxy_name: name of the target proxy

        Returns:

        """
        proxy_type_to_compute_api = {
            'targetHttpProxies': self.compute.targetHttpProxies(),
            'targetHttpsProxies': self.compute.targetHttpsProxies(),
            'targetTcpProxies': self.compute.targetTcpProxies(),
            'targetSslProxies': self.compute.targetSslProxies()
        }

        if target_proxy_type in proxy_type_to_compute_api:
            compute_engine_api = proxy_type_to_compute_api[target_proxy_type]
        else:
            raise TargetTypeError(
                'The forwarding rule\'s target proxy type is not supported.')
        args = {
            'project': self.project,
            GlobalForwardingRule.proxy_type_to_proxy_keyword[
                target_proxy_type]: target_proxy_name
        }

        return compute_engine_api.get(**args).execute()

    def get_backend_service_selfLinks_from_target_proxy_configs(self,
                                                                target_proxy_configs) -> list:
        """ Get all the backend services which are serving the forwarding rule

        Returns: a list pf backend service selfLink

        """
        if 'service' in target_proxy_configs:
            return [target_proxy_configs['service']]
        elif 'urlMap' in target_proxy_configs:
            backend_services_selfLinks = set()
            urlMap_name = target_proxy_configs['urlMap'].split('/')[-1]
            urlMap_configs = self.compute.urlMaps().get(project=self.project,
                                                        urlMap=urlMap_name).execute()
            find_all_matching_strings_from_a_dict(urlMap_configs, "compute/v1/projects/", backend_services_selfLinks)
            print('DEBUGGING LINKS:', backend_services_selfLinks)
            # if 'defaultService' in urlMap_configs:
            #     backend_services_selfLinks.append(
            #         urlMap_configs['defaultService'])
            # if 'defaultRouteAction' in urlMap_configs and 'weightedBackendServices' in \
            #         urlMap_configs['defaultRouteAction']:
            #     for weighted_backend_service in \
            #             urlMap_configs['defaultRouteAction'][
            #                 'weightedBackendServices']:
            #         backend_services_selfLinks.append(
            #             weighted_backend_service['backendService'])
            # if 'pathMatchers' in urlMap_configs:

            return list(backend_services_selfLinks)
        return []

    def get_backend_service_selfLinks(self) -> list:
        """ Get the selfLinks of all the backend service which is in use by
        this forwarding rule.

        Returns: list of selfLinks

        """
        if self.forwarding_rule_configs != None:
            target_proxy_type = self.get_target_proxy_type()
            target_proxy_name = self.get_target_proxy_name()
            target_proxy_configs = self.get_target_proxy_configs(
                target_proxy_type, target_proxy_name)
            return self.get_backend_service_selfLinks_from_target_proxy_configs(
                target_proxy_configs)
        return []