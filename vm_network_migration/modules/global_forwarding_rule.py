from vm_network_migration.errors import *
from vm_network_migration.modules.forwarding_rule import ForwardingRule


class GlobalForwardingRule(ForwardingRule):
    def __init__(self, compute, project, forwarding_rule_name, network,
                 subnetwork, preserve_instance_external_ip):
        super(GlobalForwardingRule, self).__init__(compute, project,
                                                   forwarding_rule_name,
                                                   network, subnetwork,
                                                   preserve_instance_external_ip)
        self.forwarding_rule_configs = self.get_forwarding_rule_configs()
        self.target_proxy_type = self.get_target_proxy_type()
        self.target_proxy_name = self.get_target_proxy_name()
        self.target_proxy_configs = self.get_target_proxy_configs()
        self.backend_service_selfLink = self.get_backend_service_selfLinks()

    def get_forwarding_rule_configs(self):
        return self.compute.globalForwardingRules().get(project=self.project,
                                                        forwardingRule=self.forwarding_rule_name).execute()

    # "target": "https://www.googleapis.com/compute/v1/projects/dakeying-devconsole/global/targetHttpProxies/http-external-legacy-target-proxy",
    def get_target_proxy_type(self):
        if 'target' in self.forwarding_rule_configs:
            return self.forwarding_rule_configs.split('/')[-2]

    def get_target_proxy_name(self):
        if 'target' in self.forwarding_rule_configs:
            return self.forwarding_rule_configs.split('/')[-1]

    def get_target_proxy_configs(self):
        if self.target_proxy_type == 'targetHttpProxies':
            compute_engine_api = self.compute.targetHttpProxies()
        elif self.target_proxy_type == 'targetHttpsProxies':
            compute_engine_api = self.compute.targetHttpsProxies()
        elif self.target_proxy_type == 'targetSslProxies':
            compute_engine_api = self.compute.targetSslProxies()
        elif self.target_proxy_type == 'targetTcpProxies':
            compute_engine_api = self.compute.targetTcpProxies()
        else:
            raise TargetTypeError(
                'The forwarding rule\'s target proxy type is not supported.')
        args = {
            'project': self.project,
            self.target_proxy_type: self.target_proxy_name
        }
        return compute_engine_api.get(**args).execute()

    def get_backend_service_selfLinks(self) -> list:
        """ Get all the backend services which are serving the forwarding rule

        Returns: a list pf backend service selfLink

        """
        if 'service' in self.target_proxy_configs:
            return [self.target_proxy_configs['service']]
        elif 'urlMap' in self.target_proxy_configs:
            backend_services_selfLinks = []
            urlMap_name = self.target_proxy_configs['urlMap'].split('/')[-1]
            urlMap_configs = self.compute.urlMaps().get(project=self.project,
                                                        urlMap=urlMap_name).execute()

            if 'defaultService' in urlMap_configs:
                backend_services_selfLinks.append(
                    urlMap_configs['defaultService'])
            if 'defaultRouteAction' in urlMap_configs and 'weightedBackendServices' in \
                    urlMap_configs['defaultRouteAction']:
                for weighted_backend_service in \
                urlMap_configs['defaultRouteAction']['weightedBackendServices']:
                    backend_services_selfLinks.append(
                        weighted_backend_service['backendService'])
            return backend_services_selfLinks
        return []