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
""" BackendServiceHelper: helps to create a subclass instance of the BackendService.
"""
from googleapiclient.http import HttpError
from vm_network_migration.modules.external_backend_service import ExternalBackendService
from vm_network_migration.modules.internal_backend_service import InternalBackendService
from vm_network_migration.errors import *


class BackendServiceHelper:
    def __init__(self, compute, project, backend_service_name, network,
                 subnetwork, preserve_instance_external_ip, region=None):
        """ Initialization

        Args:
            compute: Google Compute Engine API
            project: project ID
            backend_service_name: name of the backend service
            network: target network
            subnetwork: target subnet
            preserve_instance_external_ip: whether preserve the external IP
            of the instances which serves this load balancer
            region: region of the internal load balancer
        """
        self.compute = compute
        self.project = project
        self.region = region
        self.backend_service_name = backend_service_name
        self.backend_config = None
        self.network = network
        self.subnetwork = subnetwork
        self.preserve_instance_external_ip = preserve_instance_external_ip

    def build_backend_service(self):
        """ Create a BackendService object

        Returns:

        """
        if self.region == None:
            try:
                self.backend_config = self.get_global_backend_service_config()
            except HttpError as e:
                raise e
            else:
                if self.backend_config['loadBalancingScheme'] == 'EXTERNAL':
                    return ExternalBackendService(self.compute, self.project,
                                                  self.backend_service_name,
                                                  self.network,
                                                  self.subnetwork,
                                                  self.preserve_instance_external_ip)
                else:
                    raise UnsupportedBackendService(
                        'The typeof the backend service is not supported. Migration is terminating.')


        else:
            try:
                self.backend_config = self.get_regional_backend_service_config()
            except HttpError as e:
                raise e
            else:
                if self.backend_config['loadBalancingScheme'] == 'INTERNAL':
                    return InternalBackendService(self.compute, self.project,
                                                  self.backend_service_name,
                                                  self.network,
                                                  self.subnetwork,
                                                  self.preserve_instance_external_ip,
                                                  self.region)
                else:
                    raise UnsupportedBackendService(
                        'The typeof the backend service is not supported. Migration is terminating.')

    def get_regional_backend_service_config(self):
        """ Get the regional backend service configuration

        Returns: configs

        """
        return self.compute.regionBackendServices().get(
            project=self.project,
            region=self.region,
            backendService=self.backend_service_name).execute()

    def get_global_backend_service_config(self):
        """ Get global backend service configs

        Returns: configs

        """
        return self.compute.backendServices().get(
            project=self.project,
            backendService=self.backend_service_name).execute()
