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

""" BackendService class: describe a backend service.
"""
from vm_network_migration.utils import initializer


class BackendService(object):

    @initializer
    def __init__(self, compute, project, backend_service_name, network,
                 subnetwork, preserve_instance_external_ip):
        """ Initialization

        Args:
            compute: Google Compute Engine
            project: Project ID
            backend_service_name: name of the backend service
        """

        self.backend_service_configs = None
        self.operations = None
        self.migrated = False

    def get_backend_service_configs(self):
        pass