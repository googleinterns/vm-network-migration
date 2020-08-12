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
import logging
import time
from datetime import datetime

from googleapiclient.http import HttpError
from vm_network_migration.errors import *
from vm_network_migration.handler_helper.selfLink_executor import SelfLinkExecutor
from vm_network_migration.modules.instance_group_modules.unmanaged_instance_group import UnmanagedInstanceGroup
from vm_network_migration.modules.other_modules.operations import Operations
from vm_network_migration.utils import initializer


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
        self.log()
        self.selfLink = self.get_selfLink()
        self.operations = Operations(self.compute, self.project, None,
                                     self.region)
        # The instances which don't belong to any instance groups
        self.attached_single_instances_selfLinks = []
        # The instances which belong to one or more unmanaged instance groups
        self.attached_managed_instance_groups_selfLinks = []
        self.get_attached_backends()

    def log(self):
        logging.basicConfig(filename='backup.log', level=logging.INFO)
        logging.info('-------Target Pool: %s-----' % (self.target_pool_name))
        logging.info(self.target_pool_config)
        logging.info('--------------------------')

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
                    'target pool, and then call the instance group migration '
                    'method instead. After detaching, you can try to migrate '
                    'the instaces of this target pool again.'
                    % (instance_selfLink_list, instance_group_selfLink))

            else:
                target_pool_list = instance_group.get_target_pools(
                    instance_group.original_instance_group_configs)
                if len(target_pool_list) == 1 and self.selfLink == \
                        target_pool_list[0]:

                    self.attached_managed_instance_groups_selfLinks.append(
                        instance_group.selfLink)
                elif self.selfLink not in target_pool_list:
                    raise AmbiguousTargetResource(
                        'The instances %s are within a managed instance group %s, \n'
                        'but this instance group is not serving the target pool. \n'
                        'If you want to migrate this instance group, please \n'
                        'detach these instances from the target pool and then \n'
                        'try out the instance group migration method. \n'
                        'After detaching the instances, you can also try to \n'
                        'migrate the instances of the target pool again. ' % (
                            instance_selfLink_list, instance_group_selfLink)
                    )
                else:
                    raise MultipleTargetPools(
                        "The instance group %s is serving multiple target pools, \n"
                        " please detach it from the other target pools or \n"
                        "backend services and try again." % (
                            instance_group_selfLink))

    def check_backend_health(self, backend_selfLink):
        """ Check if the backend is healthy

        Args:
            backends_selfLink: url selfLink of the backend (just an instance)

        Returns:

        """
        operation = self.compute.targetPools().getHealth(
            project=self.project,
            targetPool=self.target_pool_name,
            body={
                "instance": backend_selfLink
            }).execute()
        if 'healthStatus' not in operation:
            return False
        else:
            for instance_health_status in operation['healthStatus']:
                # If any instance in this backend becomes healthy,
                # this backend will start serving the backend service
                if 'healthState' in instance_health_status and \
                        instance_health_status['healthState'] == 'HEALTHY':
                    return True
        return False


    def wait_for_backend_become_healthy(self, instance_selfLink, TIME_OUT=300):
        """ Wait for backend being healthy

        Args:
            backend_selfLink: url selfLink of the backends (just an instance group)

        Returns:

        """
        start = datetime.now()
        print('Waiting for %s being healthy with time out %s seconds.' % (
            instance_selfLink, TIME_OUT))
        while not self.check_backend_health(instance_selfLink):
            time.sleep(3)
            current_time = datetime.now()
            if (current_time - start).seconds > TIME_OUT:
                print('Health waiting operation is timed out.')
                return
        print('At least one of the instances in %s is healthy.' % (
            instance_selfLink))