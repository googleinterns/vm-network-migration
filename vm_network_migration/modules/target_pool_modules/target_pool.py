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
""" TargetPool class: describes a target pool and its API methods

"""
from googleapiclient.http import HttpError
from vm_network_migration.handler_helper.selfLink_executor import SelfLinkExecutor
from vm_network_migration.modules.instance_group_modules.unmanaged_instance_group import UnmanagedInstanceGroup
from vm_network_migration.modules.other_modules.operations import Operations
from vm_network_migration.utils import initializer
from vm_network_migration.errors import *


class TargetPool:
    @initializer
    def __init__(self, compute, project, target_pool_name, region, network,
                 subnetwork, preserve_instance_external_ip):
        """ Initialization

        Args:
            compute: google compute engine
            project: project id
            target_pool_name: name of the target pool
            region: name of the region
            network: target network
            subnetwork: target subnet
            preserve_instance_external_ip: whether to preserve the external IPs
            of the instances serving the backends
        """

        self.target_pool_config = self.get_target_pool_configs()
        self.selfLink = self.get_selfLink()
        self.operations = Operations(self.compute, self.project, None,
                                     self.region)
        # The instances which don't belong to any instance groups
        self.attached_single_instances_selfLinks = []
        # The instances which belong to one or more unmanaged instance groups
        self.attached_managed_instance_groups_selfLinks = []
        self.get_attached_backends()

    def get_target_pool_configs(self):
        """ Get the configs of the target pool

        Returns: a deserialized python object of the response

        """
        return self.compute.targetPools().get(
            project=self.project,
            region=self.region,
            targetPool=self.target_pool_name).execute()

    def get_selfLink(self):
        """ Get the selfLink of the target pool

        Returns: URL string

        """
        if 'selfLink' in self.target_pool_config:
            return self.target_pool_config['selfLink']

    def add_instance(self, instance_selfLink):
        """ Add instance into the backends

        Returns: a deserialized python object of the response

        """
        add_instance_operation = self.compute.targetPools().addInstance(
            project=self.project,
            region=self.region,
            targetPool=self.target_pool_name,
            body={
                'instances': [{
                    'instance': instance_selfLink}]
            }).execute()
        self.operations.wait_for_region_operation(
            add_instance_operation['name'])
        return add_instance_operation

    def get_attached_backends(self):
        """ According to the target pool configs, the attached instances
        can be found. These instances can be a single instance which does
        not belong to any instance group, but they can also belongs to an
        unmanaged instance group or a managed instance group. This function
        can get all these information and store the Instance objects and
        Instance group objects into the attributes.

        """
        instance_group_and_instances = {}
        for instance_selfLink in self.target_pool_config['instances']:
            instance_selfLink_executor = SelfLinkExecutor(self.compute,
                                                          instance_selfLink,
                                                          self.network,
                                                          self.subnetwork,
                                                          self.preserve_instance_external_ip)
            try:
                instance = instance_selfLink_executor.build_an_instance()
                instance_group_selfLinks = instance.get_referrer_selfLinks()
            except HttpError as e:
                error_message = e._get_reason()
                if 'not found' in error_message:
                    continue
                else:
                    raise e
            # No instance group is associated with this instance
            if len(instance_group_selfLinks) == 0:
                self.attached_single_instances_selfLinks.append(
                    instance.selfLink)
            else:
                for selfLink in instance_group_selfLinks:
                    if selfLink in instance_group_and_instances:
                        instance_group_and_instances[selfLink].append(
                            instance.selfLink)
                    else:
                        instance_group_and_instances[selfLink] = [
                            instance.selfLink]

        for instance_group_selfLink, instance_selfLink_list in instance_group_and_instances.items():
            instance_group_selfLink_executor = SelfLinkExecutor(self.compute,
                                                                instance_group_selfLink,
                                                                self.network,
                                                                self.subnetwork,
                                                                self.preserve_instance_external_ip)

            instance_group = instance_group_selfLink_executor.build_an_instance_group()
            if isinstance(instance_group, UnmanagedInstanceGroup):
                raise AmbiguousTargetResource(
                    'The instance %s is within an unmanaged instance group %s. '
                    'If you want to migrate this instance group, you should '
                    'detach this instance or this instance group from the '
                    'target pool through the GCP console, and then call'
                    ' the instance group migration method instead. '
                    'After migrating this unmanaged instance group, '
                    'you can try to migrate this target pool again.'
                    ' Finally, reattach this instance group or the instances '
                    'from this instance group to the migrated target pool.'
                    % (instance_selfLink_list, instance_group_selfLink))

            else:
                target_pool_list = instance_group.get_target_pool(
                    instance_group.original_instance_group_configs)
                if len(target_pool_list) == 1 and self.selfLink == \
                        target_pool_list[0]:

                    self.attached_managed_instance_groups_selfLinks.append(
                        instance_group.selfLink)
                elif self.selfLink not in target_pool_list:
                    raise AmbiguousTargetResource(
                        'The instance %s is within a managed instance group %s, \n'
                        'but this instance group is not serving the target pool. \n'
                        'If you want to migrate this instance group, please \n'
                        'detach the instance %s from the target pool and then \n'
                        'try out the instance group migration method. \n'
                        'After detaching the instance, you can also try to \n'
                        'migrate this target pool again. Finally, you can still \n'
                        'attach any instances or instance groups after migrating \n'
                        ' the target pool. ' % (
                            instance_selfLink_list, instance_group_selfLink,
                            instance_selfLink_list)
                    )
                else:
                    raise MultipleTargetPools(
                        "The instance group %s is serving mutliple target pools, \n"
                        " please detach it from the other target pools or \n"
                        "backend services and try again." % (
                            instance_group_selfLink))
