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
""" ZonalManagedInstanceGroup: describes a single-zone managed instance group
"""
from copy import deepcopy

from vm_network_migration.modules.instance_group_modules.managed_instance_group import ManagedInstanceGroup
from vm_network_migration.modules.other_modules.operations import Operations


class ZonalManagedInstanceGroup(ManagedInstanceGroup):

    def __init__(self, compute, project, instance_group_name, network_name,
                 subnetwork_name, preserve_instance_ip, zone):
        """ Initialization

        Args:
            compute: google compute engine
            project: project name
            network_name: target network
            subnetwork_name: target subnet
            instance_group_name: instance group's name
            preserve_instance_ip: whether to preserve instances external IPs
            zone: zone name of the instance group
        """
        super(ZonalManagedInstanceGroup, self).__init__(compute, project,
                                                        instance_group_name,
                                                        network_name,
                                                        subnetwork_name,
                                                        preserve_instance_ip)
        self.zone_or_region = zone
        self.operation = Operations(self.compute, self.project, zone, None)
        self.instance_group_manager_api = self.compute.instanceGroupManagers()
        self.autoscaler_api = self.compute.autoscalers()
        self.original_instance_group_configs = self.get_instance_group_configs()
        self.new_instance_group_configs = deepcopy(
            self.original_instance_group_configs)
        self.autoscaler = self.get_autoscaler()
        self.autoscaler_configs = self.get_autoscaler_configs()
        self.selfLink = self.get_selfLink(self.original_instance_group_configs)
        self.log()