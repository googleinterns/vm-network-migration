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

from googleapiclient.http import HttpError
from vm_network_migration.modules.backend_service_modules.backend_service import BackendService


class InternalBackendService(BackendService):
    def __init__(self, compute, project, backend_service_name, network,
                 subnetwork, preserve_instance_external_ip):
        """ Initialization

        Args:
            compute: google compute engine
            project: project ID
            backend_service_name: name of the backend service
            network: target network
            subnetwork: target subnet
            preserve_instance_external_ip: whether to preserve the external IP
        """
        super(InternalBackendService, self).__init__(compute, project,
                                                     backend_service_name,
                                                     network, subnetwork,
                                                     preserve_instance_external_ip)

        self.region = None
        self.operations = None
        self.compute_engine_api = None
        self.backend_service_configs = None
        self.network_object = None
        self.new_backend_service_configs = None

    def add_region_info(self, args):
        if self.region != None:
            args['region'] = self.region

    def get_backend_service_configs(self):
        """ Get the configs of the backend service

        Returns: a deserialized python object of the response

        """
        args = {
            'project': self.project,
            'backendService': self.backend_service_name
        }
        self.add_region_info(args)
        return self.compute_engine_api.get(**args).execute()

    def delete_backend_service(self):
        """ Delete the backend service

             Returns: a deserialized python object of the response

        """
        args = {
            'project': self.project,
            'backendService': self.backend_service_name
        }
        self.add_region_info(args)
        delete_backend_service_operation = self.compute_engine_api.delete(
            **args).execute()
        if self.region == None:
            self.operations.wait_for_global_operation(
                delete_backend_service_operation['name'])
        else:
            self.operations.wait_for_region_operation(
                delete_backend_service_operation['name'])
        return delete_backend_service_operation

    def insert_backend_service(self, backend_service_configs):
        """ Insert the backend service

             Returns: a deserialized python object of the response

        """
        args = {
            'project': self.project,
            'body': backend_service_configs
        }
        self.add_region_info(args)
        insert_backend_service_operation = self.compute_engine_api.insert(
            **args).execute()
        if self.region == None:
            self.operations.wait_for_global_operation(
                insert_backend_service_operation['name'])
        else:
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
        args = {
            'project': self.project,
        }
        self.add_region_info(args)
        if self.region == None:
            forwarding_rule_api = self.compute.forwardingRules()
        else:
            forwarding_rule_api = self.compute.regionForwardingRules()
        request = forwarding_rule_api.list(**args)
        while request is not None:
            response = request.execute()
            for forwarding_rule in response['items']:
                if 'backendService' in forwarding_rule and forwarding_rule[
                    'backendService'] == backend_service_selfLink:
                    forwarding_rule_list.append(forwarding_rule)

            request = forwarding_rule_api.list_next(
                previous_request=request,
                previous_response=response)
        return forwarding_rule_list

    def count_forwarding_rules(self) -> int:
        """ Count the number of forwarding rules connecting this backend service
        to check whether it is only serving a single forwarding rule

        Returns: True or False

        """
        return len(self.get_connecting_forwarding_rule_list())
