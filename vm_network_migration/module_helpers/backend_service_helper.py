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
""" BackendServiceHelper: helps to create an BackendService object.
"""
from googleapiclient.http import HttpError
from vm_network_migration.modules.external_backend_service import ExternalBackendService
from vm_network_migration.modules.internal_backend_service import InternalBackendService


class BackendServiceHelper:
    def __init__(self, compute, project, backend_service_name, network,
                 subnetwork, preserve_instance_external_ip, region=None):
        self.compute = compute
        self.project = project
        self.region = region
        self.backend_service_name = backend_service_name
        self.backend_config = None
        self.network = network
        self.subnetwork = subnetwork
        self.preserve_instance_external_ip = preserve_instance_external_ip

    def build_backend_service(self):
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
        return None

    def get_regional_backend_service_config(self):
        return self.compute.regionBackendServices().get(
            project=self.project,
            region=self.region,
            backendService=self.backend_service_name).execute()

    def get_global_backend_service_config(self):
        return self.compute.backendServices().get(
            project=self.project,
            backendService=self.backend_service_name).execute()
