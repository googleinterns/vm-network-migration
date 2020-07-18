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
            preserve_instance_external_ip: whether preserve the external IP
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

            for forwarding_rule in response['items']:
                if forwarding_rule['target'] == backend_service_selfLink:
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

    def insert_forwarding_rule(self):
        """ Insert the forwarding rule

             Returns: a deserialized python object of the response

        """
        insert_forwarding_rule_operation = self.compute.forwardingRules().insert(
            project=self.project,
            region=self.region,
            forwardingRule=self.forwarding_rule_name).execute()
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

    def insert_backend_service(self):
        """ Insert the backend service

             Returns: a deserialized python object of the response

        """
        insert_backend_service_operation = self.compute.regionBackendServices(
        ).delete(
            project=self.project,
            region=self.region,
            backendService=self.backend_service_name).execute()
        self.operations.wait_for_region_operation(
            insert_backend_service_operation['name'])
        return insert_backend_service_operation
