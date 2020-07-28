from copy import deepcopy

from vm_network_migration.module_helpers.subnet_network_helper import SubnetNetworkHelper
from vm_network_migration.modules.backend_service_modules.internal_backend_service import InternalBackendService
from vm_network_migration.modules.other_modules.operations import Operations


class RegionalInternalBackendService(InternalBackendService):
    def __init__(self, compute, project, backend_service_name, network,
                 subnetwork, preserve_instance_external_ip, region):
        super(RegionalInternalBackendService, self).__init__(compute, project,
                                                             backend_service_name,
                                                             network,
                                                             subnetwork,
                                                             preserve_instance_external_ip)
        self.region = region
        self.operations = Operations(self.compute, self.project, None,
                                     self.region)
        self.compute_engine_api = self.compute.regionBackendServices()
        self.backend_service_configs = self.get_backend_service_configs()
        self.network_object = self.build_network_object()
        self.new_backend_service_configs =self.get_new_backend_config_with_new_network_info(
            self.backend_service_configs)

    def build_network_object(self):
        """ Build network object

        Returns: SubnetNetwork object

        """

        subnetwork_factory = SubnetNetworkHelper(self.compute, self.project,
                                                 None, self.region)
        network_object = subnetwork_factory.generate_network(
            self.network,
            self.subnetwork)
        return network_object

    def get_new_backend_config_with_new_network_info(self,
                                                     backend_service_configs):
        """ Generate a new backend configs with the new network info

        Args:
            backend_service_configs: configs of the backend service

        Returns:

        """
        new_backend_configs = deepcopy(backend_service_configs)
        new_backend_configs['network'] = self.network_object.network_link
        return new_backend_configs
