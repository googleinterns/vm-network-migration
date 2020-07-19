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

""" Migrate a external backend service.

"""
import warnings

import google.auth
from googleapiclient import discovery
from vm_network_migration.handlers.external_backend_service_migration import ExternalBackendServiceNetworkMigration
from vm_network_migration.handlers.internal_backend_service_migration import InternalBackendServiceNetworkMigration
from vm_network_migration.module_helpers.backend_service_helper import BackendServiceHelper
from vm_network_migration.modules.backend_service import BackendService
from vm_network_migration.modules.external_backend_service import ExternalBackendService
from vm_network_migration.modules.internal_backend_service import InternalBackendService


class BackendServiceMigration:
    def __init__(self, project, backend_service_name, network, subnetwork,
                 preserve_instance_external_ip, region):
        """ Initialize a BackendServiceMigration object

        Args:
            project: project ID
            backend_service_name: name of the backend service
            network: target network
            subnetwork: target subnet
            preserve_instance_external_ip: whether preserve the external IP
            of the instances which serves this load balancer
            region: region of the internal load balancer
        """
        self.compute = self.set_compute_engine()
        self.project = project
        self.region = region
        self.network = network
        self.subnetwork = subnetwork
        self.backend_service_name = backend_service_name
        self.backend_service_migration_handler = None
        self.preserve_instance_external_ip = preserve_instance_external_ip
        self.backend_service = self.build_backend_service()

    def set_compute_engine(self):
        """ Credential setup

        Returns:google compute engine

        """
        credentials, default_project = google.auth.default()
        return discovery.build('compute', 'v1', credentials=credentials)

    def build_backend_service(self) -> BackendService:
        """ Create a BackendService object.

        Returns: an BackendService object

        """
        backend_service_helper = BackendServiceHelper(
            self.compute,
            self.project,
            self.backend_service_name,
            self.network,
            self.subnetwork,
            self.preserve_instance_external_ip,
            self.region)
        backend_service = backend_service_helper.build_backend_service()
        return backend_service

    def network_migration(self):
        """ Migrate an external backend service's network
        """
        if isinstance(self.backend_service, ExternalBackendService):
            try:
                self.backend_service_migration_handler = ExternalBackendServiceNetworkMigration(
                    self.project, self.backend_service_name, self.network,
                    self.subnetwork,
                    self.preserve_instance_external_ip, self.region,
                    self.backend_service)
                self.backend_service_migration_handler.network_migration()
            except Exception as e:
                warnings.warn(e, Warning)
                print(
                    'The backend service migration was failed. Rolling back to the original instance group.')
                self.backend_service_migration_handler.rollback()

        elif isinstance(self.backend_service, InternalBackendService):
            try:
                self.backend_service_migration_handler = InternalBackendServiceNetworkMigration(
                    self.project, self.backend_service_name, self.network,
                    self.subnetwork,
                    self.preserve_instance_external_ip, self.region,
                    self.backend_service)
            except Exception as e:
                warnings.warn(e, Warning)
                print(
                    'The backend service migration was failed. Rolling back to the original instance group.')
                self.backend_service_migration_handler.rollback()
        else:
            warnings.warn(
                'Unable to find a backend service. Migration was stopped.',
                Warning)
