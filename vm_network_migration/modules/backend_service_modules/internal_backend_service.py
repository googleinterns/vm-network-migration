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

""" InternalBackendService class: internal backend service, which is used by
TCP/UDP internal load balancer. It is always regional.

"""
from copy import deepcopy

from vm_network_migration.module_helpers.subnet_network_helper import SubnetNetworkHelper
from vm_network_migration.modules.backend_service_modules.backend_service import BackendService
from vm_network_migration.modules.other_modules.operations import Operations
from googleapiclient.http import HttpError
import logging


class InternalBackendService(BackendService):
    def __init__(self, compute, project, backend_service_name, network,
                 subnetwork, preserve_instance_external_ip, region):
        """ Initialization

        Args:
            compute: google compute engine
            project: project ID
            backend_service_name: name of the backend service
            network: target network
            subnetwork: target subnet
            preserve_instance_external_ip: whether to preserve the external IP
            region: region of the load balancer
        """
        super(InternalBackendService, self).__init__(compute, project,
                                                     backend_service_name,
                                                     network, subnetwork,
                                                     preserve_instance_external_ip)
        self.region = region
        self.backend_service_configs = self.get_backend_service_configs()
        self.operations = Operations(self.compute, self.project, None,
                                     self.region)
        self.network_object = self.build_network_object()
        self.new_backend_service_configs = self.get_new_backend_config_with_new_network_info(
            self.backend_service_configs)
        self.log()

    def get_backend_service_configs(self):
        """ Get the configs of the backend service

        Returns: a deserialized python object of the response

        """
        return self.compute.regionBackendServices().get(
            project=self.project,
            region=self.region,
            backendService=self.backend_service_name).execute()

    def build_network_object(self):
        """ Build network object

        Returns: SubnetNetwork object

        """
        subnetwork_factory = SubnetNetworkHelper(self.compute, self.project,
                                                 None, self.region)
        network_object = subnetwork_factory.generate_network(
            self.network,
            self.subnetwork)
        return network_object

    def get_new_forwarding_rule_with_new_network_info(self,
                                                      forwarding_rule_configs):
        """ Generate a new forwarding rule with the new network info

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

    def get_new_backend_config_with_new_network_info(self,
                                                     backend_service_configs):
        """ Generate a new backend configs with the new network info

        Args:
            backend_service_configs: configs of the backend service

        Returns:

        """
        new_backend_configs = deepcopy(backend_service_configs)
        new_backend_configs['network'] = self.network_object.network_link
        return new_backend_configs

    def delete_backend_service(self):
        """ Delete the backend service

             Returns: a deserialized python object of the response

        """
        delete_backend_service_operation = self.compute.regionBackendServices(
        ).delete(
            project=self.project,
            region=self.region,
            backendService=self.backend_service_name).execute()
        self.operations.wait_for_region_operation(
            delete_backend_service_operation['name'])
        return delete_backend_service_operation

    def insert_backend_service(self, backend_service_configs):
        """ Insert the backend service

             Returns: a deserialized python object of the response

        """
        insert_backend_service_operation = self.compute.regionBackendServices(
        ).insert(
            project=self.project,
            region=self.region,
            body=backend_service_configs).execute()
        self.operations.wait_for_region_operation(
            insert_backend_service_operation['name'])
        if backend_service_configs == self.new_backend_service_configs:
            self.migrated = True
        else:
            self.migrated = False
        return insert_backend_service_operation

    def check_backend_service_exists(self) -> bool:
        """ Check if the backend service exists in the compute engine

        Returns: True or False

        """
        try:
            self.get_backend_service_configs()
        except HttpError:
            return False
        else:
            return True

    def get_connecting_forwarding_rule_list(self):
        """ Get the configs of the forwarding rule which serves this backend service

        Returns: a deserialized python object of the response

        """
        forwarding_rule_list = []
        backend_service_selfLink = self.backend_service_configs['selfLink']

        request = self.compute.forwardingRules().list(project=self.project,
                                                      region=self.region)
        while request is not None:
            response = request.execute()
            if 'items' not in response:
                break
            for forwarding_rule in response['items']:
                if 'backendService' in forwarding_rule and forwarding_rule[
                    'backendService'] == backend_service_selfLink:
                    forwarding_rule_list.append(forwarding_rule)

            request = self.compute.forwardingRules().list_next(
                previous_request=request,
                previous_response=response)
        return forwarding_rule_list
