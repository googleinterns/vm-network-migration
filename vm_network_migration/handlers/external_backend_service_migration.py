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

""" This script is used to migrate an external backend service
from its legacy network to a subnetwork mode network.

"""
import warnings

import google.auth
from googleapiclient import discovery
from vm_network_migration.handler_helper.selfLink_executor import SelfLinkExecutor
from vm_network_migration.modules.external_backend_service import \
    ExternalBackendService


class ExternalBackendServiceNetworkMigration:
    def __init__(self, project, backend_service_name, network, subnetwork,
                 preserve_instance_external_ip, region, backend_service):
        """ Initialize a InstanceNetworkMigration object

        Args:
            project: project ID
            backend_service_name: name of the backend service
            network: target network
            subnetwork: target subnet
            preserve_instance_external_ip: whether preserve the external IP
            of the instances which serves this load balancer
            region: region of the internal load balancer
            backend_service: an InternalBackEndService object
        """
        self.compute = self.set_compute_engine()
        self.project = project
        self.region = region
        self.network = network
        self.subnetwork = subnetwork
        self.backend_service_name = backend_service_name
        self.backend_migration_handlers = []
        self.preserve_instance_external_ip = preserve_instance_external_ip
        self.backend_service = backend_service
        if backend_service == None:
            self.backend_service = ExternalBackendService(self.compute,
                                                          self.project,
                                                          self.backend_service_name,
                                                          self.network,
                                                          self.subnetwork,
                                                          self.preserve_instance_external_ip)

    def set_compute_engine(self):
        """ Credential setup

        Returns:google compute engine

        """
        credentials, default_project = google.auth.default()
        return discovery.build('compute', 'v1', credentials=credentials)

    def migrate_backends(self):
        """ Migrate the backends of the backend service one by one
        without deleting or recreating the backend service

        Args:
            backend_service_configs: the configs of the backend service

        """

        if 'backends' not in self.backend_service.backend_service_configs:
            return None
        backends = self.backend_service.backend_service_configs['backends']
        for backend in backends:
            migration_helper = SelfLinkExecutor(backend['group'], self.network,
                                               self.subnetwork,
                                               self.preserve_instance_external_ip)
            backend_migration_handler = migration_helper.build_instance_group_migration_handler()
            # The backend type is not an instance group, then just ignore
            if backend_migration_handler == None:
                continue
            self.backend_migration_handlers.append(backend_migration_handler)
            self.backend_service.detach_a_backend(backend)
            backend_migration_handler.network_migration()
            self.backend_service.reattach_all_backends()

    def network_migration(self):
        """ Migrate the network of an external backend service.
        """
        try:
            self.migrate_backends()
            self.backend_service.migrated = True
        except Exception as e:
            warnings.warn(e, Warning)
            print(
                'The backend service migration was failed. Rolling back all the backends to its original network.')
            self.rollback()
            raise e

    def rollback(self, force=False):
        # Rollback the instance group backends one by one
        for backend_migration_handler in self.backend_migration_handlers:
            backend_migration_handler.rollback()
        self.backend_service.migrated = False