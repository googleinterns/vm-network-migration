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
import warnings
from copy import deepcopy

from googleapiclient.http import HttpError
from vm_network_migration.module_helpers.subnet_network_helper import SubnetNetworkHelper
from vm_network_migration.modules.backend_service import BackendService
from vm_network_migration.modules.operations import Operations


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
        self.forwarding_rule_configs = self.get_forwarding_rule_configs()

        self.forwarding_rule_name = self.get_forwarding_rule_name()
        self.operations = Operations(self.compute, self.project, None,
                                     self.region)
        self.network_object = self.build_network_object()
        self.new_backend_service_configs = self.get_new_backend_config_with_new_network_info(
            self.backend_service_configs)
        self.new_forwarding_rule_configs = self.get_new_forwarding_rule_with_new_network_info(
            self.forwarding_rule_configs)

    def get_backend_service_configs(self):
        """ Get the configs of the backend service

        Returns: a deserialized python object of the response

        """
        return self.compute.regionBackendServices().get(
            project=self.project,
            region=self.region,
            backendService=self.backend_service_name).execute()

    def get_forwarding_rule_configs(self):
        """ Get the configs of the forwarding rule which serves this backend service

        Returns: a deserialized python object of the response

        """
        backend_service_selfLink = self.backend_service_configs['selfLink']

        request = self.compute.forwardingRules().list(project=self.project,
                                                      region=self.region)
        while request is not None:
            response = request.execute()
            print('DEBUGGING: BACKEND SELFLINK:', backend_service_selfLink)
            for forwarding_rule in response['items']:
                if 'backendService' in forwarding_rule:
                    print('DEBUGGING TARGET:',
                          forwarding_rule['backendService'])
                if 'backendService' in forwarding_rule and forwarding_rule[
                    'backendService'] == backend_service_selfLink:
                    return forwarding_rule

            request = self.compute.forwardingRules().list_next(
                previous_request=request,
                previous_response=response)
        return None

    def get_forwarding_rule_name(self) -> str:
        """ Get the name of the forwarding rule

        Returns: name

        """
        if self.forwarding_rule_configs != None:
            return self.forwarding_rule_configs['name']

    def build_network_object(self):
        subnetwork_factory = SubnetNetworkHelper(self.compute, self.project,
                                                 None, self.region)
        network_object = subnetwork_factory.generate_network(
            self.network,
            self.subnetwork)
        return network_object

    def get_new_forwarding_rule_with_new_network_info(self,
                                                      forwarding_rule_configs):

        new_forwarding_rule_configs = deepcopy(forwarding_rule_configs)
        new_forwarding_rule_configs[
            'network'] = self.network_object.network_link
        new_forwarding_rule_configs[
            'subnetwork'] = self.network_object.subnetwork_link
        return new_forwarding_rule_configs

    def get_new_backend_config_with_new_network_info(self,
                                                     backend_service_configs):
        new_backend_configs = deepcopy(backend_service_configs)
        new_backend_configs['network'] = self.network_object.network_link
        return new_backend_configs

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
        return insert_backend_service_operation

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
            print('DEBUGGING: BACKEND SELFLINK:', backend_service_selfLink)
            for forwarding_rule in response['items']:
                if 'backendService' in forwarding_rule:
                    print('DEBUGGING TARGET:',
                          forwarding_rule['backendService'])
                if 'backendService' in forwarding_rule and forwarding_rule[
                    'backendService'] == backend_service_selfLink:
                    forwarding_rule_list.append(forwarding_rule)

            request = self.compute.forwardingRules().list_next(
                previous_request=request,
                previous_response=response)
        return forwarding_rule_list

    def has_only_one_forwarding_rules(self) -> bool:
        """ Count the number of forwarding rules connecting this backend service
        to check whether it is only serving a single forwarding rule

        Returns: True or False

        """
        return len(self.get_connecting_forwarding_rule_list()) == 1