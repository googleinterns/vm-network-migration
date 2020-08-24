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
""" Helper functions to create test resources.

"""
from vm_network_migration_end_to_end_tests.utils import *


class TestResourceCreator:
    def __init__(self, google_api_interface):
        self.google_api_interface = google_api_interface
        self.legacy_network_name = 'end-to-end-test-legacy-network'
        self.network_name = 'end-to-end-test-vpc-network'
        self.subnetwork_name = 'end-to-end-test-subnet-network'
        try:
            self.legacy_network_selfLink = \
                self.google_api_interface.get_network(self.legacy_network_name)[
                    'selfLink']
        except:
            self.legacy_network_selfLink = \
                self.google_api_interface.create_legacy_network(
                    'end-to-end-test-legacy-network')['targetLink']
        try:
            self.network_selfLink = \
                self.google_api_interface.get_network(self.network_name)[
                    'selfLink']
        except:
            self.network_selfLink = self.google_api_interface.create_non_auto_network(
                self.network_name)
        try:
            self.subnetwork_selfLink = \
                self.google_api_interface.get_subnetwork(self.subnetwork_name)[
                    'selfLink']
        except:
            self.subnetwork_selfLink = self.google_api_interface.create_subnetwork_using_random_ip_range(
                self.subnetwork_name, self.network_selfLink)['targetLink']
            print('Created subnetwork: ', self.subnetwork_selfLink)

        self.legacy_template_name = 'end-to-end-test-legacy-template'
        try:
            self.legacy_instance_template_selfLink = \
                self.google_api_interface.get_instance_template_body(
                    self.legacy_template_name)['selfLink']
        except:
            self.legacy_instance_template_selfLink = \
                self.create_instance_template(
                    'sample_instance_template.json',
                    'end-to-end-test-legacy-template')[
                    'targetLink']

        self.healthcheck_name = 'end-to-end-test-tcp-80-health-check'
        try:
            self.tcp_80_health_check_selfLink = \
                self.google_api_interface.get_healthcheck(
                    self.healthcheck_name)[
                    'selfLink']

        except:
            self.tcp_80_health_check_selfLink = \
                self.create_tcp_80_health_check(self.healthcheck_name)[
                    'targetLink']

    def create_tcp_80_health_check(self, healthcheck_name):

        config = {
            "name": healthcheck_name,
            "description": "",
            "checkIntervalSec": 5,
            "timeoutSec": 5,
            "unhealthyThreshold": 2,
            "healthyThreshold": 2,
            "type": "TCP",
            "tcpHealthCheck": {
                "port": 80,
                "proxyHeader": "NONE"
            },
            "kind": "compute#healthCheck"
        }
        return self.google_api_interface.add_healthcheck(config)

    def create_instance_template(self, instance_template_file,
                                 instance_template_name):
        config = read_json_file(
            instance_template_file)
        config['name'] = instance_template_name
        config['properties']['networkInterfaces'][0][
            'network'] = self.legacy_network_selfLink

        return self.google_api_interface.create_instance_template(config)

    def add_additional_disk_to_instance(self, instance_name, disk_name,
                                        disk_file):
        disk_config = read_json_file(
            disk_file)
        disk_config['name'] = disk_name
        disk_selfLink = self.google_api_interface.create_disk(disk_config)[
            'targetLink']
        self.google_api_interface.attach_disk(instance_name, disk_selfLink)

    def create_instance_using_template(self, instance_name, template_selfLink):
        instance_configs = {
            "name": instance_name
        }
        return self.google_api_interface.create_instance(instance_configs,
                                                         template_selfLink)

    def create_unmanaged_instance_group(self,
                                        unmanaged_instance_group_name,
                                        list_of_instance_names):
        unmanaged_instance_group_configs = {
            "name": unmanaged_instance_group_name,
            "description": ""
        }

        return self.google_api_interface.create_unmanaged_instance_group_with_instances(
            unmanaged_instance_group_configs, list_of_instance_names)

    def create_regional_managed_instance_group(self, instance_template_selfLink,
                                               group_name,
                                               managed_instance_group_file_name,
                                               autoscaler_file_name=None):
        managed_instance_group_configs = read_json_file(
            managed_instance_group_file_name)

        managed_instance_group_configs[
            'instanceTemplate'] = instance_template_selfLink
        managed_instance_group_configs['name'] = group_name
        operation = self.google_api_interface.create_multi_zone_managed_instance_group(
            managed_instance_group_configs)
        instance_group_selfLink = operation['targetLink']
        if autoscaler_file_name != None:
            autoscaler_configs = read_json_file(autoscaler_file_name)
            autoscaler_configs['target'] = instance_group_selfLink
            autoscaler_configs['name'] = group_name
            self.google_api_interface.create_region_autoscaler(
                autoscaler_configs)
        return operation

    def create_target_pool_with_health_check(self, target_pool_file_name,
                                             target_pool_name,
                                             instance_group_name_list,
                                             instance_selfLinks,
                                             health_check_selfLink=None):
        target_pool_configs = read_json_file(target_pool_file_name)
        target_pool_configs['name'] = target_pool_name
        if health_check_selfLink != None:
            target_pool_configs['healthChecks'] = [health_check_selfLink]
        operation = \
            self.google_api_interface.create_target_pool(target_pool_configs)
        target_pool_selfLink = operation['targetLink']
        for regional_instance_group in instance_group_name_list:
            self.google_api_interface.regional_instance_group_set_target_pool(
                regional_instance_group,
                target_pool_selfLink)
        for instance_selfLink in instance_selfLinks:
            self.google_api_interface.add_instances_to_target_pool(
                target_pool_configs[
                    'name'],
                instance_selfLink)
        return operation

    def create_global_backend_service(self, backend_service_file_name,
                                      backend_service_name,
                                      instance_group_selfLinks):
        backend_service_configs = read_json_file(backend_service_file_name)
        backend_service_configs['name'] = backend_service_name
        backend_service_configs['healthChecks'] = [
            self.tcp_80_health_check_selfLink]
        for instance_group_selfLink in instance_group_selfLinks:
            backend_service_configs['backends'].append({
                "description": "",
                "group": instance_group_selfLink,
                "balancingMode": "UTILIZATION",
                "maxUtilization": 0.8,
                "capacityScaler": 1
            })
        return self.google_api_interface.create_global_backend_service(
            backend_service_configs)

    def create_regional_backend_service(self, backend_service_file_name,
                                        backend_service_name,
                                        instance_group_selfLinks):
        backend_service_configs = read_json_file(backend_service_file_name)
        backend_service_configs['name'] = backend_service_name
        backend_service_configs['healthChecks'] = [
            self.tcp_80_health_check_selfLink]
        for instance_group_selfLink in instance_group_selfLinks:
            backend_service_configs['backends'].append({
                "description": "",
                "group": instance_group_selfLink,
                "balancingMode": "CONNECTION"
            })
        backend_service_configs['network'] = self.legacy_network_selfLink
        return self.google_api_interface.create_regional_backend_service(
            backend_service_configs)

    def create_urlmapping(self, url_mapping_name, backend_service_selfLink):
        url_configs = {
            "name": url_mapping_name,
            "defaultService": backend_service_selfLink,
            "kind": "compute#urlMap"
        }
        return self.google_api_interface.create_urlmapping(url_configs)

    def create_urlmapping_using_two_backend_service(self, url_mapping_name,
                                                    backend_service_selfLinks):
        url_configs = {
            "name": url_mapping_name,
            "hostRules": [
                {
                    "hosts": [
                        "www.example.come"
                    ],
                    "pathMatcher": "path-matcher-1"
                }
            ],
            "pathMatchers": [
                {
                    "name": "path-matcher-1",
                    "defaultService": backend_service_selfLinks[1],
                    "pathRules": [
                        {
                            "service": backend_service_selfLinks[1],
                            "paths": [
                                "/test/*"
                            ]
                        }
                    ]
                }
            ],
            "defaultService": backend_service_selfLinks[0],
        }
        return self.google_api_interface.create_urlmapping(url_configs)

    def create_http_target_proxy(self, target_proxy_name, urlmapping_selfLink):
        return self.google_api_interface.create_http_proxy(target_proxy_name,
                                                           urlmapping_selfLink)

    def create_global_forwarding_rule_with_target(self,
                                                  forwarding_rule_file_name,
                                                  forwarding_rule_name,
                                                  target_selfLink,
                                                  network_selfLink=None):
        forwarding_rule_configs = read_json_file(forwarding_rule_file_name)
        forwarding_rule_configs['name'] = forwarding_rule_name
        forwarding_rule_configs['target'] = target_selfLink
        if network_selfLink != None:
            forwarding_rule_configs['network'] = network_selfLink
        return self.google_api_interface.create_global_forwarding_rule(
            forwarding_rule_configs)

    def create_global_forwarding_rule_with_backend_service(self,
                                                           forwarding_rule_file_name,
                                                           forwarding_rule_name,
                                                           backend_service_selfLink):
        forwarding_rule_configs = read_json_file(forwarding_rule_file_name)
        forwarding_rule_configs['name'] = forwarding_rule_name
        forwarding_rule_configs['backendService'] = backend_service_selfLink
        return self.google_api_interface.create_global_forwarding_rule(
            forwarding_rule_configs)

    def create_regional_forwarding_rule_with_target(self,
                                                    forwarding_rule_file_name,
                                                    forwarding_rule_name,
                                                    target_selfLink):
        forwarding_rule_configs = read_json_file(forwarding_rule_file_name)
        forwarding_rule_configs['name'] = forwarding_rule_name
        forwarding_rule_configs['target'] = target_selfLink
        if 'backendService' in forwarding_rule_configs:
            del forwarding_rule_configs['backendService']
        forwarding_rule_configs['network'] = self.legacy_network_selfLink
        return self.google_api_interface.create_regional_forwarding_rule(
            forwarding_rule_configs)

    def create_regional_forwarding_rule_with_backend_service(self,
                                                             forwarding_rule_file_name,
                                                             forwarding_rule_name,
                                                             backend_service_selfLink):
        forwarding_rule_configs = read_json_file(forwarding_rule_file_name)
        forwarding_rule_configs['name'] = forwarding_rule_name
        forwarding_rule_configs['backendService'] = backend_service_selfLink
        forwarding_rule_configs['network'] = self.legacy_network_selfLink
        return self.google_api_interface.create_regional_forwarding_rule(
            forwarding_rule_configs)

    def create_a_target_instance(self, target_instance_name, instance_selfLink):
        target_instance_configs = {
            "name": target_instance_name,
            "description": "",
            "natPolicy": "NO_NAT",
            "instance": instance_selfLink
        }
        return self.google_api_interface.create_target_instance(
            target_instance_configs)
