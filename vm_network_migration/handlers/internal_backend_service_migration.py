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

""" This script is used to migrate an internal backend service
from its legacy network to a subnetwork mode network.

"""
import warnings

import google.auth
from googleapiclient import discovery
from vm_network_migration.errors import *
from vm_network_migration.handler_helper.selfLink_executor import SelfLinkExecutor
from vm_network_migration.modules.internal_backend_service import \
    InternalBackendService


class InternalBackendServiceNetworkMigration:
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
            self.backend_service = InternalBackendService(self.compute,
                                                          self.project,
                                                          self.backend_service_name,
                                                          self.network,
                                                          self.subnetwork,
                                                          self.preserve_instance_external_ip,
                                                          self.region)

    def set_compute_engine(self):
        """ Credential setup

        Returns:google compute engine

        """
        credentials, default_project = google.auth.default()
        return discovery.build('compute', 'v1', credentials=credentials)

    def migrate_backends(self):
        """ Migrate the backends of the backend service one by one

        Args:
            backend_service_configs: the configs of the backend service

        """
        if 'backends' not in self.backend_service.backend_service_configs:
            return None
        backends = self.backend_service.backend_service_configs['backends']
        for backend in backends:
            selfLink_executor = SelfLinkExecutor(backend['group'], self.network,
                                                 self.subnetwork,
                                                 self.preserve_instance_external_ip)
            backend_migration_handler = selfLink_executor.build_instance_group_migration_handler()
            backend_migration_handler.network_migration()
            self.backend_migration_handlers.append(backend_migration_handler)

    def network_migration(self):
        """ Migrate the network of an internal backend service.
        If there is a forwarding rule serving the backend service,
        the forwarding rule needs to be deleted and recreated.
        """

        count_forwarding_rules = self.backend_service.count_forwarding_rules()
        if count_forwarding_rules == 1:
            print(
                'The backend service is in use by one forwarding rules. Please try to use forwarding rule migration method.')
        elif count_forwarding_rules > 1:
            print(
                'The backend service is in use by two or more forwarding rules. It cannot be migrated. Terminating.')
        else:
            print('Deleting the backend service.')
            self.backend_service.delete_backend_service()
            print('Migrating the backends one by one.')
            self.migrate_backends()
            print('Creating the backend service in the target subnet')
            self.backend_service.insert_backend_service(
                self.backend_service.new_backend_service_configs)

    def rollback(self):
        """ Rollback

        Returns:

        """
        if self.backend_service.check_backend_service_exists():
            if self.backend_service.migrated:
                print('Deleting the new backend service')
                self.backend_service.delete_backend_service()
            else:
                # The original backend service wasn't deleted.
                # Therefore, the migration never started.
                return
        print('Rolling back the backends to the original network ')
        for backend_migration_handler in self.backend_migration_handlers:
            backend_migration_handler.rollback()
        print('Recreating the backend service with the original configuration')
        self.backend_service.insert_backend_service(
            self.backend_service.backend_service_configs)
