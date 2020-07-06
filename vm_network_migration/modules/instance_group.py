from enum import Enum

from googleapiclient.http import HttpError



class InstanceGroup:
    def __init__(self, compute, project, instance_group_name):
        self.compute = compute
        self.project = project
        self.instance_group_name = instance_group_name
        self.original_instance_group_configs = None
        self.new_instance_group_configs = None
        self.status = None
        self.operation = None
        self.migrated = False

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
