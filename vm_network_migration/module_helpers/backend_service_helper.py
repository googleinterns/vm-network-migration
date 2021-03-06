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
""" Helper class for creating a BackendService object.
"""
from googleapiclient.http import HttpError
from vm_network_migration.errors import *
from vm_network_migration.modules.backend_service_modules.external_global_backend_service import ExternalBackendService
from vm_network_migration.modules.backend_service_modules.internal_regional_backend_service import InternalBackendService
from vm_network_migration.utils import initializer
from vm_network_migration.modules.backend_service_modules.internal_self_managed_global_backend_service import InternalSelfManagedBackendService


class BackendServiceHelper:
    @initializer
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
            of the instances which serves this backend service
            region: region of the backend service
        """
        self.backend_config = None

    def build_backend_service(self):
        """ Create a BackendService object

        Returns:

        """
        # Try to create a global backend service
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
                elif self.backend_config[
                    'loadBalancingScheme'] == 'INTERNAL_SELF_MANAGED':
                    return InternalSelfManagedBackendService(self.compute,
                                                             self.project,
                                                             self.backend_service_name,
                                                             self.network,
                                                             self.subnetwork,
                                                             self.preserve_instance_external_ip)
                else:
                    raise UnsupportedBackendService(
                        'The typeof the backend service is not supported. Migration is terminating.')

        # try to create a regional backend service (INTERNAL backend service)
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
                        'The backend service with a loadBalancingScheme %s is not supported. Migration is terminating.' % (
                            self.backend_config['loadBalancingScheme']))

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
