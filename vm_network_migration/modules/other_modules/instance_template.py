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

""" InstanceTemplate class: describe an instance template

"""
from copy import deepcopy
from vm_network_migration.modules.other_modules.operations import Operations
from vm_network_migration.utils import *
from vm_network_migration.module_helpers.subnet_network_helper import SubnetNetworkHelper
from vm_network_migration.errors import *

class InstanceTemplate:
    @initializer
    def __init__(self, compute, project, instance_template_name, zone, region,
                 instance_template_body=None, network=None, subnetwork=None):
        """ Initialize an instance template object

        Args:
            compute: google compute engine
            project: project ID
            instance_template_name: name of the instance template
            instance_template_body: a dictionary of the instance template's configs
        """

        self.operation = Operations(self.compute, self.project, None, None)

        if self.instance_template_body == None:
            self.instance_template_body = self.get_instance_template_body()
        self.network_object = None
        if network != None:
            self.network_object = self.get_network()

    def get_instance_template_body(self) -> dict:
        """ Get the instance template's configs

        Returns: a deserialized object of the response

        """
        return self.compute.instanceTemplates().get(project=self.project,
                                                    instanceTemplate=self.instance_template_name).execute()

    def get_network(self):
        """ Generate the network object

        Returns: Network object

        """
        subnetwork_factory = SubnetNetworkHelper(self.compute, self.project,
                                                 self.zone, self.region)
        network = subnetwork_factory.generate_network(
            self.network,
            self.subnetwork)
        return network

    def insert(self) -> dict:
        """ Create the instance template

        Returns: a deserialized object of the response

        """
        insert_operation = self.compute.instanceTemplates().insert(
            project=self.project,
            body=self.instance_template_body).execute()
        self.operation.wait_for_global_operation(insert_operation['name'])
        return insert_operation

    def delete(self) -> dict:
        """ Delete the instance template

        Returns: a deserialized object of the response

        """
        delete_operation = self.compute.instanceTemplates().delete(
            project=self.project,
            instanceTemplate=self.instance_template_name).execute()

        self.operation.wait_for_global_operation(delete_operation['name'])
        return delete_operation

    def modify_instance_template_with_new_network(self, instance_template_body,
                                                  add_network_metadata=True):
        """ Modify the instance template with the new network links

            Args:
                new_network_link: the selflink of the network
                new_subnetwork_link: the selflink of the subnetwork

        """
        instance_template_body['properties']['networkInterfaces'][0][
            'network'] = self.network_object.network_link
        instance_template_body['properties']['networkInterfaces'][0][
            'subnetwork'] = self.network_object.subnetwork_link
        # For testing
        # if add_network_metadata:
        #     if 'items' not in instance_template_body['properties'][
        #         'metadata']:
        #         instance_template_body['properties']['metadata'][
        #             'items'] = []
        #
        #     for item in instance_template_body['properties']['metadata'][
        #         'items']:
        #         if item['key'] == 'network':
        #             item['value'] = self.network_object.subnetwork_link
        #             return
        #
        #     instance_template_body['properties']['metadata'][
        #         'items'].append({
        #         'key': 'network',
        #         'value': self.network_object.subnetwork_link})

    def get_selfLink(self) -> str:
        """ Get the selfLink of the instance template

        Returns: selfLink

        """
        instance_template_body = self.get_instance_template_body()
        return instance_template_body['selfLink']

    def generate_random_name(self) -> str:
        """ Change the name of the instance template according to the current timestamp

        Returns: new name
        """
        new_name = self.instance_template_name[
                   0:25] + '-' + generate_timestamp_string()
        return new_name

    def generating_new_instance_template_using_network_info(self):
        """ Genereate a new InstanceTemplate object using the current network info

        Returns: an InstanceTemplate object

        """
        if self.network_object == None:
            return None
        else:
            new_instance_template_body = deepcopy(self.instance_template_body)
            self.modify_instance_template_with_new_network(
                new_instance_template_body)
            new_instance_template_name = self.generate_random_name()
            new_instance_template_body['name'] = new_instance_template_name
            new_instance_template = InstanceTemplate(self.compute, self.project,
                                                     new_instance_template_name,
                                                     self.zone, self.region,
                                                     new_instance_template_body)
            return new_instance_template

    def compare_original_network_and_target_network(self):
        """ Check if the original network is the
        same as the target subnet
        """
        if self.network_object == None or self.network_object.subnetwork_link == None:
            raise InvalidTargetNetworkError

        if 'subnetwork' not in \
                self.instance_template_body['properties']['networkInterfaces'][
                    0]:
            return False
        elif is_equal_or_contians(
                self.instance_template_body['properties']['networkInterfaces'][
                    0]['subnetwork'],
                self.network_object.subnetwork_link):
            return True
        else:
            return False
