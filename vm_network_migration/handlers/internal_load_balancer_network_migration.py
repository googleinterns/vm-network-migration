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

""" This script is used to migrate an internal load balancer's backend service
from its legacy network to a subnetwork mode network.

"""
import google.auth
from googleapiclient import discovery
from vm_network_migration.handlers.instance_group_network_migration import \
    InstanceGroupNetworkMigration
from vm_network_migration.modules.internal_load_balancer import \
    InternalLoadBalancer


class InternalLoadBalancerNetworkMigration:
    def __init__(self, project, backend_service_name, network, subnetwork,
                 preserve_instance_external_ip, region):
        """ Initialize a InstanceNetworkMigration object

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
        self.backend_migration_handlers = []
        self.preserve_instance_external_ip = preserve_instance_external_ip
        self.internal_load_balancer = InternalLoadBalancer(self.compute,
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

    def migrate_backends(self, backend_service_configs):
        """ Migrate the backends of the backend service one by one

        Args:
            backend_service_configs: the configs of the backend service

        """
        if 'backends' not in backend_service_configs:
            return None
        backends = backend_service_configs['backends']
        for backend in backends:
            backend_migration_handler = InstanceGroupNetworkMigration(
                self.project,
                instance_group_selfLink=backend['group'])
            backend_migration_handler.network_migration(
                self.network,
                self.subnetwork,
                self.preserve_instance_external_ip)
            self.backend_migration_handlers.append(backend_migration_handler)

    def network_migration(self):
        """ Migrate the network of the load balancer.
        If there is a forwarding rule serving the backend service,
        the forwarding rule needs to be deleted and recreated.
        """

        if self.internal_load_balancer.forwarding_rule_name != None:
            self.internal_load_balancer.delete_forwarding_rule()
        self.internal_load_balancer.delete_backend_service()
        self.migrate_backends(
            self.internal_load_balancer.backend_service_configs)
        self.internal_load_balancer.insert_backend_service()
        if self.internal_load_balancer.forwarding_rule_name != None:
            self.internal_load_balancer.insert_forwarding_rule()
