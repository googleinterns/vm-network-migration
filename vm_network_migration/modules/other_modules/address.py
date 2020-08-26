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
""" Address class: describes an instance's IP address and handle the related API calls
"""
import warnings

from googleapiclient.errors import HttpError
from vm_network_migration.errors import *
from vm_network_migration.modules.other_modules.operations import Operations
from vm_network_migration.utils import *


class Address:
    @initializer
    def __init__(self, compute, project, region, external_ip=None):
        """ Initialize an Address object
        Args:
            compute: google api compute engine
            project: project ID
            region: region of the instance
            external_ip: external IP address, such as "123.123.123.123"
        """
        self.operations = Operations(compute, project, None, region)

    def get_region(self) -> str:
        """ Get region information

            Returns: region name

            Raises:
                googleapiclient.errors.HttpError: invalid request
        """
        return self.compute.zones().get(
            project=self.project,
            zone=self.zone).execute()['region'].split('regions/')[1]

    def retrieve_ip_from_network_interface(self, network_interface):
        """ Get external IP address from the network interface dict
        and update self.external_ip

        Args:
            network_interface: the network interface dictionary, such as
            {
              "network": "https://www.googleapis.com/compute/v1/projects/mock_project/global/networks/default",
              "networkIP": "10.128.0.9",
              "accessConfigs": [
                {
                  "type": "ONE_TO_ONE_NAT",
                  "name": "External NAT",
                  "natIP": "23.24.5.64",
                  "networkTier": "PREMIUM",
                  "kind": "compute#accessConfig"
                }
              ]
            }

        Returns: None

        """
        if 'accessConfigs' in network_interface and 'natIP' in \
                network_interface['accessConfigs'][0]:
            self.external_ip = network_interface['accessConfigs'][0][
                'natIP']
        else:
            self.external_ip = None
        return self.external_ip

    def preserve_ip_addresses_handler(self, preserve_external_ip):
        """Preserve the IP address.

        Args:
            preserve_external_ip: boolean. Preserving the external ip or not

        """

        if preserve_external_ip and self.external_ip != None:
            print('Preserving the external IP address')
            # There is no external ip assigned to the original VM
            # An ephemeral external ip will be assigned to the new VM

            external_ip_address_body = self.generate_external_ip_address_body()
            try:
                preserve_external_ip_operation = self.preserve_external_ip_address(
                    external_ip_address_body)
                self.operations.wait_for_region_operation(
                    preserve_external_ip_operation[
                        'name'])
            except Exception as e:
                if isinstance(e, HttpError) and \
                        'already reserved' in e._get_reason():
                    # The external IP is already preserved as a static IP,
                    return
                warnings.warn(
                    'Failed to preserve the external IP address as a static IP.',
                    Warning)
                raise e
            else:
                print(
                    '%s is reserved as a static IP address.' % (
                        self.external_ip))
        else:
            self.external_ip = None

    def preserve_external_ip_address(self, address_body):
        """ Preserve the external IP address.

        Args:
            address_body: internal IP address information, such as
               {
                  name: "ADDRESS_NAME",
                  address: "IP_ADDRESS"
                }
        Returns: a deserialized object of the response

        Raises:
            googleapiclient.errors.HttpError: If the IP
            address is already a static one, or if the IP is not being
            used by any instance, or invalid request, it will raise an Http error
        """
        preserve_external_ip_operation = self.compute.addresses().insert(
            project=self.project, region=self.region,
            body=address_body).execute()
        self.operations.wait_for_region_operation(
            preserve_external_ip_operation['name'])
        return preserve_external_ip_operation

    def generate_external_ip_address_body(self) -> dict:
        """Generate body of an external IP address.

        Returns:
              {
              name: "ADDRESS_NAME",
              address: "IP_ADDRESS"
            }
        """
        if self.external_ip == None:
            raise AttributeNotExistError
        external_ip_address_body = {}
        external_ip_address_body[
            'name'] = self.project + '-' + self.region + '-' + generate_timestamp_string()
        external_ip_address_body['address'] = self.external_ip
        return external_ip_address_body
