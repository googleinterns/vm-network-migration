from copy import deepcopy

from vm_network_migration.modules.managed_instance_group import ManagedInstanceGroup
from vm_network_migration.modules.operations import Operations


class SingleZoneManagedInstanceGroup(ManagedInstanceGroup):

    def __init__(self, compute, project, instance_group_name, zone):
        super(SingleZoneManagedInstanceGroup, self).__init__(compute, project,
                                                             instance_group_name)
        self.zone_or_region = zone
        self.operation = Operations(self.compute, self.project, zone, None)
        self.instance_group_manager_api = self.compute.instanceGroupManagers()
        self.autoscaler_api = self.compute.autoscalers()
        self.original_instance_group_configs = self.get_instance_group_configs()
        self.new_instance_group_configs = deepcopy(
            self.original_instance_group_configs)
        self.autoscaler = self.get_autoscaler()
        self.autoscaler_configs = self.get_autoscaler_configs()
