from copy import deepcopy

from vm_network_migration.modules.backend_service import BackendService


class ExternalBackendService(BackendService):
    # Can be global or regional
    def __init__(self, compute, project, backend_service_name, network,
                 subnetwork, preserve_instance_external_ip):
        super(ExternalBackendService, self).__init__(compute, project,
                                                   backend_service_name,
                                                   network, subnetwork,
                                                   preserve_instance_external_ip)
        self.backend_service_api = None
        self.backend_service_configs = None
        self.operations = None
        self.region = None
        self.preserve_instance_external_ip = preserve_instance_external_ip

    def get_backend_service_configs(self):
        args = {
            'project': self.project,
            'backendService': self.backend_service_name
        }
        self.add_region_into_args(args)
        return self.backend_service_api.get(**args).execute()

    def add_region_into_args(self, args):
        if self.region != None:
            args['region'] = self.region

    def detach_a_backend(self, backend_configs):
        updated_backend_service = deepcopy(self.backend_service_configs)
        updated_backend_service['backends'] = [v for v in
                                               updated_backend_service[
                                                   'backends'] if
                                               v != backend_configs]
        args = {
            'project': self.project,
            'backendService': self.backend_service_name,
            'body': updated_backend_service
        }
        self.add_region_into_args(args)
        detach_a_backend_operation = self.backend_service_api.update(
            **args).execute()

        self.operations.wait_for_global_operation(
            detach_a_backend_operation['name'])

        return detach_a_backend_operation

    def revert_backends(self):
        """ Revert the backend service to its original configs.
        If a backend has been detached, after this operation,
        it will be reattached to the backend service.

        Returns: a deserialized python object of the response

        """
        args = {
            'project': self.project,
            'backendService': self.backend_service_name,
            'body': self.backend_service_configs
        }
        self.add_region_into_args(args)
        revert_backends_operation = self.backend_service_api.update(
            **args).execute()
        self.operations.wait_for_global_operation(
            revert_backends_operation['name'])

        return revert_backends_operation
