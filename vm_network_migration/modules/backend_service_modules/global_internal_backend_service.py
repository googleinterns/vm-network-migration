from copy import deepcopy

from vm_network_migration.modules.backend_service_modules.internal_backend_service import InternalBackendService
from vm_network_migration.modules.other_modules.operations import Operations


class GlobalInternalBackendService(InternalBackendService):
    def __init__(self, compute, project, backend_service_name, network,
                 subnetwork, preserve_instance_external_ip):
        super(GlobalInternalBackendService, self).__init__(compute, project,
                                                           backend_service_name,
                                                           network,
                                                           subnetwork,
                                                           preserve_instance_external_ip)
        self.operations = Operations(self.compute, self.project)
        self.compute_engine_api = self.compute.backendServices()
        self.backend_service_configs = self.get_backend_service_configs()

        self.network_object = None
        self.new_backend_service_configs = deepcopy(
            self.backend_service_configs)
