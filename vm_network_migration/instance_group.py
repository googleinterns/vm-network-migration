from enum import Enum
from vm_network_migration.operations import Operations
class InstanceGroup(object):
    def __init__(self, compute, project, instance_group_name, region, zone):
        self.compute = compute
        self.project = project
        self.instance_group_name = instance_group_name
        self.region = region
        self.zone = zone
        self.status = None
        self.operation = Operations(compute, project, zone, region)

    def get_status(self):
        pass
    def create_instance_group(self, configs):
        pass
    def get_instance_group_configs(self):
        pass
    def delete_instance_group(self):
        pass

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









