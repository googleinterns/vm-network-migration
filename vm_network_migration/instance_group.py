class InstanceGroup(object):
    def __init__(self, compute, project, instance_group_name, region, zone):
        self.compute = compute
        self.project = project
        self.instance_group_name = instance_group_name
        self.region = region
        self.zone = zone



