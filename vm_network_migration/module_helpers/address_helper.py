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
""" AddressHelper class: helps to generate an Address class object.

"""
from vm_network_migration.modules.address import Address


class AddressHelper:
    def __init__(self, compute, project, region):
        self.compute = compute
        self.project = project
        self.region = region

    def generate_address(self, instance_template):
        """ Generate an address object

        Args:
            instance_template: the instance template which contains the IP address information

        Returns: an Address object

        """
        address = Address(self.compute, self.project, self.region)
        address.retrieve_ip_from_network_interface(
            instance_template['networkInterfaces'][0])
        return address