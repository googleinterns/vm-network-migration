from vm_network_migration.modules.load_balancer import LoadBalancer
from vm_network_migration.modules.operations import Operations
from vm_network_migration.migrations.instance_group_network_migration import InstanceGroupNetworkMigration

class InternalLoadBalancer(LoadBalancer):
    def __init__(self, compute, project, backend_service_name, network,
                 subnetwork, preserve_instance_external_ip, region):
        super(InternalLoadBalancer, self).__init__(compute, project,
                                                   backend_service_name,
                                                   network, subnetwork,
                                                   preserve_instance_external_ip)
        self.region = region
        self.backend_service_configs = self.get_backend_service_configs()
        self.forwarding_rule_configs = self.get_forwarding_rule_configs()
        self.forwarding_rule_name = self.get_forwarding_rule_name()
        self.operations = Operations(self.compute, self.project, None,
                                     self.region)
        self.backend_migration_handlers = []

    def get_backend_service_configs(self):
        return self.compute.regionBackendServices().get(project=self.project,
                                                        region=self.region,
                                                        backendService=self.backend_service_name).execute()

    def get_forwarding_rule_configs(self):
        if self.backend_service_configs == None:
            self.backend_service_configs = self.get_backend_service_configs()
        backend_service_selfLink = self.backend_service_configs['selfLink']

        request = self.compute.forwardingRules().list(project=self.project,
                                                      region=self.region)
        while request is not None:
            response = request.execute()

            for forwarding_rule in response['items']:
                if forwarding_rule['target'] == backend_service_selfLink:
                    return forwarding_rule

            request = self.compute.forwardingRules().list_next(
                previous_request=request,
                previous_response=response)
        return None

    def get_forwarding_rule_name(self):
        if self.forwarding_rule_configs == None:
            self.forwarding_rule_configs = self.get_forwarding_rule_configs()
        if self.forwarding_rule_configs != None:
            return self.forwarding_rule_configs['name']

    def delete_forwarding_rule(self):

        delete_forwarding_rule_operation = self.compute.forwardingRules().delete(
            project=self.project,
            region=self.region,
            forwardingRule=self.forwarding_rule_name).execute()
        self.operations.wait_for_region_operation(
            delete_forwarding_rule_operation['name'])
        return delete_forwarding_rule_operation

    def insert_forwarding_rule(self):
        insert_forwarding_rule_operation = self.compute.forwardingRules().insert(
            project=self.project,
            region=self.region,
            forwardingRule=self.forwarding_rule_name).execute()
        self.operations.wait_for_region_operation(
            insert_forwarding_rule_operation['name'])
        return insert_forwarding_rule_operation

    def delete_backend_service(self):
        delete_backend_service_operation = self.compute.regionBackendServices().delete(
            project=self.project,
            region=self.region,
            backendService=self.backend_service_name).execute()
        self.operations.wait_for_region_operation(
            delete_backend_service_operation['name'])
        return delete_backend_service_operation

    def insert_backend_service(self):
        insert_backend_service_operation = self.compute.regionBackendServices().delete(
            project=self.project,
            region=self.region,
            backendService=self.backend_service_name).execute()
        self.operations.wait_for_region_operation(
            insert_backend_service_operation['name'])
        return insert_backend_service_operation

    def migrate_backends(self):
        if 'backends' not in self.backend_service_configs:
            return None
        backends = self.backend_service_configs['backends']
        for backend in backends:
            backend_migration_handler = InstanceGroupNetworkMigration(
                self.project,
                instance_group_selfLink=backend['group'])
            backend_migration_handler.network_migration(
                self.network,
                self.subnetwork,
                self.preserve_instance_external_ip)
            self.backend_migration_handlers.append(backend_migration_handler)
