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
""" Instance group class: describe an instance group
    InstanceGroupStatus class: describe an instance group's current status
"""
from enum import Enum

from googleapiclient.http import HttpError
from vm_network_migration.utils import initializer
import logging


class InstanceGroup(object):
    @initializer
    def __init__(self, compute, project, instance_group_name, network_name,
                 subnetwork_name, preserve_instance_ip):
        """ Initialize an instance group.

        Args:
            compute: google compute engine
            project: project ID
            instance_group_name: name of the instance group
        """
        self.original_instance_group_configs = None
        self.new_instance_group_configs = None
        self.status = None
        self.operation = None
        self.selfLink = None

    def log(self):
        """ Log the original configs

        Returns:

        """
        logging.basicConfig(filename='backup.log', level=logging.INFO)
        logging.info(
            '-------Instance Group: %s-----' % (self.instance_group_name))
        logging.info(self.original_instance_group_configs)
        logging.info('--------------------------')

    def get_status(self):
        """ Get the current status of the instance group

        Returns: the instance group's status

        """
        try:
            self.get_instance_group_configs()
        except HttpError as e:
            error_reason = e._get_reason()
            print(error_reason)
            # if instance is not found, it has a NOTEXISTS status
            if 'not found' in error_reason:
                return InstanceGroupStatus.NOTEXISTS
            else:
                raise e
        return InstanceGroupStatus('EXISTS')

    def list_instances(self):
        """ get a list of instances' selfLinks which are in this group

        Returns: a list of selfLinks

        """
        pass

    def get_selfLink(self, config):
        """ Get the selfLink from config

        Args:
            config: config of an instance group

        Returns: url string

        """
        if 'selfLink' in config:
            return config['selfLink']

    def create_instance_group(self, configs):
        """Abstract method: create an instance group using configs

        Args:
            configs: instance group's configurations
        """
        pass

    def get_instance_group_configs(self):
        """ Abstract method: get the instance group's configurations
        """
        pass

    def delete_instance_group(self):
        """ Abstract method: delete the instance group
        """
        pass

    def compare_original_network_and_target_network(self):
        return False


class InstanceGroupStatus(Enum):
    """
    An Enum class for instance group's status
    """
    NOTEXISTS = None
    EXISTS = 'EXISTS'

    def __eq__(self, other):
        """ Override __eq__ function

        Args:
            other: another InstanceGroupStatus object

        Returns: True/False

        """
        return self.value == other.value
