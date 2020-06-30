from vm_network_migration.instance_group import InstanceGroup

class UnmanagedInstanceGroup(InstanceGroup):
    def __init__(self, compute, project, instance_group_name, region, zone):
        super(UnmanagedInstanceGroup, self).__init__(compute, project, instance_group_name, region, zone)
        self.instances = []

    def get_instance_group_configs(self):
        return self.compute.instanceGroups().get(project=self.project, zone=self.zone,
                                          instanceGroup=self.instance_group_name).execute()
    def list_instances(self):
        """List all the instances in this instance group

        Returns:

        """




