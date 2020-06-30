from vm_network_migration.modules.instance_group import InstanceGroup

class ManagedInstanceGroup(InstanceGroup):

    def __init__(self, compute, project, instance_group_name, region):
        super(ManagedInstanceGroup, self).__init__(compute, project, instance_group_name)
        self.region = region
