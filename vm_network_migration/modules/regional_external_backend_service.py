from copy import deepcopy

from vm_network_migration.modules.backend_service import BackendService


class RegionalExternalBackendService(BackendService):
    # Can be global or regional
    def __init__(self, compute, project, backend_service_name, network,
                 subnetwork, preserve_instance_external_ip, region):
        super(RegionalExternalBackendService, self).__init__(compute, project,
                                                   backend_service_name,
                                                   network, subnetwork,
                                                   preserve_instance_external_ip)
        self.backend_service_api = None
        self.backend_service_configs = None
        self.operations = None
        self.region = region
        self.backend_service_api = self.compute.regionBackendServices()
        self.preserve_instance_external_ip = preserve_instance_external_ip