# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" SubnetNetworkHelper class: helps to create a SubnetNetwork object
"""
from vm_network_migration.modules.other_modules.subnet_network import SubnetNetwork
from vm_network_migration.utils import initializer


class SubnetNetworkHelper:
    @initializer
    def __init__(self, compute, project, zone, region=None, only_check_network_info=False):
        """ Initialization

        Args:
            compute: compute engine
            project: project ID
            zone: zone of the network
            region: region of the network
            only_check_network_info: only check network information, subnetwork is ignored
        """
        if self.region == None and not self.only_check_network_info:
            self.region = self.get_region()

    def generate_network(self, network, subnetwork):
        """ Generate a network object

        Args:
            network: network name
            subnetwork: subnetwork name

        Returns: a SubnetNetwork object

        """
        network = SubnetNetwork(self.compute, self.project, self.zone,
                                self.region, network, subnetwork, self.only_check_network_info)
        network.subnetwork_validation()
        network.generate_new_network_info()

        return network

    def get_region(self) -> dict:
        """ Get region information

            Returns:
                region name of the self.zone

            Raises:
                googleapiclient.errors.HttpError: invalid request
        """
        return self.compute.zones().get(
            project=self.project,
            zone=self.zone).execute()['region'].split('regions/')[1]
