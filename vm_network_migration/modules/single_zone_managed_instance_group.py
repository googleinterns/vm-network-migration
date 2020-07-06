from copy import deepcopy

from vm_network_migration.modules.managed_instance_group import ManagedInstanceGroup
from vm_network_migration.modules.operations import Operations


class SingleZoneManagedInstanceGroup(ManagedInstanceGroup):

    def __init__(self, compute, project, instance_group_name, zone):
        super(SingleZoneManagedInstanceGroup, self).__init__(compute, project,
                                                             instance_group_name)
        self.zone = zone
        self.operation = Operations(self.compute, self.project, self.zone, None)
        self.original_instance_group_configs = self.get_instance_group_configs()
        self.new_instance_group_configs = deepcopy(
            self.original_instance_group_configs)

    def get_instance_group_configs(self):

        return self.compute.instanceGroupManagers().get(
            project=self.project,
            zone=self.zone,
            instanceGroupManager=self.instance_group_name).execute()

    def create_instance_group(self, configs):
        create_instance_group_operation = self.compute.instanceGroupManagers().insert(
            project=self.project,
            zone=self.zone,
            body=configs).execute()
        self.operation.wait_for_zone_operation(
            create_instance_group_operation['name'])
        if configs == self.original_instance_group_configs:
            self.migrated = False
        elif configs == self.new_instance_group_configs:
            self.migrated = True

        return create_instance_group_operation

    def delete_instance_group(self):
        delete_instance_group_operation = self.compute.instanceGroupManagers().delete(
            project=self.project,
            zone=self.zone, instanceGroupManager=self.instance_group_name).execute()
        self.operation.wait_for_zone_operation(
            delete_instance_group_operation['name'])
        return delete_instance_group_operation

    def retrieve_instance_template_name(self, instance_zone_configs):
        instance_template_link = instance_zone_configs['instanceTemplate']
        return instance_template_link.split('/')[-1]

    def modify_instance_group_configs_with_instance_template(self,
                                                             instance_group_configs,
                                                             instance_template_link):
        instance_group_configs['instanceTemplate'] = instance_template_link
        instance_group_configs['versions'][0]['instanceTemplate'] = instance_template_link
        return instance_group_configs
