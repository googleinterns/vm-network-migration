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
Test subnet_network.py
"""

import httplib2
import mock
import unittest2 as unittest
from googleapiclient.discovery import build
from googleapiclient.http import HttpMock
from googleapiclient.http import RequestMockBuilder
from utils import *
from vm_network_migration.subnet_network import SubnetNetwork
from vm_network_migration.vm_network_migration import *


class TestCheckSubnetworkValidation(unittest.TestCase):

    def test_subnetwork_not_none_in_auto_mode(self):
        mock_subnetwork_name = "mock-subnetwork"
        subnet_network = mock.MagicMock()
        subnet_network.subnetwork = mock_subnetwork_name
        subnet_network.check_network_auto_mode.return_value = True
        SubnetNetwork.check_subnetwork_validation(subnet_network)
        self.assertEqual(subnet_network.subnetwork, mock_subnetwork_name)

    def test_subnetwork_is_none_in_auto_mode(self):
        network_name = "mock-network"
        subnet_network = mock.MagicMock()
        subnet_network.network = network_name
        subnet_network.subnetwork = None
        subnet_network.check_network_auto_mode.return_value = True
        SubnetNetwork.check_subnetwork_validation(subnet_network)
        self.assertEqual(subnet_network.subnetwork, network_name)

    def test_subnetwork_not_none_in_custom_mode(self):
        subnetwork_name = "mock-subnetwork"
        network_name = "mock-network"
        subnet_network = mock.MagicMock()
        subnet_network.network = network_name
        subnet_network.subnetwork = subnetwork_name
        subnet_network.check_network_auto_mode.return_value = False
        SubnetNetwork.check_subnetwork_validation(subnet_network)
        self.assertEqual(subnet_network.subnetwork, subnetwork_name)

    def test_subnetwork_is_none_in_custom_mode(self):
        network_name = "mock-network"
        subnet_network = mock.MagicMock()
        subnet_network.network = network_name
        subnet_network.subnetwork = None
        subnet_network.check_network_auto_mode.return_value = False

        with self.assertRaises(MissingSubnetworkError):
            SubnetNetwork.check_subnetwork_validation(subnet_network)


class TestGetNetwork(unittest.TestCase):
    project = "mock_project"
    zone = "mock_us_central1_a"
    region = "mock_us_central1"
    http = HttpMock(datafile("compute_rest.json"), {
        "status": "200"})
    errorResponse = httplib2.Response({
        "status": 404,
        "reason": "HttpMock response: the resource is not found"})
    successResponse = httplib2.Response({
        "status": 200,
        "reason": "HttpMock response: Successful"
    })

    def test_preserve_external_ip_success(self):
        request_builder = RequestMockBuilder(
            {
                "compute.networks.get": (
                    self.successResponse, '{"name": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        subnet = SubnetNetwork(compute, self.project, self.zone,
                               self.region, "mock-network", "mock-subnet")
        get_network_operation = subnet.get_network()
        self.assertEqual(
            get_network_operation,
            {
                "name": "bar"}
        )

    def test_preserve_external_ip_failure(self):
        request_builder = RequestMockBuilder(
            {
                "compute.networks.get": (
                    self.errorResponse, b'{"name": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        subnet = SubnetNetwork(compute, self.project, self.zone,
                               self.region, "mock-network", "mock-subnet")

        with self.assertRaises(HttpError):
            subnet.get_network()


class TestGenerateNewNetworkInfo(unittest.TestCase):
    def test_basic(self):
        subnet_network = mock.MagicMock()
        subnet_network.get_network.return_value = {
            'selfLink': 'https://www.googleapis.com/compute/v1/projects/mock_project/global/networks/target-network'}
        subnet_network.subnetwork = 'target-subnetwork'
        subnet_network.region = 'mock-region'
        SubnetNetwork.generate_new_network_info(subnet_network)
        self.assertEqual(subnet_network.network_link,
                         subnet_network.get_network.return_value['selfLink'])
        self.assertEqual(subnet_network.subnetwork_link,
                         'regions/mock-region/subnetworks/target-subnetwork')


class TestCheckNetworkAutoMode(unittest.TestCase):

    def test_auto_mode_network(self):
        subnet_network = mock.MagicMock()
        subnet_network.get_network.return_value = read_json_file(
            "sample_auto_mode_network.json")
        auto_mode = SubnetNetwork.check_network_auto_mode(subnet_network)
        self.assertEqual(auto_mode, True)

    def test_non_auto_mode_network(self):
        subnet_network = mock.MagicMock()
        subnet_network.get_network.return_value = read_json_file(
            "sample_non_auto_mode_network.json")
        auto_mode = SubnetNetwork.check_network_auto_mode(subnet_network)
        self.assertEqual(auto_mode, False)
