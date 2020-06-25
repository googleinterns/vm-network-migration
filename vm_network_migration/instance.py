from googleapiclient.errors import HttpError
from enum import Enum
from vm_network_migration.errors import *
from vm_network_migration.operations import Operations


class Instance(object):
    def __init__(self, compute, project, name, region, zone,
                 instance_template=None):
        self.compute = compute
        self.name = name
        self.region = region
        self.project = project
        self.zone = zone
        self.instance_template = instance_template
        self.network = None
        self.address = None
        self.operations = Operations(compute, project, zone, region)

    def retrieve_instance_template(self) -> dict:
        """ Get the instance template from an instance.

        Args:
            compute: google API compute engine service
            project: project ID
            zone: zone of the VM
            instance: name of the VM

        Returns:
            instance template

        Raises:
            googleapiclient.errors.HttpError: invalid request
        """
        self.instance_template = self.compute.instances().get(
            project=self.project,
            zone=self.zone,
            instance=self.name).execute()
        return self.instance_template

    def start_instance(self) -> dict:
        """ Start the instance.

        Args:
            compute: google API compute engine service
            project: project ID
            zone: zone of the VM
            instance: name of the VM

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

        Args:
            compute: google API compute engine service
            project: project ID
            zone: zone of the VM
            instance: name of the VM

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

        Args:
            instance_template: a dict of the instance template

        Returns:
            a list of disks' info

        Raises:
            AttributeNotExistError: No disks on the VM
        """
        if 'disks' not in self.instance_template:
            raise AttributeNotExistError('No disks are attached on the VM')
        return self.instance_template['disks']

    def detach_disk(self, disk) -> dict:
        """ Detach a disk from the instance

        Args:
            compute: google API compute engine service
            project: project ID
            zone: zone of the VM
            instance: name of the VM
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
        disks = self.get_disks_info_from_instance_template()
        for diskInfo in disks:
            self.detach_disk(diskInfo['deviceName'])

    def attach_disk(self, disk):
        """Attach a disk to the instance

        Args:
            compute: google API compute engine service
            project: project ID
            zone: zone of the VM
            instance: name of the VM
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
        """Attach a disk to the instance

        Args:
            compute: google API compute engine service
            project: project ID
            zone: zone of the VM
            instance: name of the VM
            disk: deserialized info of the disk

        Returns:
            a deserialized object of the response

        Raises:
            googleapiclient.errors.HttpError: invalid request
        """
        disks = self.get_disks_info_from_instance_template()
        for diskInfo in disks:
            self.attach_disk(diskInfo['deviceName'])

    def modify_instance_template_with_new_name(self, new_name):
        self.instance_template['name'] = new_name
        return self.instance_template

    def modify_instance_template_with_new_network(self, new_network_link,
                                                  new_subnetwork_link) -> dict:
        """ Modify the instance template with the new network interface

            Args:
                instance_template: dictionary of the instance template
                new_instance: name of the new VM
                new_network_info: dictionary of the new network interface

            Returns:
                a dict of the new network interface
        """
        self.instance_template['networkInterfaces'][0][
            'network'] = new_network_link
        self.instance_template['networkInterfaces'][0][
            'subnetwork'] = new_subnetwork_link
        return self.instance_template

    def modify_instance_template_with_external_ip(self, external_ip) -> dict:
        # no unittest
        if external_ip == None:
            if 'accessConfigs' in self.instance_template['networkInterfaces'][
                0]:
                del self.instance_template['networkInterfaces'][0][
                    'accessConfigs']
        else:
            if 'accessConfigs' not in self.instance_template['networkInterfaces'][0]:
                self.instance_template['networkInterfaces'][0]['accessConfigs'] = [{}]
            self.instance_template['networkInterfaces'][0]['accessConfigs'][0][
                'natIP'] = external_ip

        if 'networkIP' in self.instance_template['networkInterfaces'][0]:
            del self.instance_template['networkInterfaces'][0]['networkIP']
        return self.instance_template

    def update_instance_template(self):
        if self.address == None or self.network == None:
            raise AttributeNotExistError('Missing address or network object.')
        self.modify_instance_template_with_new_name(self.name)
        self.modify_instance_template_with_external_ip(self.address.external_ip)
        self.modify_instance_template_with_new_network(
            self.network.network_link, self.network.subnetwork_link)

    def get_instance_status(self):
        try:
            instance_template = self.retrieve_instance_template()
        except HttpError as e:
            error_reason = e._get_reason()
            print(error_reason)
            if "not found" in error_reason:
                return InstanceStatus.NOTEXISTS
            else:
                raise e
        return InstanceStatus(instance_template['status'])

    def create_instance(self) -> dict:
        """ Create the instance using instance template

            Args:
                compute: google API compute engine service
                project: project ID
                zone: zone of the VM
                instance_template: instance template

            Returns:
                a dict of the new network interface

            Raises:
                googleapiclient.errors.HttpError: invalid request
        """
        create_instance_operation = self.compute.instances().insert(
            project=self.project,
            zone=self.zone,
            body=self.instance_template).execute()
        self.operations.wait_for_zone_operation(
            create_instance_operation['name'])
        return create_instance_operation

    def delete_instance(self) -> dict:
        """ delete the instance

            Args:
                compute: google API compute engine service
                project: project ID
                zone: zone of the VM
                instance: name of the instance

            Returns:
                a deserialized object of the response

            Raises:
                googleapiclient.errors.HttpError: invalid request
        """
        delete_instance_operation = self.compute.instances().delete(
            project=self.project,
            zone=self.zone,
            instance=self.name).execute()
        self.operations.wait_for_zone_operation(delete_instance_operation['name'])
        return delete_instance_operation


class InstanceStatus(Enum):
    NOTEXISTS = None
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    TERMINATED = "TERMINATED"
    def __eq__(self, other):
        return self.value == other.value