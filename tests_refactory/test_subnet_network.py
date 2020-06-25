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
Test googleapi http calls
"""

from unittest.mock import patch

import httplib2
import unittest2 as unittest
from googleapiclient.discovery import build
from googleapiclient.http import HttpMock
from googleapiclient.http import RequestMockBuilder
from utils import *
from vm_network_migration.subnet_network import SubnetNetwork
from vm_network_migration.vm_network_migration import *


@patch(
    "vm_network_migration.subnet_network.SubnetNetwork.generate_new_network_info")  # index 0
@patch(
    "vm_network_migration.subnet_network.SubnetNetwork.check_network_auto_mode")  # index 0
class TestCheckSubnetworkValidation(unittest.TestCase):
    def setUp(self) -> None:
        self.http = HttpMock(datafile("compute_rest.json"), {
            "status": "200"})
        self.request_builder = RequestMockBuilder({})
        self.compute = build("compute", "v1", self.http,
                        requestBuilder=self.request_builder)
        self.project = 'mock_project'
        self.region = 'mock_region'
        self.zone = 'mock_zone'

    def test_subnetwork_not_none_in_auto_mode(self, *mocks):
        mocks[0].return_value = True
        mocks[1].return_value = True
        network = 'mock_network'
        subnetwork = 'mock_subnetwork'
        subnet = SubnetNetwork(self.compute, self.project, self.zone, self.region, network, subnetwork)
        subnet.check_subnetwork_validation()
        self.assertEqual(subnet.subnetwork, subnetwork)


    def test_subnetwork_is_none_in_auto_mode(self, *mocks):
        mocks[0].return_value = True
        mocks[1].return_value = True
        network = 'mock_network'
        subnetwork = None
        subnet = SubnetNetwork(self.compute, self.project, self.zone, self.region, network, subnetwork)
        subnet.check_subnetwork_validation()
        self.assertEqual(subnet.subnetwork, network)

    def test_subnetwork_not_none_in_custom_mode(self, *mocks):
        mocks[0].return_value = False
        mocks[1].return_value = True
        network = 'mock_network'
        subnetwork = 'mock_subnetwork'
        subnet = SubnetNetwork(self.compute, self.project, self.zone, self.region, network, subnetwork)
        subnet.check_subnetwork_validation()
        self.assertEqual(subnet.subnetwork, subnetwork)


    def test_subnetwork_is_none_in_custom_mode(self, *mocks):
        mocks[0].return_value = False
        mocks[1].return_value = True
        network = 'mock_network'
        subnetwork = None

        with self.assertRaises(MissingSubnetworkError):
            subnet = SubnetNetwork(self.compute, self.project, self.zone,
                                   self.region, network, subnetwork)
            subnet.check_subnetwork_validation()

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



@patch(
    "vm_network_migration.subnet_network.SubnetNetwork.get_network")  # index 0
class TestGenerateNewNetworkInfo(unittest.TestCase):
    def setUp(self) -> None:
        self.http = HttpMock(datafile("compute_rest.json"), {
            "status": "200"})
        self.request_builder = RequestMockBuilder({})
        self.compute = build("compute", "v1", self.http,
                        requestBuilder=self.request_builder)
        self.project = 'mock_project'
        self.region = 'mock_region'
        self.zone = 'mock_zone'

    def test_basic(self, *mocks):
        mocks[0].return_value = {'selfLink': 'https://www.googleapis.com/compute/v1/projects/mock_project/global/networks/target-network'}
        network = 'target-network'
        subnetwork = 'target-subnetwork'
        subnet = SubnetNetwork(self.compute, self.project, self.zone, self.region, network, subnetwork)
        subnet.generate_new_network_info()
        self.assertEqual(subnet.subnetwork_link, 'https://www.googleapis.com/compute/v1/projects/mock_project/regions/mock_region/subnetworks/target-subnetwork')

@patch(
    "vm_network_migration.subnet_network.SubnetNetwork.get_network")  # index 0
class TestGenerateNewNetworkInfo(unittest.TestCase):
    def setUp(self) -> None:
        self.http = HttpMock(datafile("compute_rest.json"), {
            "status": "200"})
        self.request_builder = RequestMockBuilder({})
        self.compute = build("compute", "v1", self.http,
                        requestBuilder=self.request_builder)
        self.project = 'mock_project'
        self.region = 'mock_region'
        self.zone = 'mock_zone'

    def test_auto_mode_network(self, *mocks):
        mocks[0].return_value = read_json_file(
            "sample_auto_mode_network.json")
        network = 'target-network'
        subnetwork = 'target-subnetwork'
        subnet = SubnetNetwork(self.compute, self.project, self.zone, self.region, network, subnetwork)
        auto_mode = subnet.check_network_auto_mode()
        self.assertEqual(auto_mode, True)

    def test_non_auto_mode_network(self, *mocks):
        mocks[0].return_value = read_json_file(
            "sample_non_auto_mode_network.json")
        network = 'target-network'
        subnetwork = 'target-subnetwork'
        subnet = SubnetNetwork(self.compute, self.project, self.zone, self.region, network, subnetwork)
        auto_mode = subnet.check_network_auto_mode()
        self.assertEqual(auto_mode, False)