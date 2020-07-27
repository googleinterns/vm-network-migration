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
""" SubnetNetwork class: describes an instance's subnetwork.
    SubnetNetworkHelper class: helps to create a SubnetNetwork object
"""
from vm_network_migration.errors import *
from vm_network_migration.utils import initializer


class SubnetNetwork():
    @initializer
    def __init__(self, compute, project, zone, region, network,
                 subnetwork=None):
        """ Initialize a SubnetNetwork object.
            If the network is auto, then the subnetwork name is optional;
            otherwise, it should be specified
        Args:
            compute: google compute engine
            project: project ID
            zone: zone name
            region: region name
            network: network name
            subnetwork: subnetwork name
        """
        self.network_link = None
        self.subnetwork_link = None

    def check_subnetwork_validation(self):
        """ Check if the current subnetwork is a potential valid subnetwork

        Raises:
            MissingSubnetworkError: The subnetwork is not specified and
            the network is in a custom mode.
        """

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

            Returns:
                a deserialized object of the network information

            Raises:
                googleapiclient.errors.HttpError: invalid request
        """
        return self.compute.networks().get(
            project=self.project,
            network=self.network).execute()

    def generate_new_network_info(self):
        network_parameters = self.get_network()
        self.network_link = network_parameters['selfLink']
        self.subnetwork_link = 'regions/' + self.region + '/subnetworks/' + self.subnetwork

    def check_network_auto_mode(self) -> bool:
        """ Check if the network is in auto mode

        Returns:
            true or false

        Raises:
            InvalidTargetNetworkError: if the network is not a subnetwork mode network
        """
        network_info = self.get_network()
        if 'autoCreateSubnetworks' not in network_info:
            raise InvalidTargetNetworkError(
                'The target network is not a subnetwork mode network')
        auto_mode_status = network_info['autoCreateSubnetworks']
        return auto_mode_status
