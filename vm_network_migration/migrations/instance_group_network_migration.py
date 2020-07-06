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

""" This script is used to migrate a GCP instance from its legacy network to a
subnetwork mode network.

Ihe Google API python client module is imported to manage the GCP Compute Engine
 resources.

Before running:
    1. If not already done, enable the Compute Engine API
       and check the quota for your project at
       https://console.developers.google.com/apis/api/compute
    2. This sample uses Application Default Credentials for authentication.
       If not already done, install the gcloud CLI from
       https://cloud.google.com/sdk and run
       `gcloud beta auth application-default login`.
       For more information, see
       https://developers.google.com/identity/protocols/application-default-credentials
    3. Install the Python client library for Google APIs by running
       `pip install --upgrade google-api-python-client`

Run the script by terminal, for example:
     python3 vm_network_migration.py --project_id=test-project
     --zone=us-central1-a --original_instance_name=instance-legacy
     --network=tests-network
     --subnetwork=tests-network --preserve_internal_ip=False
     --preserve_external_ip = False --preserve_alias_ip_ranges=False

"""

from copy import deepcopy

import google.auth
from googleapiclient import discovery
from vm_network_migration.migrations.instance_network_migration import InstanceNetworkMigration
from vm_network_migration.modules.instance_group import InstanceGroupStatus
from vm_network_migration.modules.instance_group_helper import InstanceGroupHelper
from vm_network_migration.modules.instance_template import InstanceTemplate
from vm_network_migration.modules.subnet_network import SubnetNetworkHelper
from vm_network_migration.modules.unmanaged_instance_group import UnmanagedInstanceGroup


class InstanceGroupNetworkMigration:
    def __init__(self, project, zone, region):
        """ Initialize a InstanceNetworkMigration object

        Args:
            project: project ID
            zone: zone of the instance
        """
        self.compute = self.set_compute_engine()
        self.project = project
        self.zone = zone
        self.region = region
        self.instance_group = None

    def build_instance_group(self, instance_group_name):
        instance_group_factory = InstanceGroupHelper(self.compute,
                                                     self.project,
                                                     instance_group_name,
                                                     self.region,
                                                     self.zone)
        instance_group = instance_group_factory.build_instance_group()
        return instance_group

    def set_compute_engine(self):
        """ Credential setup

        Returns:google compute engine

        """
        credentials, default_project = google.auth.default()
        return discovery.build('compute', 'v1', credentials=credentials)

    def network_migration(self, instance_group_name,
                          network_name,
                          subnetwork_name, preserve_external_ip):
        """ The main method of the instance network migration process

        Args:
            network_name: target network name
            subnetwork_name: target subnetwork name
            preserve_external_ip: preserve the external IP of the instances
            in an unmanaged instance group

        Returns: None

        """
        if self.instance_group == None:
            self.instance_group = self.build_instance_group(instance_group_name)
        if isinstance(self.instance_group, UnmanagedInstanceGroup):
            self.migrate_unmanaged_instance_group(network_name, subnetwork_name,
                                                  preserve_external_ip)

        else:
            self.migrate_managed_instance_group(network_name,
                                                subnetwork_name)

    def migrate_region_managed_instance_group(self, network_name,
                                              subnetwork_name):
        pass

    def migrate_unmanaged_instance_group(self, network_name, subnetwork_name,
                                         preserve_external_ip):
        if self.region == None:
            self.region = self.get_region()
        subnetwork_factory = SubnetNetworkHelper(self.compute, self.project,
                                                 self.zone, self.region)
        self.instance_group.network = subnetwork_factory.generate_network(
            network_name,
            subnetwork_name)
        instance_network_migration = InstanceNetworkMigration(self.project,
                                                              self.zone)
        print(
            "Migrating all the instances in the instance group to the new network.")
        for instance in self.instance_group.instances:
            instance_network_migration.instance = instance
            instance_network_migration.network_migration(instance.name,
                                                         network_name,
                                                         subnetwork_name,
                                                         preserve_external_ip)
        print("Modifying the instance group's configs with the new network.")
        self.instance_group.update_new_instance_group_configs()
        print("Deleting the original instance group.")
        self.instance_group.delete_instance_group()
        print("Creating a new instance group in the new network.")
        self.instance_group.create_instance_group(
            self.instance_group.new_instance_group_configs)
        print("Adding the instances back to the new instance group")
        self.instance_group.add_all_instances()

    def migrate_managed_instance_group(self, network_name,
                                       subnetwork_name):
        if self.region == None:
            self.region = self.get_region()
        subnetwork_factory = SubnetNetworkHelper(self.compute, self.project,
                                                 self.zone, self.region)
        subnet_network = subnetwork_factory.generate_network(
            network_name,
            subnetwork_name)
        print('Retrieving the instance template.')
        instance_template_name = self.instance_group.retrieve_instance_template_name(
            self.instance_group.original_instance_group_configs)
        original_instance_template = InstanceTemplate(self.compute,
                                                      self.project,
                                                      instance_template_name)
        new_instance_template = InstanceTemplate(self.compute, self.project,
                                                 instance_template_name,
                                                 deepcopy(
                                                     original_instance_template.instance_template_body))
        print('Generating a new instance template.')
        new_instance_template.modify_instance_template_with_new_network(
            subnet_network.network_link, subnet_network.subnetwork_link)
        new_instance_template.random_change_name()
        print('Inserting the new instance template.')
        new_instance_template.insert()
        new_instance_template_link = new_instance_template.get_selfLink()
        print(
            'Modifying the instance group\'s configs with the new instance template')
        self.instance_group.modify_instance_group_configs_with_instance_template(
            self.instance_group.new_instance_group_configs,
            new_instance_template_link)
        print(self.instance_group.new_instance_group_configs)
        print('Deleting the original instance group.')
        self.instance_group.delete_instance_group()
        print('Creating the instance group in new network.')
        self.instance_group.create_instance_group(
            self.instance_group.new_instance_group_configs)

    def rollback_original_instance_group(self):
        """ Roll back to the original VM. Reattach the disks to the
        original instance and restart it.

            Raises:
                googleapiclient.errors.HttpError: invalid request
        """

    def rollback_unmanaged_instance_group(self):
        """ Rollback an unmanaged instance group

        Returns:

        """
        if self.instance_group.migrated:
            self.instance_group.delete_instance_group()
        # Some of its instances are running on the new network.
        # These instances should be moved back to the legacy network,
        # and should be added back to the instance group.
        for instance in self.instance_group.instances:
            if instance.migrated:
                instance.delete_instance()
                instance.create_instance(instance.original_instance_template)
        instance_group_status = self.instance_group.get_status()
        if instance_group_status == InstanceGroupStatus.NOTEXISTS:
            self.instance_group.create_instance_group(
                self.instance_group.original_instance_group_configs)
        self.instance_group.add_all_instances()

    def get_region(self) -> dict:
        """ Get region information

            Returns:
                region name of the self.zone

            Raises:
                googleapiclient.errors.HttpError: invalid request
        """
        return self.compute.zones().get(
            project=self.project,
            zone=self.zone).execute()['region'].split('regions/')[1]
