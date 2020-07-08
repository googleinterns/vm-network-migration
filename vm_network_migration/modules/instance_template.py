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
from vm_network_migration.modules.operations import Operations
from vm_network_migration.utils import generate_timestamp_string


class InstanceTemplate:
    def __init__(self, compute, project, instance_template_name,
                 instance_template_body=None):
        """ Initialize an instance template object

        Args:
            compute: google compute engine
            project: project ID
            instance_template_name: name of the instance template
            instance_template_body: a dictionary of the instance template's configs
        """
        self.compute = compute
        self.project = project
        self.instance_template_name = instance_template_name
        self.operation = Operations(self.compute, self.project, None, None)
        self.instance_template_body = instance_template_body
        if self.instance_template_body == None:
            self.instance_template_body = self.get_instance_template_body()

    def get_instance_template_body(self) -> dict:
        """ Get the instance template's configs

        Returns: a deserialized object of the response

        """
        return self.compute.instanceTemplates().get(project=self.project,
                                                    instanceTemplate=self.instance_template_name).execute()

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

    def modify_instance_template_with_new_network(self, new_network_link,
                                                  new_subnetwork_link):
        """ Modify the instance template with the new network links

            Args:
                new_network_link: the selflink of the network
                new_subnetwork_link: the selflink of the subnetwork

        """
        self.instance_template_body['properties']['networkInterfaces'][0][
            'network'] = new_network_link
        self.instance_template_body['properties']['networkInterfaces'][0][
            'subnetwork'] = new_subnetwork_link

    def get_selfLink(self) -> str:
        """ Get the selfLink of the instance template

        Returns: selfLink

        """
        instance_template_body = self.get_instance_template_body()
        return instance_template_body['selfLink']

    def random_change_name(self) -> str:
        """ Change the name of the instance template according to the current timestamp

        Returns: new name
        """
        self.instance_template_name = self.instance_template_name + '-' + generate_timestamp_string()
        self.instance_template_body['name'] = self.instance_template_name
        return self.instance_template_name
