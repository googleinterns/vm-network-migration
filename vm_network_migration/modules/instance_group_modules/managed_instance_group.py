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
""" ManagedInstanceGroup: describes a managed instance group
"""
from googleapiclient.http import HttpError
from vm_network_migration.modules.instance_group_modules.instance_group import InstanceGroup


class ManagedInstanceGroup(InstanceGroup):

    def __init__(self, compute, project, instance_group_name, network_name,
                 subnetwork_name, preserve_instance_ip):
        """ Initialization

        Args:
            compute: google compute engine
            project: project ID
            instance_group_name: name of the instance group
        """
        super(ManagedInstanceGroup, self).__init__(compute, project,
                                                   instance_group_name,
                                                   network_name,
                                                   subnetwork_name,
                                                   preserve_instance_ip)
        self.instance_group_manager_api = None
        self.autoscaler_api = None
        self.operation = None
        # self.zone_or_region is the region name for a RegionManagedInstanceGroup, and
        # is the zone name for a SingleZoneManagedInstanceGroup
        self.zone_or_region = None
        self.original_instance_group_configs = None
        self.new_instance_group_configs = None
        self.is_multi_zone = False
        self.autoscaler = None
        self.autoscaler_configs = None
        self.selfLink = None

    def get_instance_group_configs(self) -> dict:
        """ Get the configs of the instance group

        Returns: configs

        """
        args = {
            'project': self.project,
            'instanceGroupManager': self.instance_group_name
        }
        self.add_zone_or_region_into_args(args)
        return self.instance_group_manager_api.get(**args).execute()

    def create_instance_group(self, configs) -> dict:
        """ Create an instance group

        Args:
            configs: instance group's configs

        Returns: a deserialized object of the response

        """
        args = {
            'project': self.project,
            'body': configs
        }
        self.add_zone_or_region_into_args(args)

        create_instance_group_operation = self.instance_group_manager_api.insert(
            **args).execute()
        if self.is_multi_zone:
            self.operation.wait_for_region_operation(
                create_instance_group_operation['name'])
        else:
            self.operation.wait_for_zone_operation(
                create_instance_group_operation['name'])
        # If an autoscaler serves the original instance group,
        # it should be recreated
        if self.autoscaler != None and not self.autoscaler_exists():
            self.insert_autoscaler()
        return create_instance_group_operation

    def delete_instance_group(self) -> dict:
        """ Delete an instance group

        Returns: a deserialized object of the response

        """
        if self.autoscaler != None and self.autoscaler_exists():
            self.delete_autoscaler()
        args = {
            'project': self.project,
            'instanceGroupManager': self.instance_group_name
        }
        self.add_zone_or_region_into_args(args)
        delete_instance_group_operation = self.instance_group_manager_api.delete(
            **args).execute()
        if self.is_multi_zone:
            self.operation.wait_for_region_operation(
                delete_instance_group_operation['name'])
        else:
            self.operation.wait_for_zone_operation(
                delete_instance_group_operation['name'])
        return delete_instance_group_operation

    def retrieve_instance_template_name(self, instance_group_configs) -> str:
        """ Get the name of the instance template which is used by
        the instance group

        Args:
            instance_group_configs: configs of the instance group

        Returns: name of the instance template

        """
        instance_template_link = instance_group_configs['instanceTemplate']
        return instance_template_link.split('/')[-1]

    def modify_instance_group_configs_with_instance_template(self,
                                                             instance_group_configs,
                                                             instance_template_link) -> dict:
        """ Modify the instance group with the new instance template link

        Args:
            instance_group_configs: configs of the instance group
            instance_template_link: instance template link

        Returns: modified configs of the instance group

        """
        instance_group_configs['instanceTemplate'] = instance_template_link
        instance_group_configs['versions'][0][
            'instanceTemplate'] = instance_template_link
        return instance_group_configs

    def add_zone_or_region_into_args(self, args):
        """ Add the zone/region key into args.

        Args:
            args: a dictionary object

        """
        if self.is_multi_zone:
            args['region'] = self.zone_or_region
        else:
            args['zone'] = self.zone_or_region

    def get_autoscaler(self):
        """ Get the autoscaler's name which is serving the instance group

        Returns: autoscaler's name if there is an autoscaler

        """
        if self.original_instance_group_configs == None:
            self.original_instance_group_configs = self.get_instance_group_configs()
        if 'autoscaler' not in self.original_instance_group_configs['status']:
            return None
        else:
            return \
                self.original_instance_group_configs['status'][
                    'autoscaler'].split(
                    '/')[-1]

    def get_autoscaler_configs(self):
        """ Get the configs of the instance group's autoscaler

        Returns: configs

        """
        if self.autoscaler != None:
            args = {
                'project': self.project,
                'autoscaler': self.autoscaler
            }
            self.add_zone_or_region_into_args(args)
            autoscaler_configs = self.autoscaler_api.get(**args).execute()
            return autoscaler_configs
        return None

    def autoscaler_exists(self) -> bool:
        """ Check if the autoscaler exists

        Returns: boolean

        """
        try:
            autoscaler_configs = self.get_autoscaler_configs()
        except HttpError:
            return False
        else:
            return autoscaler_configs != None

    def delete_autoscaler(self) -> dict:
        """ Delete the autoscaler

        Returns: a deserialized object of the response

        """
        args = {
            'project': self.project,
            'autoscaler': self.autoscaler
        }
        self.add_zone_or_region_into_args(args)

        delete_autoscaler_operation = self.autoscaler_api.delete(
            **args).execute()
        if self.is_multi_zone:
            self.operation.wait_for_region_operation(
                delete_autoscaler_operation['name'])
        else:
            self.operation.wait_for_zone_operation(
                delete_autoscaler_operation['name'])
        return delete_autoscaler_operation

    def insert_autoscaler(self) -> dict:
        """Create an autoscaler

        Returns: a deserialized object of the response

        """
        args = {
            'project': self.project,
            'body': self.autoscaler_configs
        }
        self.add_zone_or_region_into_args(args)
        insert_autoscaler_operation = self.autoscaler_api.insert(
            **args).execute()
        if self.is_multi_zone:
            self.operation.wait_for_region_operation(
                insert_autoscaler_operation['name'])
        else:
            self.operation.wait_for_zone_operation(
                insert_autoscaler_operation['name'])
        return insert_autoscaler_operation

    def set_target_pool(self, target_pool_selfLink):
        """ Set the target pool of the managed instance group

        Args:
            target_pool_selfLink: selfLink of the target pool

        Returns: a deserialized Python object of the response

        """
        current_target_pools = self.get_target_pools()
        current_target_pools.append(target_pool_selfLink)
        args = {
            'project': self.project,
            'instanceGroupManager': self.instance_group_name,
            'body': {
                'targetPools': current_target_pools
            }
        }
        self.add_zone_or_region_into_args(args)
        set_target_pool_operation = self.instance_group_manager_api.setTargetPools(
            **args).execute()
        if self.is_multi_zone:
            self.operation.wait_for_region_operation(
                set_target_pool_operation['name'])
        else:
            self.operation.wait_for_zone_operation(
                set_target_pool_operation['name'])
        return set_target_pool_operation

    def remove_target_pool(self, target_pool_selfLink):
        """ Remove the target pool of the managed instance group

        Args:
            target_pool_selfLink: selfLink of the target pool

        Returns: a deserialized Python object of the response

        """
        current_target_pools = self.get_target_pools()
        current_target_pools.remove(target_pool_selfLink)
        args = {
            'project': self.project,
            'instanceGroupManager': self.instance_group_name,
            'body': {
                'targetPools': current_target_pools
            }
        }
        self.add_zone_or_region_into_args(args)
        remove_target_pool_operation = self.instance_group_manager_api.setTargetPools(
            **args).execute()
        if self.is_multi_zone:
            self.operation.wait_for_region_operation(
                remove_target_pool_operation['name'])
        else:
            self.operation.wait_for_zone_operation(
                remove_target_pool_operation['name'])
        return remove_target_pool_operation

    def get_target_pools(self):
        """Get a list of target pools served by the instance group"""
        configs = self.get_instance_group_configs()
        if 'targetPools' not in configs:
            return []
        return configs['targetPools']

    def list_instances(self) -> list:
        """ List managed instances' selfLinks

        Returns: a list of instances' selfLinks

        """
        instance_selfLinks = []
        args = {
            'project': self.project,
            'instanceGroupManager': self.instance_group_name,

        }
        self.add_zone_or_region_into_args(args)
        list_instances_operation = self.instance_group_manager_api.listManagedInstances(
            **args).execute()

        for item in list_instances_operation['managedInstances']:
            instance_selfLinks.append(item['instance'])
        return instance_selfLinks
