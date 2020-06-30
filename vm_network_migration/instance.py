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
""" Instance class: describe an instance
    InstanceStatus class: describe an instance's current status
"""
from enum import Enum
from copy import deepcopy
from googleapiclient.errors import HttpError
from vm_network_migration.errors import *
from vm_network_migration.operations import Operations


class Instance(object):
    def __init__(self, compute, project, name, region, zone,
                 instance_template=None, status=None):
        """ Initialize an instance object

        Args:
            compute: google compute engine
            project: project ID
            name: name of the instance
            region: region of the instance
            zone: zone of the instance
            instance_template: the instance template of the instance
            stauts:instance's status
        """
        self.compute = compute
        self.name = name
        self.region = region
        self.project = project
        self.zone = zone
        self.original_instance_template = instance_template
        if self.original_instance_template == None:
            self.original_instance_template = self.retrieve_instance_template()
        self.new_instance_template = deepcopy(self.original_instance_template)
        self.network = None
        self.address = None
        self.operations = Operations(compute, project, zone, region)
        self.status = self.get_instance_status()
        self.selfLink = self.get_selfLink(self.original_instance_template)


    def retrieve_instance_template(self) -> dict:
        """ Get the instance template from an instance.

        Returns:
            instance template of self.instance

        Raises:
            googleapiclient.errors.HttpError: invalid request
        """
        instance_template = self.compute.instances().get(
            project=self.project,
            zone=self.zone,
            instance=self.name).execute()

        return instance_template

    def get_selfLink(self, instance_template):
        if 'selfLink' in instance_template:
            return self.original_instance_template['selfLink']

    def start_instance(self) -> dict:
        """ Start the instance.

        Returns:
            a deserialized object of the response

        Raises:
            googleapiclient.errors.HttpError: invalid request
        """
        start_instance_operation = self.compute.instances().start(
            project=self.project,
            zone=self.zone,
            instance=self.name).execute()
        self.operations.wait_for_zone_operation(
            start_instance_operation['name'])
        return start_instance_operation

    def stop_instance(self) -> dict:
        """ Stop the instance.

        Returns:
            a deserialized object of the response

        Raises:
            googleapiclient.errors.HttpError: invalid request
        """
        stop_instance_operation = self.compute.instances().stop(
            project=self.project,
            zone=self.zone,
            instance=self.name).execute()
        self.operations.wait_for_zone_operation(stop_instance_operation['name'])
        return stop_instance_operation

    def get_disks_info_from_instance_template(self) -> list:
        """ Get disks' info from the instance template.

        Returns:
            a list of disks' info

        Raises:
            AttributeNotExistError: No disks on the VM
        """
        if 'disks' not in self.original_instance_template:
            raise AttributeNotExistError('No disks are attached on the VM')
        return self.original_instance_template['disks']

    def detach_disk(self, disk) -> dict:
        """ Detach a disk from the instance

        Args:
            disk: name of the disk

        Returns:
            a deserialized object of the response

        Raises:
            googleapiclient.errors.HttpError: invalid request
        """

        detach_disk_operation = self.compute.instances().detachDisk(
            project=self.project,
            zone=self.zone,
            instance=self.name,
            deviceName=disk).execute()
        self.operations.wait_for_zone_operation(detach_disk_operation['name'])
        return detach_disk_operation

    def detach_disks(self):
        """ Detach all the disks retrieved from self.instance_template

        Returns: None

        """
        disks = self.get_disks_info_from_instance_template()
        for diskInfo in disks:
            self.detach_disk(diskInfo['deviceName'])

    def attach_disk(self, disk):
        """Attach a disk to the instance

        Args:
            disk: deserialized info of the disk

        Returns:
            a deserialized object of the response

        Raises:
            googleapiclient.errors.HttpError: invalid request
        """
        attach_disk_operation = self.compute.instances().attachDisk(
            project=self.project,
            zone=self.zone,
            instance=self.name,
            forceAttach=True,
            body=disk).execute()
        self.operations.wait_for_zone_operation(attach_disk_operation['name'])
        return attach_disk_operation

    def attach_disks(self):
        """ Attach all the disks retrieved from self.instance_template

        Returns: None
        """
        disks = self.get_disks_info_from_instance_template()
        for diskInfo in disks:
            self.attach_disk(diskInfo['deviceName'])

    def modify_instance_template_with_new_network(self, new_network_link,
                                                  new_subnetwork_link, instance_template) -> dict:
        """ Modify the instance template with the new network links

            Args:
                new_network_link: the selflink of the network
                new_subnetwork_link: the selflink of the subnetwork

            Returns:
                modified instance template
        """
        instance_template['networkInterfaces'][0][
            'network'] = new_network_link
        instance_template['networkInterfaces'][0][
            'subnetwork'] = new_subnetwork_link
        return instance_template

    def modify_instance_template_with_external_ip(self, external_ip, instance_template) -> dict:
        """ Modify the instance template with the given external IP address

        Args:
            external_ip: external IP address, such as "123.213.213.123"

        Returns: modified instance template

        """
        if external_ip == None:
            if 'accessConfigs' in instance_template['networkInterfaces'][
                0]:
                if 'natIP' in instance_template['networkInterfaces'][0]['accessConfigs'][0]:
                    del instance_template['networkInterfaces'][0]['accessConfigs'][0]['natIP']

        else:
            if 'accessConfigs' not in \
                    instance_template['networkInterfaces'][0]:
                instance_template['networkInterfaces'][0][
                    'accessConfigs'] = [{}]
            instance_template['networkInterfaces'][0]['accessConfigs'][0][
                'natIP'] = external_ip

        if 'networkIP' in instance_template['networkInterfaces'][0]:
            del instance_template['networkInterfaces'][0]['networkIP']
        return instance_template

    def update_instance_template(self):
        """ Update the instance template with current attributes

        Returns: None

        """
        if self.address == None or self.network == None:
            raise AttributeNotExistError('Missing address or network object.')
        self.new_instance_template = self.modify_instance_template_with_external_ip(self.address.external_ip, self.new_instance_template)
        self.new_instance_template = self.modify_instance_template_with_new_network(
            self.network.network_link, self.network.subnetwork_link, self.new_instance_template)

    def get_instance_status(self):
        """ Get current instance's status.

        Returns: an InstanceStatus object
        Raises: HttpError for incorrect response

        """
        try:
            instance_template = self.retrieve_instance_template()
        except HttpError as e:
            error_reason = e._get_reason()
            print(error_reason)
            # if instance is not found, it has a NOTEXISTS status
            if "not found" in error_reason:
                return InstanceStatus.NOTEXISTS
            else:
                raise e
        return InstanceStatus(instance_template['status'])

    def create_instance(self, instance_template) -> dict:
        """ Create the instance using self.instance_template

            Returns:
                a deserialized object of the response

            Raises:
                googleapiclient.errors.HttpError: invalid request
        """
        create_instance_operation = self.compute.instances().insert(
            project=self.project,
            zone=self.zone,
            body=instance_template).execute()
        self.operations.wait_for_zone_operation(
            create_instance_operation['name'])
        return create_instance_operation

    def delete_instance(self) -> dict:
        """ Delete the instance

            Returns:
                a deserialized object of the response

            Raises:
                googleapiclient.errors.HttpError: invalid request
        """
        delete_instance_operation = self.compute.instances().delete(
            project=self.project,
            zone=self.zone,
            instance=self.name).execute()
        self.operations.wait_for_zone_operation(
            delete_instance_operation['name'])
        return delete_instance_operation


class InstanceStatus(Enum):
    """
    An Enum class for instance's status
    """
    NOTEXISTS = None
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    TERMINATED = "TERMINATED"

    def __eq__(self, other):
        """ Override __eq__ function

        Args:
            other: another InstanceStatus object

        Returns: True/False

        """
        return self.value == other.value
