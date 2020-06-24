from vm_network_migration.errors import *
class SubnetNetwork():
    def __init__(self, compute, project, zone, region, network, subnetwork=None):
        self.compute = compute
        self.project = project
        self.zone = zone
        self.region = region
        self.network = network
        self.subnetwork = subnetwork
        self.network_link = None
        self.subnetwork_link = None



    def check_subnetwork_validation(self):
        # If the network is auto, then the subnetwork name is optional.
        # Otherwise it should be specified
        if self.subnetwork != None:
            pass
        automode_status = self.check_network_auto_mode()
        if self.subnetwork is None:
            if not automode_status:
                raise MissingSubnetworkError('No specified subnetwork')
            else:
                # the network is in auto mode, the default subnetwork name is the
                # same as the network name
                self.subnetwork = self.network

    def get_network(self) -> dict:
        """ Get the network information.

            Args:
                compute: google API compute engine service
                project: project ID
                network: name of the network

            Returns:
                a dict of the network information

            Raises:
                googleapiclient.errors.HttpError: invalid request
        """
        return self.compute.networks().get(
            project=self.project,
            network=self.network).execute()

    def generate_new_network_info(self):
        network_parameters = self.get_network()
        self.network_link = network_parameters['selfLink']
        self.subnetwork_link = self.network_link.split('global')[0] + 'regions/' + self.region + '/subnetworks/' + self.subnetwork

    def check_network_auto_mode(self) -> bool:
        """ Check if the network is in auto mode

        Args:
            compute: google API compute engine service
            project: project ID
            network: name of the network

        Returns:
            true or false

        Raises:
            InvalidTargetNetworkError: if the network is not a subnetwork mode network
            googleapiclient.errors.HttpError: invalid request
        """
        network_info = self.get_network()
        if 'autoCreateSubnetworks' not in network_info:
            raise InvalidTargetNetworkError(
                'The target network is not a subnetwork mode network')
        auto_mode_status = network_info['autoCreateSubnetworks']
        return auto_mode_status

