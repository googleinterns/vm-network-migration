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
"""
Test helper functions
"""

import unittest2 as unittest
from vm_network_migration.vm_network_migration import *


class ModifyInstanceTemplateWithNewNetwork(unittest.TestCase):
    new_instance = "mock_new_instance"
    new_network_info = {
        "network": "mock_new_network",
        "subnetwork": "mock_new_subnet"}

    def test_basic(self):
        instance_template = {
            'networkInterfaces': [{
                "network": "legacy"}],
            'name': 'mock_old_instance'}

        new_instance_template = modify_instance_template_with_new_network(
            instance_template,
            self.new_instance,
            self.new_network_info)
        self.assertEqual(new_instance_template['name'], self.new_instance)
        self.assertEqual(new_instance_template['networkInterfaces'][0],
                         self.new_network_info)

    def test_invalid_instance_template(self):
        instance_template = {}

        with self.assertRaises(AttributeNotExistError):
            modify_instance_template_with_new_network(instance_template,
                                                      self.new_instance,
                                                      self.new_network_info)
        instance_template = {
            'networkInterfaces': []}

        with self.assertRaises(AttributeNotExistError):
            modify_instance_template_with_new_network(instance_template,
                                                      self.new_instance,
                                                      self.new_network_info)

        instance_template = {
            'name': 'mock_old_instance'}

        with self.assertRaises(AttributeNotExistError):
            modify_instance_template_with_new_network(instance_template,
                                                      self.new_instance,
                                                      self.new_network_info)

        instance_template = {
            'networkInterfaces': {},
            'name': 'mock_old_instance'}
        with self.assertRaises(InvalidTypeError):
            modify_instance_template_with_new_network(instance_template,
                                                      self.new_instance,
                                                      self.new_network_info)


class GenerateExternalIPAddressBody(unittest.TestCase):
    def test_basic(self):
        external_ip_address = "125.125.125.125"
        new_instance_name = "mock_new_instance"
        external_ip_address_body = generate_external_ip_address_body(
            external_ip_address, new_instance_name)
        self.assertEqual(external_ip_address_body["address"],
                         external_ip_address)
        self.assertTrue(new_instance_name in external_ip_address_body["name"])
