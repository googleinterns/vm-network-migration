from vm_network_migration.modules.instance_group import InstanceGroup


class ManagedInstanceGroup(InstanceGroup):

    def __init__(self, compute, project, instance_group_name):
        super(ManagedInstanceGroup, self).__init__(compute, project,
                                                   instance_group_name)
        self.instance_group_manager_api = None
        self.autoscaler_api = None
        self.operation = None
        self.zone_or_region = None
        self.original_instance_group_configs = None
        self.new_instance_group_configs = None
        self.is_multi_zone = False
        self.autoscaler = None
        self.autoscaler_configs = None

    def get_instance_group_configs(self):
        print(self.is_multi_zone)
        args = {
            'project': self.project,
            'instanceGroupManager': self.instance_group_name
        }
        self.add_zone_or_region_into_args(args)
        return self.instance_group_manager_api.get(**args).execute()

    def create_instance_group(self, configs):
        args = {
            'project': self.project,
            'body': configs
        }
        self.add_zone_or_region_into_args(args)

        create_instance_group_operation = self.instance_group_manager_api.insert(
            **args).execute()
        if self.is_multi_zone:
            self.operation.wait_for_region_operation(
                create_instance_group_operation['name'])
        else:
            self.operation.wait_for_zone_operation(
                create_instance_group_operation['name'])
        if configs == self.original_instance_group_configs:
            self.migrated = False
        elif configs == self.new_instance_group_configs:
            self.migrated = True
        if self.autoscaler != None:
            self.insert_autoscaler()
        return create_instance_group_operation

    def delete_instance_group(self):
        if self.autoscaler != None:
            self.delete_autoscaler()
        args = {
            'project': self.project,
            'instanceGroupManager': self.instance_group_name
        }
        self.add_zone_or_region_into_args(args)
        delete_instance_group_operation = self.instance_group_manager_api.delete(
            **args).execute()
        if self.is_multi_zone:
            self.operation.wait_for_region_operation(
                delete_instance_group_operation['name'])
        else:
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
        instance_group_configs['versions'][0][
            'instanceTemplate'] = instance_template_link
        return instance_group_configs

    def add_zone_or_region_into_args(self, args):
        if self.is_multi_zone:
            args['region'] = self.zone_or_region
        else:
            args['zone'] = self.zone_or_region

    def get_autoscaler(self):
        if self.original_instance_group_configs == None:
            self.original_instance_group_configs = self.get_instance_group_configs()
        if 'autoscaler' not in self.original_instance_group_configs['status']:
            return None
        else:
            return \
            self.original_instance_group_configs['status']['autoscaler'].split(
                '/')[-1]

    def get_autoscaler_configs(self):
        if self.autoscaler != None:
            args = {
                'project': self.project,
                'autoscaler': self.autoscaler
            }
            self.add_zone_or_region_into_args(args)
            autoscaler_configs = self.autoscaler_api.get(**args).execute()
            return autoscaler_configs
        return None

    def delete_autoscaler(self):
        args = {
            'project': self.project,
            'autoscaler': self.autoscaler
        }
        self.add_zone_or_region_into_args(args)

        delete_autoscaler_operation = self.autoscaler_api.delete(
            **args).execute()
        if self.is_multi_zone:
            self.operation.wait_for_region_operation(
                delete_autoscaler_operation['name'])
        else:
            self.operation.wait_for_zone_operation(
                delete_autoscaler_operation['name'])
        return delete_autoscaler_operation

    def insert_autoscaler(self):
        args = {
            'project': self.project,
            'body': self.autoscaler_configs
        }
        self.add_zone_or_region_into_args(args)
        insert_autoscaler_operation = self.autoscaler_api.insert(
            **args).execute()
        if self.is_multi_zone:
            self.operation.wait_for_region_operation(
                insert_autoscaler_operation['name'])
        else:
            self.operation.wait_for_zone_operation(
                insert_autoscaler_operation['name'])
        return insert_autoscaler_operation