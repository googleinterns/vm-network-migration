from enum import Enum
from vm_network_migration.modules.operations import Operations
from vm_network_migration.modules.single_zone_managed_instance_group import SingleZoneManagedInstanceGroup
from vm_network_migration.modules.region_managed_instance_group import RegionManagedInstanceGroup
from vm_network_migration.modules.unmanaged_instance_group import UnmanagedInstanceGroup
from googleapiclient.http import HttpError

class InstanceGroup(object):
    def __init__(self, compute, project, instance_group_name):
        self.compute = compute
        self.project = project
        self.instance_group_name = instance_group_name
        self.status = None
        self.operation = None

    def get_status(self):
        pass
    def create_instance_group(self, configs):
        pass
    def get_instance_group_configs(self):
        pass
    def delete_instance_group(self):
        pass


class InstanceGroupFactory:
    def __init__(self, compute, project, instance_group_name, region, zone):
        self.compute = compute
        self.project = project
        self.instance_group_name = instance_group_name
        self.region = region
        self.zone = zone
        self.status = None
        self.operation = Operations(compute, project, zone, region)

    def build_instance_group(self):
        try:
            instance_group_configs = self.get_instance_group_in_zone()
        except HttpError:
            pass
        else:
            if 'Instance Group Manager' not in instance_group_configs:
                #unmanaged instance group
                return UnmanagedInstanceGroup(self.compute, self.project, self.instance_group_name, self.zone)
            else:
                return SingleZoneManagedInstanceGroup(self.compute, self.project, self.instance_group_name, self.zone)
        try:
            self.get_instance_group_in_region()
        except HttpError as e:
            raise e
        else:
            return RegionManagedInstanceGroup(self.compute, self.project, self.instance_group_name, self.region)



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



class InstanceGroupStatus(Enum):
    """
    An Enum class for instance group's status
    """
    NOTEXISTS = None
    EXISTS = "EXISTS"
    def __eq__(self, other):
        """ Override __eq__ function

        Args:
            other: another InstanceGroupStatus object

        Returns: True/False

        """
        return self.value == other.value









