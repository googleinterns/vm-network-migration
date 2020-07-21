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
"""ExternalBackendService class: external backend service, which is used by
TCP/UDP external load balancer or an HTTP external load balancer.
It is always a global compute engine resource.

"""
from copy import deepcopy

from vm_network_migration.modules.backend_service import BackendService
from vm_network_migration.modules.operations import Operations

class ExternalBackendService(BackendService):
    def __init__(self, compute, project, backend_service_name, network,
                 subnetwork, preserve_instance_external_ip):
        """ Initialization

        Args:
            compute: google compute engine
            project: project id
            backend_service_name: name of the backend service
            network: target network
            subnetwork: target subnet
            preserve_instance_external_ip: whether to preserve the external IPs
            of the instances serving the backends
        """
        super(ExternalBackendService, self).__init__(compute, project,
                                                     backend_service_name,
                                                     network, subnetwork,
                                                     preserve_instance_external_ip)
        self.backend_service_api = None
        self.backend_service_configs = self.get_backend_service_configs()
        self.operations = Operations(self.compute, self.project)
        self.preserve_instance_external_ip = preserve_instance_external_ip

    def get_backend_service_configs(self):
        args = {
            'project': self.project,
            'backendService': self.backend_service_name
        }
        return self.compute.backendServices().get(**args).execute()

    def detach_a_backend(self, backend_configs):
        """ Detach a backend from the backend service

        Args:
            backend_configs: the backend to remove

        Returns: a deserialized Python object of the response

        """
        updated_backend_service = deepcopy(self.backend_service_configs)
        updated_backend_service['backends'] = [v for v in
                                               updated_backend_service[
                                                   'backends'] if
                                               v != backend_configs]
        args = {
            'project': self.project,
            'backendService': self.backend_service_name,
            'body': updated_backend_service
        }
        detach_a_backend_operation = self.compute.backendServices().update(
            **args).execute()

        self.operations.wait_for_global_operation(
            detach_a_backend_operation['name'])

        return detach_a_backend_operation

    def reattach_all_backends(self):
        """ Revert the backend service to its original configs.
        If a backend has been detached, after this operation,
        it will be reattached to the backend service.

        Returns: a deserialized python object of the response

        """
        args = {
            'project': self.project,
            'backendService': self.backend_service_name,
            'body': self.backend_service_configs
        }
        revert_backends_operation = self.compute.backendServices().update(
            **args).execute()
        self.operations.wait_for_global_operation(
            revert_backends_operation['name'])

        return revert_backends_operation
