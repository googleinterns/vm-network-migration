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

""" This script is used to migrate a GCP instance group from its legacy network to a
subnetwork mode network.

Ihe Google API python client module is imported to manage the GCP Compute Engine
 resources.
"""

import re
from copy import deepcopy
from warnings import warn

import google.auth
from googleapiclient import discovery
from googleapiclient.http import HttpError
from vm_network_migration.handlers.instance_network_migration import InstanceNetworkMigration
from vm_network_migration.module_helpers.instance_group_helper import InstanceGroupHelper
from vm_network_migration.module_helpers.subnet_network_helper import SubnetNetworkHelper
from vm_network_migration.modules.instance_group import InstanceGroupStatus
from vm_network_migration.modules.instance_template import InstanceTemplate
from vm_network_migration.modules.unmanaged_instance_group import UnmanagedInstanceGroup


class InstanceGroupNetworkMigration:
    def __init__(self, project,
                 network_name,
                 subnetwork_name, preserve_external_ip, zone, region,
                 instance_group_name):
        """ Initialize a InstanceNetworkMigration object

        Args:
            project: project ID
            zone: zone of the instance group
            region:
        """
        self.compute = self.set_compute_engine()
        self.project = project
        self.network_name = network_name
        self.subnetwork_name = subnetwork_name
        self.preserve_external_ip = preserve_external_ip
        self.zone = zone
        self.region = region
        self.instance_group = None
        self.instance_group_name = instance_group_name

    def build_instance_group(self) -> object:
        """ Create an InstanceGroup object.

        Args:
            instance_group_name: the name of the instance group

        Returns: an InstanceGroup object

        """
        instance_group_helper = InstanceGroupHelper(self.compute,
                                                    self.project,
                                                    self.instance_group_name,
                                                    self.region,
                                                    self.zone)
        instance_group = instance_group_helper.build_instance_group()
        return instance_group

    def set_compute_engine(self):
        """ Credential setup

        Returns:google compute engine

        """
        credentials, default_project = google.auth.default()
        return discovery.build('compute', 'v1', credentials=credentials)

    def network_migration(self):
        """ The main method of the instance network migration process

        Args:
            network_name: target network name
            subnetwork_name: target subnetwork name
            preserve_external_ip: preserve the external IP of the instances
            in an unmanaged instance group

        Returns: None

        """
        if self.instance_group == None:
            self.instance_group = self.build_instance_group()
        if isinstance(self.instance_group, UnmanagedInstanceGroup):
            print('Migrating an unmanaged instance group.')
            try:
                self.migrate_unmanaged_instance_group()
            except Exception as e:
                warn(e, Warning)
                print(
                    'The migration is failed. '
                    'Rolling back to the original instance group.')
                self.rollback_unmanaged_instance_group()

        else:
            print('Migrating a managed instance group.')
            if self.preserve_external_ip:
                warn('For a managed instance group, the external IP addresses '
                     'of the instances can not be reserved.', Warning)
                continue_execution = input(
                    'Do you still want to migrate the instance group? y/n: ')
                if continue_execution == 'n':
                    return

            if self.instance_group.autoscaler != None:
                warn(
                    'The autoscaler serving the instance group will be deleted and recreated during the migration',
                    Warning)
                continue_execution = input(
                    'Do you want to continue the migration? y/n: ')
                if continue_execution == 'n':
                    return

            try:
                self.migrate_managed_instance_group()
            except Exception as e:
                warn(e, Warning)
                print(
                    'The migration is failed. Rolling back to the original instance group.')
                self.rollback_managed_instance_group()

    def migrate_unmanaged_instance_group(self):
        """ Migrate the network of an unmanaged instance group.
        The instances belonging to this instance group will
        be migrated one by one.

        Args:
            network_name: target network
            subnetwork_name: target subnetwork
            preserve_external_ip: whether preserving the external IP
            of the instances in the group

        """
        if self.region == None:
            self.region = self.get_region()
        print('Checking the target network information.')
        subnetwork_factory = SubnetNetworkHelper(self.compute, self.project,
                                                 self.zone, self.region)
        self.instance_group.network = subnetwork_factory.generate_network(
            self.network_name,
            self.subnetwork_name)

        print(
            'Migrating all the instances in the instance group to the new network.')
        for instance in self.instance_group.instances:
            instance_network_migration = InstanceNetworkMigration(self.project,
                                                                  self.zone,
                                                                  instance.name,
                                                                  self.network_name,
                                                                  self.subnetwork_name,
                                                                  self.preserve_external_ip)
            instance_network_migration.instance = instance
            instance_network_migration.network_migration()
        print('Modifying the instance group configs to use the new network.')
        self.instance_group.modify_network_info_in_instance_group_configs(
            self.instance_group.new_instance_group_configs)
        print('Deleting the original instance group.')
        self.instance_group.delete_instance_group()
        print('Creating a new instance group in the new network.')
        self.instance_group.create_instance_group(
            self.instance_group.new_instance_group_configs)
        print('Adding the instances back to the new instance group.')
        self.instance_group.add_all_instances()

    def migrate_managed_instance_group(self):
        """ Migrate the network of a managed instance group.
        The instance group will be recreated with a new
        instance template which has the subnet information.

        Args:
            network_name: target network
            subnetwork_name: target subnetwork

        Returns:

        """
        if self.region == None:
            self.region = self.get_region()

        print('Retrieving the instance template.')
        instance_template_name = self.instance_group.retrieve_instance_template_name(
            self.instance_group.original_instance_group_configs)
        original_instance_template = InstanceTemplate(
            self.compute,
            self.project,
            instance_template_name)
        new_instance_template = InstanceTemplate(
            self.compute,
            self.project,
            instance_template_name,
            deepcopy(original_instance_template.instance_template_body))
        print('Checking the target network information.')
        subnetwork_helper = SubnetNetworkHelper(self.compute,
                                                self.project,
                                                self.zone,
                                                self.region)
        subnet_network = subnetwork_helper.generate_network(self.network_name,
                                                            self.subnetwork_name)
        print('Generating a new instance template.')
        new_instance_template.modify_instance_template_with_new_network(
            subnet_network.network_link, subnet_network.subnetwork_link)
        new_instance_template.random_change_name()
        print('Inserting the new instance template.')
        new_instance_template.insert()
        new_instance_template_link = new_instance_template.get_selfLink()
        print(
            'Modifying the instance group configs to use the new instance template')
        self.instance_group.modify_instance_group_configs_with_instance_template(
            self.instance_group.new_instance_group_configs,
            new_instance_template_link)
        print(self.instance_group.new_instance_group_configs)
        print('Deleting the original instance group.')
        self.instance_group.delete_instance_group()
        print('Creating the instance group in new network.')
        self.instance_group.create_instance_group(
            self.instance_group.new_instance_group_configs)

    def rollback_unmanaged_instance_group(self):
        """ Rollback an unmanaged instance group

        Returns:

        """
        # The new instance group is migrated, but the instances are not
        # reattached successfully. The new instance group needs to be deleted.
        if self.instance_group.migrated:
            self.instance_group.delete_instance_group()
        # Some of its instances are running on the new network.
        # These instances should be moved back to the legacy network,
        # and should be added back to the instance group.
        for instance in self.instance_group.instances:
            if instance.migrated:
                print('Deleting the migrated instance.')
                instance.delete_instance()
                try:
                    print(
                        'Recreating the original instance in the legacy network.')
                    instance.create_instance(
                        instance.original_instance_configs)
                except HttpError as e:
                    error_reason = e._get_reason()
                    if 'not found in region' in error_reason:
                        # the external IP can not be preserved.
                        instance.create_instance_with_ephemeral_external_ip(
                            instance.original_instance_configs)
                    else:
                        raise e
        instance_group_status = self.instance_group.get_status()
        # The original instance group has been deleted, it needs to be recreated.
        if instance_group_status == InstanceGroupStatus.NOTEXISTS:
            self.instance_group.create_instance_group(
                self.instance_group.original_instance_group_configs)
        print('Adding all instances back to the original instance group.')
        self.instance_group.add_all_instances()

    def rollback_managed_instance_group(self):
        """ Rollback an managed instance group

        """
        instance_group_status = self.instance_group.get_status()
        # Either original instance group or new instance group doesn't exist
        if instance_group_status == InstanceGroupStatus.NOTEXISTS:
            print('Recreating the instance group.')
            self.instance_group.create_instance_group(
                self.instance_group.original_instance_group_configs
            )
        else:
            # The new instance group has been created
            if self.instance_group.migrated:
                print('Deleting the instance group.')
                self.instance_group.delete_instance_group()
                print(
                    'Recreating the instance group with the original configuration')
                self.instance_group.create_instance_group(
                    self.instance_group.new_instance_group_configs
                )
            else:
                # The original autoscaler has been deleted
                if self.instance_group.autoscaler != None and \
                        not self.instance_group.autoscaler_exists():
                    print('Recreating the autoscaler.')
                    self.instance_group.insert_autoscaler()

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
