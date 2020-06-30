from vm_network_migration.modules.managed_instance_group import ManagedInstanceGroup


class RegionManagedInstanceGroup(ManagedInstanceGroup):
    def __init__(self, compute, project, instance_group_name, region):
        super(RegionManagedInstanceGroup, self).__init__(compute, project, instance_group_name, region)
