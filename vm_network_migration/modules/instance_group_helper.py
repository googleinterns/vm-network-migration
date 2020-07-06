from googleapiclient.http import HttpError
from vm_network_migration.modules.region_managed_instance_group import RegionManagedInstanceGroup
from vm_network_migration.modules.single_zone_managed_instance_group import SingleZoneManagedInstanceGroup
from vm_network_migration.modules.unmanaged_instance_group import UnmanagedInstanceGroup
class InstanceGroupHelper:
    def __init__(self, compute, project, instance_group_name, region, zone):
        self.compute = compute
        self.project = project
        self.instance_group_name = instance_group_name
        self.region = region
        self.zone = zone
        self.status = None

    def build_instance_group(self):
        try:
            instance_group_configs = self.get_instance_group_in_zone()
        except Exception:
            pass
        else:
            if 'Instance Group Manager' not in instance_group_configs['description']:
                # it is an unmanaged instance group
                print('Migrating an unmanaged instance group.')
                return UnmanagedInstanceGroup(self.compute, self.project,
                                              self.instance_group_name,
                                              self.zone)
            else:
                print('Migrating a single-zone managed instance group.')
                return SingleZoneManagedInstanceGroup(self.compute,
                                                      self.project,
                                                      self.instance_group_name,
                                                      self.zone)
        try:
            self.get_instance_group_in_region()
        except Exception as e:
            raise e
        else:
            print('Migrating a multi-zone managed instance group.')
            return RegionManagedInstanceGroup(self.compute, self.project,
                                              self.instance_group_name,
                                              self.region)

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
