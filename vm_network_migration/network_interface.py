from vm_network_migration.subnet_network import SubnetNetwork
from vm_network_migration.address import Address

class NetworkInterface:
    def __init__(self, network_interface, compute, project, zone, region, is_legacy, address=None, network=None):
        self.network_interface = network_interface
        self.compute = compute
        self.project = project,
        self.zone = zone,
        self.region = region
        self.address = address
        self.network = network
        self.is_legacy = is_legacy

    # def generate_address(self):
    #     self.address = Address(self.compute, self.project, self.region)
    #     self.address.retrieve_ip_from_instance_template(self.network_interface)
    #
    # def generate_network(self, network, subnetwork):
    #     if not self.is_legacy:
    #         self.network = SubnetNetwork(self.compute, self.project, self.zone, self.region, network, subnetwork)

    def get_external_ip(self):
        try:
            return self.network_interface['accessConfigs']['natIP']
        except:
            return None

    def update_network_interface_with_network(self):
        if self.is_legacy:
            pass
        if self.network != None:
            self.network_interface['network'] = self.network.network_link
            self.network_interface['subnetwork'] = self.network.subnetwork_link

    def update_network_interface_with_address(self):
        if self.is_legacy:
            pass
        if self.address != None:
            del self.network_interface['networkIP']
            if self.address.external_ip != None:
                self.network_interface['accessConfigs']['natIP'] = self.address.external_ip
            elif self.address.external_ip == None and 'accessConfigs' in self.network_interface:
                del self.network_interface['accessConfigs']



