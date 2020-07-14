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
""" InstanceGroupHelper class helps to create an InstanceGroup object.
"""
from vm_network_migration.modules.regional_managed_instance_group import RegionalManagedInstanceGroup
from vm_network_migration.modules.unmanaged_instance_group import UnmanagedInstanceGroup
from vm_network_migration.modules.zonal_managed_instance_group import ZonalManagedInstanceGroup
import re

class InstanceGroupHelper:
    def __init__(self, compute, project, instance_group_name, region, zone, instance_group_selfLink = None):
        """ Initialize an instance group helper object

        Args:
            compute: google compute engine
            project: project ID
            instance_group_name: name of the instance group
            region: region of the instance group
            zone: zone of the instance group
            instance_group_selfLink: selfLink of the instance group
        """
        self.compute = compute
        self.project = project
        if instance_group_selfLink == None:
            self.instance_group_name = instance_group_name
            self.region = region
            self.zone = zone
            self.status = None
        else:
            zone_match = re.search(r'\/zones\/(.*)\/', instance_group_selfLink)
            if zone_match != None:
                self.zone = zone_match[1]
            region_match = re.search(r'\/regions\/(.*)\/', instance_group_selfLink)
            if region_match != None:
                self.region = region_match[1]
            self.name = instance_group_selfLink.split('/')[-1]


    def build_instance_group(self) -> object:
        """ Initialize a subclass object of the InstanceGroup.

        Returns: a subclass object of the InstanceGroup

        """
        try:
            instance_group_configs = self.get_instance_group_in_zone()
        except Exception:
            # It is not a single zone instance group
            pass
        else:
            if 'Instance Group Manager' not in instance_group_configs[
                'description']:
                print('Migrating an unmanaged instance group.')
                return UnmanagedInstanceGroup(self.compute, self.project,
                                              self.instance_group_name,
                                              self.zone)
            else:
                print('Migrating a single-zone managed instance group.')
                return ZonalManagedInstanceGroup(self.compute,
                                                 self.project,
                                                 self.instance_group_name,
                                                 self.zone)
        try:
            self.get_instance_group_in_region()
        except Exception as e:
            raise e
        else:
            print('Migrating a regional managed instance group.')
            return RegionalManagedInstanceGroup(self.compute, self.project,
                                                self.instance_group_name,
                                                self.region)

    def get_instance_group_in_zone(self) -> dict:
        """ Get a single zone instance group's configurations

        Returns: instance group's configurations

        """
        return self.compute.instanceGroups().get(
            project=self.project,
            zone=self.zone,
            instanceGroup=self.instance_group_name).execute()

    def get_instance_group_in_region(self) -> dict:
        """ Get multi-zone instance group's configurations

        Returns: instance group's configurations

        """
        return self.compute.regionInstanceGroups().get(
            project=self.project,
            region=self.region,
            instanceGroup=self.instance_group_name).execute()
