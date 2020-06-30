from vm_network_migration.modules.instance_group import InstanceGroup, \
    InstanceGroupStatus
from vm_network_migration.modules.instance import Instance
from vm_network_migration.errors import *
from googleapiclient.errors import HttpError
from vm_network_migration.modules.operations import Operations


class UnmanagedInstanceGroup(InstanceGroup):
    def __init__(self, compute, project, instance_group_name, zone):
        """ Initialize an unmanaged instance group object

        Args:
            compute: google compute engine
            project: project name
            instance_group_name: instance group's name
            region: region name of the instance group
            zone: zone name of the instance group
        """
        super(UnmanagedInstanceGroup, self).__init__(compute, project,
                                                     instance_group_name)
        self.zone = zone
        self.instances = self.retrieve_instances()
        self.original_instance_group_configs = self.get_instance_group_configs()
        self.new_instance_group_configs = None
        self.status = self.get_status()
        self.network = None
        self.operation = Operations(self.compute, self.project, self.zone, None)

    def get_instance_group_configs(self):
        """ Get instance group's configurations

        Returns: instance group's configurations

        """
        return self.compute.instanceGroups().get(project=self.project,
                                                 zone=self.zone,
                                                 instanceGroup=self.instance_group_name).execute()

    def retrieve_instances(self):
        """Retrieve all the instances in this instance group,
        and save the instances into a list of Instance objects

        Returns: a list of Instance objects

        """
        instances = []
        request = self.compute.instanceGroups().listInstances(
            project=self.project, zone=self.zone,
            instanceGroup=self.instance_group_name)
        while request is not None:
            response = request.execute()

            for instance_with_named_ports in response['items']:
                print(instance_with_named_ports)
                instance_name = \
                    instance_with_named_ports['instance'].split('instances/')[1]
                instances.append(
                    Instance(self.compute, self.project, instance_name,
                             self.region, self.zone))
            request = self.compute.instanceGroups().listInstances_next(
                previous_request=request, previous_response=response)
        return instances

    def delete_instance_group(self):
        """ Delete the instance group in the compute engine

        Returns:  a deserialized object of the response

        """

        delete_instance_group_operation = self.compute.instanceGroups().delete(
            project=self.project,
            zone=self.zone,
            instanceGroup=self.instance_group_name).execute()
        self.operation.wait_for_zone_operation(delete_instance_group_operation)
        return delete_instance_group_operation

    def create_instance_group(self, configs):
        """ Create the instance group

        Returns: a deserialized object of the response

        """
        create_instance_group_operation = self.compute.instanceGroups().insert(
            project=self.project,
            zone=self.zone,
            body=configs)
        return create_instance_group_operation

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
            if "not found" in error_reason:
                return InstanceGroupStatus.NOTEXISTS
            else:
                raise e
        return InstanceGroupStatus("EXISTS")

    def add_an_instance(self, instance_selfLink):
        """ Add an instance into the instance group

        Args:
            instance_selflink: the instance's selfLink

        Returns:

        """
        add_instance_operation = self.compute.instanceGroups().addInstances(
            project=self.project,
            zone=self.zone,
            InstanceGroup=self.instance_group_name,
            body={"instances":[{"instance": instance_selfLink}]})
        self.operation.wait_for_zone_operation(add_instance_operation)
        return add_instance_operation

    def add_all_instances(self):
        """ Add all the instances in self.instances to the current instance group
        Returns:

        """
        for instance in self.instances:
            try:
                self.add_an_instance(instance.selfLink)
            except HttpError:
                raise AddInstanceToInstanceGroupError(
                    'Failed to add all instances back to the instance group.')

    def modify_instance_group_configs_with_new_network(self, new_network_link,
                                                       new_subnetwork_link,
                                                       instance_group_configs) -> dict:
        """ Modify the instance template with the new network links

            Args:
                new_network_link: the selflink of the network
                new_subnetwork_link: the selflink of the subnetwork

            Returns:
                modified instance template
        """
        instance_group_configs['network'] = new_network_link
        instance_group_configs['subnetwork'] = new_subnetwork_link
        return instance_group_configs

    def update_new_instance_group_configs(self):
        """ Update the new configs with current attributes

        Returns: None

        """
        if self.network == None:
            raise AttributeNotExistError('Missing network object.')
        self.new_instance_group_configs = \
            self.modify_instance_group_configs_with_new_network(
            self.network.network_link, self.network.subnetwork_link,
            self.new_instance_group_configs)
