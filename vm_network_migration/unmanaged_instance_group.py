from vm_network_migration.instance_group import InstanceGroup

class UnmanagedInstanceGroup(InstanceGroup):
    def __init__(self, compute, project, instance_group_name, region, zone):
        super(UnmanagedInstanceGroup, self).__init__(compute, project, instance_group_name, region, zone)
        self.instances = []

    def list_instances(self):
        """List all the instances in this instance group

        Returns:

        """

        request = self.compute.instanceGroups().get(project=self.project, zone=self.zone,
                                               instanceGroup=self.instance_group_name)
        response = request.execute()

