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
""" Helper class is used to decide which subclass
    of InstanceGroup should be initialized.
"""
from vm_network_migration.modules.region_managed_instance_group import RegionManagedInstanceGroup
from vm_network_migration.modules.single_zone_managed_instance_group import SingleZoneManagedInstanceGroup
from vm_network_migration.modules.unmanaged_instance_group import UnmanagedInstanceGroup
class InstanceGroupHelper:
    def __init__(self, compute, project, instance_group_name, region, zone):
        """ Initialize an instance group helper class

        Args:
            compute: google compute engine
            project: project ID
            instance_group_name: name of the instance group
            region: region of the instance group
            zone: zone of the instance group
        """
        self.compute = compute
        self.project = project
        self.instance_group_name = instance_group_name
        self.region = region
        self.zone = zone
        self.status = None

    def build_instance_group(self):
        """ Initialize a subclass object of the InstanceGroup.

        Returns: a subclass object of the InstanceGroup

        """
        try:
            instance_group_configs = self.get_instance_group_in_zone()
        except Exception:
            # It is not a single zone instance group
            pass
        else:
            if 'Instance Group Manager' not in instance_group_configs['description']:
                print('Migrating an unmanaged instance group.')
                return UnmanagedInstanceGroup(self.compute, self.project,
                                              self.instance_group_name,
                                              self.zone)
            else:
                print('Migrating a single-zone managed instance group.')
                return SingleZoneManagedInstanceGroup(self.compute,
                                                      self.project,
                                                      self.instance_group_name,
                                                      self.zone)
        try:
            self.get_instance_group_in_region()
        except Exception as e:
            raise e
        else:
            print('Migrating a multi-zone managed instance group.')
            return RegionManagedInstanceGroup(self.compute, self.project,
                                              self.instance_group_name,
                                              self.region)

    def get_instance_group_in_zone(self):
        """ Get a single zone instance group's configurations

        Returns: instance group's configurations

        """
        return self.compute.instanceGroups().get(project=self.project,
                                                 zone=self.zone,
                                                 instanceGroup=self.instance_group_name).execute()

    def get_instance_group_in_region(self):
        """ Get multi-zone instance group's configurations

        Returns: instance group's configurations

        """
        return self.compute.regionInstanceGroups().get(project=self.project,
                                                       region=self.region,
                                                       instanceGroup=self.instance_group_name).execute()