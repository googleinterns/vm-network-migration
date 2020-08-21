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
"""ExternalGlobalBackendService class: EXTERNAL backend service, which is used by
TCP/UDP EXTERNAL load balancer or an HTTP EXTERNAL load balancer.

"""
from vm_network_migration.modules.backend_service_modules.global_backend_service import GlobalBackendService


class ExternalBackendService(GlobalBackendService):
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
            of the instances serving this backend service
        """
        super(ExternalBackendService, self).__init__(compute, project,
                                                     backend_service_name,
                                                     network, subnetwork,
                                                     preserve_instance_external_ip)
