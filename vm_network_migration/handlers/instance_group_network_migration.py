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

from copy import deepcopy
from warnings import warn

from vm_network_migration.errors import *
from vm_network_migration.handler_helper.selfLink_executor import SelfLinkExecutor
from vm_network_migration.module_helpers.instance_group_helper import InstanceGroupHelper
from vm_network_migration.module_helpers.subnet_network_helper import SubnetNetworkHelper
from vm_network_migration.modules.instance_group_modules.instance_group import InstanceGroupStatus
from vm_network_migration.modules.instance_group_modules.unmanaged_instance_group import UnmanagedInstanceGroup
from vm_network_migration.modules.other_modules.instance_template import InstanceTemplate
from vm_network_migration.utils import initializer
from vm_network_migration.handlers.compute_engine_resource_migration import ComputeEngineResourceMigration


class InstanceGroupNetworkMigration(ComputeEngineResourceMigration):
    @initializer
    def __init__(self, compute, project,
                 network_name,
                 subnetwork_name, preserve_external_ip, zone, region,
                 instance_group_name):
        """ Initialize a InstanceNetworkMigration object

        Args:
            project: project ID
            zone: zone of the instance group
            region:
        """
        super(InstanceGroupNetworkMigration, self).__init__()
        self.instance_group = None
        self.instance_migration_handlers = []
        self.original_instance_template = None
        self.new_instance_template = None

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
                                                    self.zone,
                                                    self.network_name,
                                                    self.subnetwork_name,
                                                    self.preserve_external_ip)
        instance_group = instance_group_helper.build_instance_group()
        return instance_group

    def network_migration(self):
        """ The main method of the instance network migration process

        Args:
            network_name: target network name
            subnetwork_name: target subnetwork name
            preserve_external_ip: preserve the external IP of the instances
            in an unmanaged instance group

        Returns: None

        """
        try:
            if self.instance_group == None:
                self.instance_group = self.build_instance_group()
            if isinstance(self.instance_group, UnmanagedInstanceGroup):
                print('Migrating an unmanaged instance group: %s.' % (
                    self.instance_group_name))
                self.migrate_unmanaged_instance_group()

            else:
                print('Migrating a managed instance group: %s.' % (
                    self.instance_group_name))
                if self.preserve_external_ip:
                    warn(
                        'For a managed instance group, the external IP addresses '
                        'of the instances can not be reserved.', Warning)
                    # continue_execution = input(
                    #     'Do you still want to migrate the instance group? y/n: ')
                    # if continue_execution == 'n':
                    #     return

                if self.instance_group.autoscaler != None:
                    warn(
                        'The autoscaler serving the instance group will be deleted and recreated during the migration',
                        Warning)
                self.migrate_managed_instance_group()

        except Exception as e:
            warn(e, Warning)
            print(
                'The migration was failed. Rolling back to the original network.')
            self.rollback()
            raise MigrationFailed('Rollback has been finished.')

    def migrate_unmanaged_instance_group(self):
        """ Migrate the network of an unmanaged instance group.
        The instances belonging to this instance group will
        be migrated one by one.
        """
        for instance_selfLink in self.instance_group.instance_selfLinks:
            selfLink_executor = SelfLinkExecutor(self.compute,
                                                 instance_selfLink,
                                                 self.network_name,
                                                 self.subnetwork_name,
                                                 self.preserve_external_ip)
            instance_migration_handler = selfLink_executor.build_migration_handler()
            if instance_migration_handler != None:
                self.instance_migration_handlers.append(
                    instance_migration_handler)
                # print('Detaching the instance %s.' %(instance_selfLink))
                # self.instance_group.remove_an_instance(instance_selfLink)
                instance_migration_handler.network_migration(force=True)

        print('Deleting the original instance group: %s.' % (
            self.instance_group_name))
        self.instance_group.delete_instance_group()
        print(
            'Creating a new instance group using the same configuration in the new network.')
        self.instance_group.create_instance_group(
            self.instance_group.new_instance_group_configs)
        print('Adding the instances back to the new instance group: %s.' % (
            self.instance_group_name))
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

        print('Retrieving the instance template of %s.' % (
            self.instance_group_name))
        instance_template_name = self.instance_group.retrieve_instance_template_name(
            self.instance_group.original_instance_group_configs)
        self.original_instance_template = InstanceTemplate(
            self.compute,
            self.project,
            instance_template_name)
        self.new_instance_template = InstanceTemplate(
            self.compute,
            self.project,
            instance_template_name,
            deepcopy(self.original_instance_template.instance_template_body))
        print('Checking the target network information.')
        subnetwork_helper = SubnetNetworkHelper(self.compute,
                                                self.project,
                                                self.zone,
                                                self.region)
        subnet_network = subnetwork_helper.generate_network(self.network_name,
                                                            self.subnetwork_name)
        print(
            'Generating a new instance template to use the target network information.')
        self.new_instance_template.modify_instance_template_with_new_network(
            subnet_network.network_link, subnet_network.subnetwork_link)
        self.new_instance_template.random_change_name()
        print('Inserting the new instance template.')
        self.new_instance_template.insert()
        new_instance_template_link = self.new_instance_template.get_selfLink()
        print(
            'Modifying the instance group configs to use the new instance template')
        self.instance_group.modify_instance_group_configs_with_instance_template(
            self.instance_group.new_instance_group_configs,
            new_instance_template_link)
        # print(self.instance_group.new_instance_group_configs)
        print('Deleting the original instance group: %s.' % (
            self.instance_group_name))
        self.instance_group.delete_instance_group()
        print('Creating the instance group in new network.')
        self.instance_group.create_instance_group(
            self.instance_group.new_instance_group_configs)

    def rollback_unmanaged_instance_group(self):
        """ Rollback an unmanaged instance group

        Returns:

        """
        # The new instance group has been migrated, but the instances are not
        # reattached successfully. The new instance group needs to be deleted.
        # Or just force it to rollback
        if self.instance_group.migrated:
            self.instance_group.delete_instance_group()
        # Some of its instances are running on the new network.
        # These instances should be moved back to the legacy network,
        # and should be added back to the instance group.
        print('Force to rollback all the instances in the group: %s.' % (
            self.instance_group_name))
        for instance_migration_handler in self.instance_migration_handlers:
            instance_migration_handler.rollback()

        instance_group_status = self.instance_group.get_status()
        # The original instance group has been deleted, it needs to be recreated.
        if instance_group_status == InstanceGroupStatus.NOTEXISTS:
            self.instance_group.create_instance_group(
                self.instance_group.original_instance_group_configs)
        print('Adding all instances back to the instance group: %s.' % (
            self.instance_group_name))
        self.instance_group.add_all_instances()

    def rollback_managed_instance_group(self):
        """ Rollback an managed instance group

        """
        instance_group_status = self.instance_group.get_status()
        # Either original instance group or new instance group doesn't exist
        if instance_group_status == InstanceGroupStatus.NOTEXISTS:
            print('Recreating the instance group: %s.' % (
                self.instance_group_name))
            self.instance_group.create_instance_group(
                self.instance_group.original_instance_group_configs
            )
        else:
            # The new instance group has been created
            if self.instance_group.migrated:
                print('Deleting the instance group: %s.' % (
                    self.instance_group_name))
                self.instance_group.delete_instance_group()
                print(
                    'Recreating the instance group with the original configuration')
                self.instance_group.create_instance_group(
                    self.instance_group.original_instance_group_configs
                )
            else:
                # The original autoscaler has been deleted
                if self.instance_group.autoscaler != None and \
                        not self.instance_group.autoscaler_exists():
                    print('Recreating the autoscaler.')
                    self.instance_group.insert_autoscaler()

        if self.new_instance_template != None:
            try:
                self.new_instance_template.delete()
            except:
                return

    def rollback(self):
        """ Rollback to the original instance group

        """
        if self.instance_group == None:
            print('Unable to fetch the instance group: %s.' % (
                self.instance_group_name))
            return
        elif isinstance(self.instance_group, UnmanagedInstanceGroup):
            self.rollback_unmanaged_instance_group()
        else:
            self.rollback_managed_instance_group()
        self.instance_group.migrated = False
