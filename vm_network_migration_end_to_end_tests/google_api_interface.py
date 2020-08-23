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
""" Basic Google Client API function call

"""

from vm_network_migration.modules.other_modules.operations import Operations


class GoogleApiInterface:
    def __init__(self, compute, project, region, zone):
        self.compute = compute
        self.project = project
        self.region = region
        self.zone = zone
        self.operation = Operations(self.compute, self.project, self.zone,
                                    self.region)
        self.autoscalers = []
        self.region_autoscalers = []
        self.unmanaged_instance_groups = []
        self.region_managed_instance_groups = []
        self.single_zone_managed_instance_groups = []
        self.instances = []
        self.instance_templates = []
        self.disks = []
        self.external_addresses = []
        self.target_pools = []
        self.target_instances = []
        self.healthcheck = []
        self.internal_backend_service = []
        self.global_backend_services = []
        self.regional_backend_services = []
        self.external_backend_service = []
        self.regional_forwarding_rules = []
        self.global_forwarding_rules = []
        self.urlmappings = []
        self.target_http_proxies = []
        self.target_tcp_proxies = []
        self.target_https_proxies = []
        self.target_ssl_proxies = []
        self.target_grpc_proxies = []
        self.networks = []
        self.subnetworks = []
        self.ssl_certificates = []
        self.possible_reserved_ips = []

    def get_list_of_zones_from_regions(self):
        return self.compute.regions().get(project=self.project,
                                          region=self.region).execute()['zones']

    def create_unmanaged_instance_group_with_instances(self, configs,
                                                       instances):
        """ Create the instance group

        Returns: a deserialized object of the response

        """
        create_instance_group_operation = self.compute.instanceGroups().insert(
            project=self.project,
            zone=self.zone,
            body=configs).execute()
        self.unmanaged_instance_groups.append(configs['name'])
        self.operation.wait_for_zone_operation(
            create_instance_group_operation['name'])
        instance_links = []
        for instance in instances:
            instance_links.append(
                self.get_instance_configs(instance)['selfLink'])

        for instance_link in instance_links:
            insert_instance_operation = self.compute.instanceGroups().addInstances(
                project=self.project, zone=self.zone,
                instanceGroup=configs['name'],
                body={
                    "instances": [{
                        "instance": instance_link}]}).execute()
            self.operation.wait_for_zone_operation(
                insert_instance_operation['name'])
        return create_instance_group_operation

    def list_instances_in_unmanaged_instance_group(self, instance_group_name):
        operation = self.compute.instanceGroups().listInstances(
            project=self.project,
            zone=self.zone,
            instanceGroup=instance_group_name
        ).execute()
        if 'items' not in operation:
            return []
        instance_configs = operation['items']
        instances = []
        for instance_configs in instance_configs:
            instances.append(instance_configs['instance'].split('/')[-1])
        return instances

    def get_unmanaged_instance_group_configs(self, instance_group_name):
        get_instance_group_operation = self.compute.instanceGroups().get(
            project=self.project,
            zone=self.zone,
            instanceGroup=instance_group_name
        ).execute()
        return get_instance_group_operation

    def delete_unmanaged_instance_group(self, instance_group_name):
        delete_instance_group_operation = self.compute.instanceGroups().delete(
            project=self.project,
            zone=self.zone,
            instanceGroup=instance_group_name
        ).execute()
        self.operation.wait_for_zone_operation(
            delete_instance_group_operation['name'])
        return delete_instance_group_operation

    def create_single_zone_managed_instance_group(self, configs):
        create_instance_group_operation = self.compute.instanceGroupManagers().insert(
            project=self.project,
            zone=self.zone,
            body=configs
        ).execute()
        self.operation.wait_for_zone_operation(
            create_instance_group_operation['name']
        )
        self.single_zone_managed_instance_groups.append(configs['name'])

    def get_single_zone_managed_instance_group_configs(self,
                                                       instance_group_name):
        get_instance_group_operation = self.compute.instanceGroupManagers().get(
            project=self.project,
            zone=self.zone,
            instanceGroupManager=instance_group_name
        ).execute()
        return get_instance_group_operation

    def delete_single_zone_managed_instance_group_configs(self,
                                                          instance_group_name):
        delete_instance_group_operation = self.compute.instanceGroupManagers().delete(
            project=self.project,
            zone=self.zone,
            instanceGroupManager=instance_group_name
        ).execute()
        self.operation.wait_for_zone_operation(
            delete_instance_group_operation['name'])
        return delete_instance_group_operation

    def create_multi_zone_managed_instance_group(self, configs):
        configs['distributionPolicy'] = {
            "zones": []}
        all_valid_zones = self.get_list_of_zones_from_regions()
        for zone in all_valid_zones:
            configs['distributionPolicy']['zones'].append({
                'zone': zone})
        create_instance_group_operation = self.compute.regionInstanceGroupManagers().insert(
            project=self.project,
            region=self.region,
            body=configs
        ).execute()
        self.operation.wait_for_region_operation(
            create_instance_group_operation['name']
        )
        self.region_managed_instance_groups.append(configs['name'])
        return create_instance_group_operation

    def get_multi_zone_managed_instance_group_configs(self,
                                                      instance_group_name):
        get_instance_group_operation = self.compute.regionInstanceGroupManagers().get(
            project=self.project,
            region=self.region,
            instanceGroupManager=instance_group_name
        ).execute()
        return get_instance_group_operation

    def get_multi_zone_instance_template_configs(self, instance_group_name):
        instance_group_config = self.get_multi_zone_managed_instance_group_configs(
            instance_group_name)
        instance_template_name = \
            instance_group_config['instanceTemplate'].split('/')[-1]
        return self.get_instance_template_body(instance_template_name)

    def delete_multi_zone_managed_instance_group_configs(self,
                                                         instance_group_name):
        delete_instance_group_operation = self.compute.regionInstanceGroupManagers().delete(
            project=self.project,
            region=self.region,
            instanceGroupManager=instance_group_name
        ).execute()
        self.operation.wait_for_region_operation(
            delete_instance_group_operation['name'])
        return delete_instance_group_operation

    def create_instance(self, instance_configs, template_selfLink=None) -> dict:
        """ Create the instance using self.instance_template

            Returns:
                a deserialized object of the response

            Raises:
                googleapiclient.errors.HttpError: invalid request
        """
        if template_selfLink == None:
            create_instance_operation = self.compute.instances().insert(
                project=self.project,
                zone=self.zone,
                body=instance_configs).execute()
        else:
            create_instance_operation = self.compute.instances().insert(
                project=self.project,
                zone=self.zone,
                sourceInstanceTemplate=template_selfLink,
                body=instance_configs).execute()
        self.operation.wait_for_zone_operation(
            create_instance_operation['name'])
        self.instances.append(instance_configs['name'])
        external_ip = self.get_instance_external_ip(instance_configs['name'])
        self.possible_reserved_ips.append(external_ip)
        return create_instance_operation

    def get_instance_selfLink(self, instance_name):
        configs = self.compute.instances().get(project=self.project,
                                               zone=self.zone,
                                               instance=instance_name).execute()
        return configs['selfLink']

    def attach_disk(self, instance_name, disk_selfLink):
        operation = self.compute.instances().attachDisk(project=self.project,
                                                        zone=self.zone,
                                                        instance=instance_name,
                                                        body={
                                                            'source': disk_selfLink}).execute()

        self.operation.wait_for_zone_operation(operation['name'])
        return operation

    def delete_instance(self, instance_name) -> dict:
        delete_instance_operation = self.compute.instances().delete(
            project=self.project,
            zone=self.zone,
            instance=instance_name
        ).execute()
        self.operation.wait_for_zone_operation(
            delete_instance_operation['name'])
        return delete_instance_operation

    def stop_instance(self, instance_name) -> dict:
        stop_instance_operation = self.compute.instances().stop(
            project=self.project,
            zone=self.zone,
            instance=instance_name
        ).execute()
        self.operation.wait_for_zone_operation(stop_instance_operation['name'])
        return stop_instance_operation

    def get_instance_configs(self, instance_name):
        instance_template = self.compute.instances().get(
            project=self.project,
            zone=self.zone,
            instance=instance_name).execute()
        return instance_template

    def get_instance_external_ip(self, instance_name):
        configs = self.get_instance_configs(instance_name)
        try:
            return configs['networkInterfaces'][0]['accessConfigs'][0]['natIP']
        except:
            return None

    def get_instance_network_selfLink(self, instance_name):
        configs = self.get_instance_configs(instance_name)
        try:
            return configs['networkInterfaces'][0]['network']
        except:
            return None

    def get_regional_instance_group_network_selfLink(self, instance_group_name):
        instance_template_name = \
            self.get_multi_zone_managed_instance_group_configs(
                instance_group_name)[
                'instanceTemplate'].split('/')[-1]
        return \
            self.get_instance_template_body(instance_template_name)[
                'properties'][
                'networkInterfaces'][0]['network']

    def create_disk(self, disk_config):
        create_disk_operation = self.compute.disks().insert(
            project=self.project, zone=self.zone,
            body=disk_config).execute()
        self.operation.wait_for_zone_operation(create_disk_operation['name'])
        self.disks.append(disk_config['name'])
        return create_disk_operation

    def delete_disk(self, disk_name):
        delete_disk_operation = self.compute.disks().delete(
            project=self.project, zone=self.zone, disk=disk_name).execute()
        self.operation.wait_for_zone_operation(delete_disk_operation['name'])
        return delete_disk_operation

    def create_autoscaler(self, configs):
        create_autoscaler_operation = self.compute.autoscalers().insert(
            project=self.project, zone=self.zone, body=configs).execute()
        self.operation.wait_for_zone_operation(
            create_autoscaler_operation['name'])
        self.autoscalers.append(configs['name'])
        return create_autoscaler_operation

    def get_autoscaler(self, autoscaler_name):
        return self.compute.autoscalers().get(
            project=self.project,
            zone=self.zone,
            autoscaler=autoscaler_name
        ).execute()

    def get_region_autoscaler(self, autoscaler_name):
        return self.compute.regionAutoscalers().get(
            project=self.project,
            region=self.region,
            autoscaler=autoscaler_name
        ).execute()

    def delete_autoscaler(self, autoscaler_name):
        delete_autoscaler_operation = self.compute.autoscalers().delete(
            project=self.project,
            zone=self.zone,
            autoscaler=autoscaler_name
        ).execute()
        self.operation.wait_for_zone_operation(
            delete_autoscaler_operation['name'])
        return delete_autoscaler_operation

    def create_region_autoscaler(self, configs):
        create_autoscaler_operation = self.compute.regionAutoscalers().insert(
            project=self.project, region=self.region, body=configs).execute()
        self.operation.wait_for_region_operation(
            create_autoscaler_operation['name'])
        self.region_autoscalers.append(configs['name'])
        return create_autoscaler_operation

    def delete_region_autoscaler(self, autoscaler_name):
        delete_autoscaler_operation = self.compute.regionAutoscalers().delete(
            project=self.project,
            region=self.region,
            autoscaler=autoscaler_name
        ).execute()
        self.operation.wait_for_region_operation(
            delete_autoscaler_operation['name'])
        return delete_autoscaler_operation

    def create_instance_template(self, instance_template_configs):
        create_instance_template_operation = self.compute.instanceTemplates().insert(
            project=self.project, body=instance_template_configs).execute()
        self.operation.wait_for_global_operation(
            create_instance_template_operation['name'])
        self.instance_templates.append(instance_template_configs['name'])
        return create_instance_template_operation

    def delete_instance_template(self, instance_template_name):
        delete_instance_template_operation = self.compute.instanceTemplates().delete(
            project=self.project,
            instanceTemplate=instance_template_name).execute()
        self.operation.wait_for_global_operation(
            delete_instance_template_operation['name'])

    def list_instance_template_names_begin_with_suffix(self, suffix):
        instance_template_name_list = []
        operation = self.compute.instanceTemplates().list(
            project=self.project).execute()

        for instance_template in operation['items']:
            if instance_template['name'].startswith(suffix):
                instance_template_name_list.append(instance_template['name'])

        return instance_template_name_list

    def retrieve_instance_template_name(self, instance_zone_configs):
        instance_template_link = instance_zone_configs['instanceTemplate']
        return instance_template_link.split('/')[-1]

    def get_instance_template_body(self, instance_template_name) -> dict:
        """ Get the instance template's configs

        Returns: a deserialized object of the response

        """
        return self.compute.instanceTemplates().get(project=self.project,
                                                    instanceTemplate=instance_template_name).execute()

    def insert_address(self, external_ip_address, address_name):
        operation = self.compute.addresses().insert(project=self.project,
                                                    region=self.region,
                                                    body=self.generate_external_ip_address_body(
                                                        external_ip_address,
                                                        address_name)).execute()
        self.operation.wait_for_region_operation(operation['name'])
        self.external_addresses.append(address_name)
        return operation

    def delete_address(self, external_ip_address_name):
        delete_operation = self.compute.addresses().delete(project=self.project,
                                                           region=self.region,
                                                           address=external_ip_address_name).execute()
        self.operation.wait_for_region_operation(delete_operation['name'])
        return delete_operation

    def generate_external_ip_address_body(self, external_ip, address_name):
        """Generate external IP address.

        Returns:
              {
              name: "ADDRESS_NAME",
              address: "IP_ADDRESS"
            }
        """
        external_ip_address_body = {}
        external_ip_address_body[
            'name'] = address_name
        external_ip_address_body['address'] = external_ip
        return external_ip_address_body

    def create_target_pool(self, target_pool_configs):
        opertaion = self.compute.targetPools().insert(project=self.project,
                                                      region=self.region,
                                                      body=target_pool_configs).execute()
        self.operation.wait_for_region_operation(opertaion['name'])
        self.target_pools.append(target_pool_configs['name'])
        return opertaion

    def get_target_pool_config(self, target_pool_name):
        operation = self.compute.targetPools().get(project=self.project,
                                                   region=self.region,
                                                   targetPool=target_pool_name).execute()
        return operation

    def delete_a_target_pool(self, target_pool_name):
        operation = self.compute.targetPools().delete(project=self.project,
                                                      region=self.region,
                                                      targetPool=target_pool_name).execute()
        self.operation.wait_for_region_operation(operation['name'])
        return operation

    def create_target_instance(self, target_instance_configs):
        operation = self.compute.targetInstances().insert(project=self.project,
                                                          zone=self.zone,
                                                          body=target_instance_configs).execute()
        self.operation.wait_for_zone_operation(operation['name'])
        self.target_instances.append(target_instance_configs['name'])
        return operation

    def delete_target_instance(self, target_instance_name):
        operation = self.compute.targetInstances().delete(project=self.project,
                                                          zone=self.zone,
                                                          targetInstance=target_instance_name).execute()
        self.operation.wait_for_zone_operation(operation['name'])
        return operation

    def get_target_instance_configs(self, target_instance_name):
        operation = self.compute.targetInstances().get(project=self.project,
                                                       zone=self.zone,
                                                       targetInstance=target_instance_name).execute()
        return operation

    def add_instances_to_target_pool(self, target_pool_name, instance_selfLink):
        add_instance_body = {
            "instances": [{
                "instance": instance_selfLink}]}
        operation = self.compute.targetPools().addInstance(project=self.project,
                                                           region=self.region,
                                                           targetPool=target_pool_name,
                                                           body=add_instance_body).execute()
        self.operation.wait_for_region_operation(operation['name'])
        return operation

    def get_instances_selfLink_list_from_target_pool(self, target_pool_name):
        operation = self.compute.targetPools().get(project=self.project,
                                                   region=self.region,
                                                   targetPool=target_pool_name).execute()
        return operation['instances']

    def regional_instance_group_set_target_pool(self, instance_group,
                                                target_pool_selfLink):
        """ Set the target pool of the managed instance group

        Args:
            target_pool_selfLink: selfLink of the target pool

        Returns: a deserialized Python object of the response

        """
        args = {
            'project': self.project,
            'instanceGroupManager': instance_group,
            'body': {
                "targetPools": [
                    target_pool_selfLink
                ]
            },
            'region': self.region

        }
        set_target_pool_operation = self.compute.regionInstanceGroupManagers().setTargetPools(
            **args).execute()

        self.operation.wait_for_region_operation(
            set_target_pool_operation['name'])

        return set_target_pool_operation

    def delete_all_firewalls(self):
        request = self.compute.firewalls().list(project=self.project)

        response = request.execute()

        for firewall in response['items']:
            # delete it

            if 'denied' in firewall:
                delete_operation = self.compute.firewalls().delete(
                    project=self.project, firewall=firewall['name']).execute()
                self.operation.wait_for_global_operation(
                    delete_operation['name'])

    def delete_all_firewalls_of_a_target_network(self, network_name):
        request = self.compute.firewalls().list(project=self.project)

        response = request.execute()

        for firewall in response['items']:
            # delete it
            if firewall['name'].startswith(network_name):
                delete_operation = self.compute.firewalls().delete(
                    project=self.project, firewall=firewall['name']).execute()
                self.operation.wait_for_global_operation(
                    delete_operation['name'])
                print('deleted firewall:', firewall['name'])

    def add_a_firewall(self, firewall_config):
        operation = self.compute.firewalls().insert(project=self.project,
                                                    body=firewall_config).execute()
        self.operation.wait_for_global_operation(operation['name'])
        return operation

    def add_healthcheck(self, healthcheck_configs):
        operation = self.compute.healthChecks().insert(project=self.project,
                                                       body=healthcheck_configs).execute()
        self.operation.wait_for_global_operation(operation['name'])
        self.healthcheck.append(healthcheck_configs['name'])
        return operation

    def get_healthcheck(self, healthcheck_name):
        operation = self.compute.healthChecks().get(project=self.project,
                                                    healthCheck=healthcheck_name).execute()
        return operation

    def delete_healthcheck(self, healthcheck_name):
        operation = self.compute.healthChecks().delete(project=self.project,
                                                       healthCheck=healthcheck_name).execute()
        self.operation.wait_for_global_operation(operation['name'])
        return operation

    def create_internal_backend_service(self, backend_service_configs):
        operation = self.compute.regionBackendServices().insert(
            project=self.project,
            region=self.region,
            body=backend_service_configs).execute()

        self.operation.wait_for_region_operation(operation['name'])
        self.internal_backend_service.append(backend_service_configs['name'])
        return operation

    def create_regional_backend_service(self, backend_service_configs):
        operation = self.compute.regionBackendServices().insert(
            project=self.project,
            region=self.region,
            body=backend_service_configs).execute()

        self.operation.wait_for_region_operation(operation['name'])
        self.regional_backend_services.append(backend_service_configs['name'])
        return operation

    def get_backends_links_from_backend_service_configs(self,
                                                        backend_service_configs):
        if 'backends' not in backend_service_configs:
            return []
        backends = backend_service_configs['backends']
        backends_links = []
        for backend in backends:
            backends_links.append(backend['group'])
        return backends_links

    def delete_internal_backend_service(self, backend_service_name):

        operation = self.compute.regionBackendServices().delete(
            project=self.project,
            region=self.region,
            backendService=backend_service_name).execute()

        self.operation.wait_for_region_operation(operation['name'])
        return operation

    def delete_regional_backend_service(self, backend_service_name):

        operation = self.compute.regionBackendServices().delete(
            project=self.project,
            region=self.region,
            backendService=backend_service_name).execute()

        self.operation.wait_for_region_operation(operation['name'])
        return operation

    def create_external_backend_service(self, backend_service_configs):
        operation = self.compute.backendServices().insert(
            project=self.project,
            body=backend_service_configs).execute()

        self.operation.wait_for_global_operation(operation['name'])
        self.external_backend_service.append(backend_service_configs['name'])
        return operation

    def create_global_backend_service(self, backend_service_configs):
        operation = self.compute.backendServices().insert(
            project=self.project,
            body=backend_service_configs).execute()

        self.operation.wait_for_global_operation(operation['name'])
        self.global_backend_services.append(backend_service_configs['name'])
        return operation

    def delete_external_backend_service(self, backend_service_name):
        operation = self.compute.backendServices().delete(
            project=self.project,
            backendService=backend_service_name).execute()
        print('deleting backend service')
        self.operation.wait_for_global_operation(operation['name'])
        return operation

    def delete_global_backend_service(self, backend_service_name):
        operation = self.compute.backendServices().delete(
            project=self.project,
            backendService=backend_service_name).execute()
        print('deleting backend service')
        self.operation.wait_for_global_operation(operation['name'])
        return operation

    def get_internal_backend_service_configs(self, backend_service_name):
        return self.compute.regionBackendServices().get(project=self.project,
                                                        region=self.region,
                                                        backendService=backend_service_name).execute()

    def get_regional_backend_service_configs(self, backend_service_name):
        return self.compute.regionBackendServices().get(project=self.project,
                                                        region=self.region,
                                                        backendService=backend_service_name).execute()

    def get_external_backend_service_configs(self, backend_service_name):
        return self.compute.backendServices().get(project=self.project,
                                                  backendService=backend_service_name).execute()

    def get_global_backend_service_configs(self, backend_service_name):
        return self.compute.backendServices().get(project=self.project,
                                                  backendService=backend_service_name).execute()

    def create_regional_forwarding_rule(self, forwarding_rule_configs):
        operation = self.compute.forwardingRules().insert(project=self.project,
                                                          region=self.region,
                                                          body=forwarding_rule_configs).execute()
        self.operation.wait_for_region_operation(operation['name'])
        self.regional_forwarding_rules.append(forwarding_rule_configs['name'])
        return operation

    def delete_regional_forwarding_rule(self, forwarding_rule_name):
        operation = self.compute.forwardingRules().delete(project=self.project,
                                                          region=self.region,
                                                          forwardingRule=forwarding_rule_name).execute()
        self.operation.wait_for_region_operation(operation['name'])

        return operation

    def get_regional_forwarding_rule_config(self, forwarding_rule_name):
        return self.compute.forwardingRules().get(project=self.project,
                                                  region=self.region,
                                                  forwardingRule=forwarding_rule_name).execute()

    def create_global_forwarding_rule(self, forwarding_rule_configs):
        operation = self.compute.globalForwardingRules().insert(
            project=self.project,

            body=forwarding_rule_configs).execute()
        print('waiting for forwarding rule creation')
        self.operation.wait_for_global_operation(operation['name'])
        self.global_forwarding_rules.append(forwarding_rule_configs['name'])
        return operation

    def delete_global_forwarding_rule(self, forwarding_rule_name):
        operation = self.compute.globalForwardingRules().delete(
            project=self.project,
            forwardingRule=forwarding_rule_name).execute()
        self.operation.wait_for_global_operation(operation['name'])

        return operation

    def get_global_forwarding_rule_config(self, forwarding_rule_name):
        return self.compute.globalForwardingRules().get(
            project=self.project,
            forwardingRule=forwarding_rule_name).execute()

    def create_urlmapping(self, urlmapping_configs):
        operation = self.compute.urlMaps().insert(project=self.project,
                                                  body=urlmapping_configs).execute()
        self.operation.wait_for_global_operation(operation['name'])
        self.urlmappings.append(urlmapping_configs['name'])
        return operation

    def delete_urlmapping(self, urlmapping_name):
        operation = self.compute.urlMaps().delete(project=self.project,
                                                  urlMap=urlmapping_name).execute()
        print(operation)
        self.operation.wait_for_global_operation(operation['name'])
        return operation

    def create_http_proxy(self, http_proxy_name, urlmapping_selfLink):
        body = {
            "name": http_proxy_name,
            "urlMap": urlmapping_selfLink
        }
        operation = self.compute.targetHttpProxies().insert(
            project=self.project, body=body).execute()
        self.operation.wait_for_global_operation(operation['name'])
        self.target_http_proxies.append(http_proxy_name)
        return operation

    def create_tcp_proxy(self, tcp_proxy_name, backend_service_selfLink):
        body = {
            "description": "",
            "name": tcp_proxy_name,
            "proxyHeader": "NONE",
            "service": backend_service_selfLink
        }
        operation = self.compute.targetTcpProxies().insert(
            project=self.project, body=body).execute()
        self.operation.wait_for_global_operation(operation['name'])
        self.target_tcp_proxies.append(tcp_proxy_name)
        return operation

    def create_ssl_proxy(self, proxy_name, backend_service_selfLink,
                         ssl_certificate_selfLink):
        body = {
            "name": proxy_name,
            "proxyHeader": "NONE",
            "service": backend_service_selfLink,
            "sslCertificates": [
                ssl_certificate_selfLink
            ]
        }
        operation = self.compute.targetSslProxies().insert(
            project=self.project, body=body).execute()
        self.operation.wait_for_global_operation(operation['name'])
        self.target_ssl_proxies.append(proxy_name)
        return operation

    def create_grpc_proxy(self, proxy_name, urlmap_selfLink):
        body = {
            "name": proxy_name,
            "urlMap": urlmap_selfLink,
            "validateForProxyless": False
        }
        operation = self.compute.targetGrpcProxies().insert(
            project=self.project, body=body
        ).execute()
        self.operation.wait_for_global_operation(operation['name'])
        self.target_grpc_proxies.append(proxy_name)
        return operation

    def create_ssl_certificate(self, name):
        body = {
            "name": name,
            "managed": {
                "domains": [
                    "www.example.com"
                ],
                "domainStatus": {
                    "www.example.com": "FAILED_NOT_VISIBLE"
                }
            },
            "type": "MANAGED"
        }
        operation = self.compute.sslCertificates().insert(
            project=self.project,
            body=body).execute()
        self.operation.wait_for_global_operation(operation['name'])
        self.ssl_certificates.append(name)
        return operation

    def delete_ssl_certificate(self, name):
        operation = self.compute.sslCertificates().delete(
            project=self.project,
            sslCertificate=name).execute()
        self.operation.wait_for_global_operation(operation['name'])

        return operation

    def create_https_proxy(self, https_proxy_name, urlmapping_selfLink,
                           certificate_selfLink):
        body = {
            "name": https_proxy_name,
            "urlMap": urlmapping_selfLink,
            "sslCertificates": [
                certificate_selfLink
            ],
            "quicOverride": "NONE",
        }
        operation = self.compute.targetHttpsProxies().insert(
            project=self.project, body=body).execute()
        self.operation.wait_for_global_operation(operation['name'])
        self.target_https_proxies.append(https_proxy_name)
        return operation

    def delete_http_proxy(self, http_proxy_name):
        operation = self.compute.targetHttpProxies().delete(
            project=self.project,
            targetHttpProxy=http_proxy_name).execute()
        self.operation.wait_for_global_operation(operation['name'])
        return operation

    def delete_tcp_proxy(self, tcp_proxy_name):
        operation = self.compute.targetTcpProxies().delete(project=self.project,
                                                           targetTcpProxy=tcp_proxy_name).execute()
        self.operation.wait_for_global_operation(operation['name'])
        return operation

    def delete_ssl_proxy(self, ssl_proxy_name):
        operation = self.compute.targetSslProxies().delete(project=self.project,
                                                           targetSslProxy=ssl_proxy_name).execute()
        self.operation.wait_for_global_operation(operation['name'])
        return operation

    def delete_https_proxy(self, https_proxy_name):
        operation = self.compute.targetHttpsProxies().delete(
            project=self.project,
            targetHttpsProxy=https_proxy_name).execute()
        self.operation.wait_for_global_operation(operation['name'])
        return operation

    def delete_grpc_proxy(self, proxy_name):
        operation = self.compute.targetGrpcProxies().delete(
            project=self.project, targetGrpcProxy=proxy_name
        ).execute()
        self.operation.wait_for_global_operation(operation['name'])
        self.target_grpc_proxies.append(proxy_name)
        return operation

    def create_legacy_network(self, network_name):
        network_body = {
            "name": network_name,
            "IPv4Range": "10.240.0.0/16",
            "routingConfig": {
                "routingMode": "REGIONAL"
            }
        }

        operation = self.compute.networks().insert(project=self.project,
                                                   body=network_body).execute()
        self.operation.wait_for_global_operation(operation['name'])
        self.networks.append(network_name)
        return operation

    def get_network(self, network_name):

        operation = self.compute.networks().get(project=self.project,
                                                network=network_name).execute()
        return operation

    def delete_network(self, network_name):

        operation = self.compute.networks().delete(project=self.project,
                                                   network=network_name).execute()
        self.operation.wait_for_global_operation(operation['name'])
        return operation

    def create_auto_subnetwork(self, network_name):
        network_body = {
            "name": network_name,
            "autoCreateSubnetworks": True,
            "routingConfig": {
                "routingMode": "REGIONAL"
            },
        }
        operation = self.compute.networks().insert(project=self.project,
                                                   body=network_body).execute()
        self.operation.wait_for_global_operation(operation['name'])
        self.networks.append(network_name)
        return operation

    def delete_subnetwork(self, subnetwork_name):
        operation = self.compute.subnetworks().delete(project=self.project,
                                                      region=self.region,
                                                      subnetwork=subnetwork_name).execute()
        self.operation.wait_for_region_operation(operation['name'])
        return operation

    def get_subnetwork(self, subnetwork_name):
        operation = self.compute.subnetworks().get(project=self.project,
                                                   region=self.region,
                                                   subnetwork=subnetwork_name).execute()
        return operation

    def create_non_auto_network(self, network_name):
        network_body = {
            "name": network_name,
            "autoCreateSubnetworks": False,
            "routingConfig": {
                "routingMode": "REGIONAL"
            },
        }

        operation = self.compute.networks().insert(project=self.project,
                                                   body=network_body).execute()
        self.operation.wait_for_global_operation(operation['name'])
        self.networks.append(network_name)
        return operation['targetLink']

    def create_subnetwork(self, subnetwork_name, network_selfLink,
                          subnetwork_ipCidrRange='10.120.0.0/24'):
        subnetwork_body = {
            "name": subnetwork_name,
            "network": network_selfLink,
            "ipCidrRange": subnetwork_ipCidrRange,
            "privateIpGoogleAccess": False,
            "purpose": "PRIVATE"
        }

        operation = self.compute.subnetworks().insert(project=self.project,
                                                      region=self.region,
                                                      body=subnetwork_body).execute()

        self.operation.wait_for_region_operation(operation['name'])
        self.subnetworks.append(subnetwork_name)
        return operation['targetLink']

    def get_project_selfLink(self):
        return self.compute.projects().get(project=self.project).execute()[
            'selfLink']

    def delete_reserved_ips(self, ipv4_address_list):
        address_list = self.compute.addresses().list(project=self.project,
                                                     region=self.region).execute()
        if 'items' not in address_list:
            return
        for address in address_list['items']:
            if address['address'] in ipv4_address_list and address[
                'status'] == 'RESERVED':
                try:
                    operation = self.compute.addresses().delete(
                        project=self.project, region=self.region,
                        address=address['name'])
                    self.operation.wait_for_region_operation(operation['name'])
                except Exception as e:
                    print(str(e))
                    continue

    def clean_all_resources(self):
        # get all the instance templates created during the test
        instance_templates_created_during_migration = []
        for instance_template_name in self.instance_templates:
            instance_templates_created_during_migration.extend(
                self.list_instance_template_names_begin_with_suffix(
                    instance_template_name[:20]))
        self.instance_templates.extend(
            instance_templates_created_during_migration)
        self.instance_templates = list(set(self.instance_templates))
        print('Cleaning all test resources')
        print('Deleting forwarding rules')
        for forwarding_rule in self.regional_forwarding_rules:
            try:
                self.delete_regional_forwarding_rule(forwarding_rule)
            except:
                continue
        for forwarding_rule in self.global_forwarding_rules:
            try:
                self.delete_global_forwarding_rule(forwarding_rule)
            except:
                continue
        print('Deleting backend services')

        for backend_service in self.internal_backend_service:
            try:
                self.delete_internal_backend_service(backend_service)
            except:
                continue
        print('Deleting target proxies')
        for proxy in self.target_http_proxies:
            try:
                self.delete_http_proxy(proxy)
            except Exception as e:
                print('Delete target proxy failed: ', str(e))
                continue
        for proxy in self.target_https_proxies:
            try:
                self.delete_https_proxy(proxy)
            except:
                continue
        for proxy in self.target_tcp_proxies:
            try:
                self.delete_tcp_proxy(proxy)
            except:
                continue

        for proxy in self.target_ssl_proxies:
            try:
                self.delete_ssl_proxy(proxy)
            except:
                continue

        for proxy in self.target_grpc_proxies:
            try:
                self.delete_grpc_proxy(proxy)
            except:
                continue

        print('Deleting url mappings:', self.urlmappings)
        for urlmapping in self.urlmappings:
            try:
                self.delete_urlmapping(urlmapping)
            except Exception as e:
                continue
        print('Deleting external backend services')
        for backend_service in self.external_backend_service:
            try:
                self.delete_external_backend_service(backend_service)
            except Exception as e:
                continue
        print('Deleting regional backend services')
        for backend_service in self.regional_backend_services:
            try:
                self.delete_regional_backend_service(backend_service)
            except Exception as e:
                continue
        print('Deleting global backend services')
        for backend_service in self.global_backend_services:
            try:
                self.delete_global_backend_service(backend_service)
            except Exception as e:
                continue
        print('Deleting target instances')
        for target_instance in self.target_instances:
            try:
                self.delete_target_instance(target_instance)
            except:
                continue
        print('Deleting target pools')
        for target_pool in self.target_pools:
            try:
                self.delete_a_target_pool(target_pool)
            except:
                continue
        print('Deleting auto scalers')
        for autoscaler in self.autoscalers:
            try:
                self.delete_autoscaler(autoscaler)
            except:
                continue
        for region_autoscaler in self.region_autoscalers:
            try:
                self.delete_region_autoscaler(region_autoscaler)
            except:
                continue
        print('Deleting instance groups')
        for unmanged_instance_group in self.unmanaged_instance_groups:
            try:
                self.delete_unmanaged_instance_group(unmanged_instance_group)
            except:
                continue
        for region_managed_instance_group in self.region_managed_instance_groups:
            try:
                self.delete_multi_zone_managed_instance_group_configs(
                    region_managed_instance_group)
            except:
                continue
        for single_zone_managed_instance_group in self.single_zone_managed_instance_groups:
            try:
                self.delete_single_zone_managed_instance_group_configs(
                    single_zone_managed_instance_group)
            except:
                continue
        print('Deleting instances')
        for instance in self.instances:
            try:
                self.delete_instance(instance)
            except:
                continue
        print('Deleting disks')
        for disk in self.disks:
            try:
                self.delete_disk(disk)
            except:
                continue
        print('Deleting instance templates')
        for instance_template in self.instance_templates:
            try:
                self.delete_instance_template(instance_template)
            except:
                continue
        print('Deleting static external IPs')
        for address_name in self.external_addresses:
            try:
                self.delete_address(address_name)
            except:
                continue

        self.delete_reserved_ips(self.possible_reserved_ips)

        print('Deleting health checks')
        for healthcheck in self.healthcheck:
            try:
                self.delete_healthcheck(healthcheck)
            except:
                continue
        print('Clean firewalls')
        for network in self.networks:
            try:
                self.delete_all_firewalls_of_a_target_network(network)
            except:
                continue

        for ssl_certificate in self.ssl_certificates:
            try:
                self.delete_ssl_certificate(ssl_certificate)
            except:
                continue

        print('Deleting subnetworks')

        for network in self.subnetworks:
            try:
                self.delete_all_firewalls_of_a_target_network(network)
                self.delete_subnetwork(network)
            except:
                continue

        print('Deleting networks')
        for network in self.networks:
            try:
                self.delete_all_firewalls_of_a_target_network(network)
                self.delete_network(network)
            except:
                continue
