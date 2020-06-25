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
import mock
import unittest2 as unittest
from google.auth import credentials
from googleapiclient.discovery import build
from googleapiclient.http import HttpMock
from googleapiclient.http import RequestMockBuilder
from utils import *
from vm_network_migration.address import Address
from vm_network_migration.vm_network_migration import *


class TestRetrieveIpFromInstanceTemplate(unittest.TestCase):
    def setUp(self) -> None:
        self.http = HttpMock(datafile("compute_rest.json"), {
            "status": "200"})
        self.request_builder = RequestMockBuilder({})
        self.compute = build("compute", "v1", self.http,
                             requestBuilder=self.request_builder)
        self.project = 'mock_project'
        self.region = 'mock_region'

    def test_basic_instance(self):
        original_instance_template = read_json_file(
            "sample_instance_template.json")
        address = Address(self.compute, self.project, self.region)
        address.retrieve_ip_from_network_interface(
            original_instance_template['networkInterfaces'][0])
        self.assertEqual(address.external_ip,
                         original_instance_template['networkInterfaces'][0][
                             'accessConfigs'][0]['natIP'])

    def test_instance_no_external_ip(self):
        original_instance_template = read_json_file(
            "sample_instance_template_no_external_ip.json")
        address = Address(self.compute, self.project, self.region)
        address.retrieve_ip_from_network_interface(
            original_instance_template['networkInterfaces'][0])
        self.assertEqual(address.external_ip, None)

    def test_instance_no_natIP(self):
        original_instance_template = read_json_file(
            "sample_instance_template_no_natIP.json")
        address = Address(self.compute, self.project, self.region)
        address.retrieve_ip_from_network_interface(
            original_instance_template['networkInterfaces'][0])
        self.assertEqual(address.external_ip, None)


class TestPreserveExternalIpAddress(unittest.TestCase):
    project = "mock_project"
    zone = "mock_us_central1_a"
    region = "mock_us_central1"
    instance = "mock_instance_legacy"
    boot_disk = "mock_boot_disk"
    target_network = "mock_target_network"
    target_subnetwork = "mock_target_subnetwork"
    instance_template = {
        "mock_instance_template": "mocking"}
    external_ip_address_body = {
        "name": "example-external-address",
        "address": "35.203.14.22"
    }
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
                "compute.addresses.insert": (
                    self.successResponse, '{"name": "bar"}'),
                "compute.regionOperations.get": (
                    self.successResponse, '{"status": "DONE"}'
                )})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        address = Address(compute, self.project, self.region)
        preserve_external_ip_address_operation = address.preserve_external_ip_address(
            self.external_ip_address_body)
        self.assertEqual(
            preserve_external_ip_address_operation,
            {
                "name": "bar"}
        )

    def test_preserve_external_ip_failure(self):
        request_builder = RequestMockBuilder(
            {
                "compute.addresses.insert": (
                    self.errorResponse, b"{Invalid resource}"),
                "compute.regionOperations.get": (
                    self.successResponse, '{"status": "DONE"}'
                )})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        with self.assertRaises(HttpError):
            preserve_external_ip_address(compute, self.project, self.region,
                                         self.external_ip_address_body)


class TestGenerateExternalIPAddressBody(unittest.TestCase):
    def setUp(self) -> None:
        self.http = HttpMock(datafile("compute_rest.json"), {
            "status": "200"})
        self.request_builder = RequestMockBuilder({})
        self.compute = build("compute", "v1", self.http,
                             requestBuilder=self.request_builder)
        self.project = 'mock_project'
        self.region = 'mock_region'

    def test_basic(self):
        external_ip_address = "125.125.125.125"
        address = Address(self.compute, self.project, self.region)
        address.external_ip = external_ip_address
        external_ip_address_body = address.generate_external_ip_address_body()
        self.assertEqual(external_ip_address_body["address"],
                         external_ip_address)
        self.assertTrue(self.project in external_ip_address_body["name"])
        self.assertTrue(self.region in external_ip_address_body["name"])


@patch(
    "vm_network_migration.operations.Operations.wait_for_region_operation")  # index: 1
@patch(
    "vm_network_migration.address.Address.preserve_external_ip_address")  # index 0
class PreserveIPAddressHandler(unittest.TestCase):
    def setUp(self) -> None:
        self.MOCK_CREDENTIALS = mock.Mock(
            spec=google.auth.credentials.Credentials)
        self.errorResponse = httplib2.Response({
            "status": 404,
            "reason": "HttpMock response: invalid network"})
        self.compute = discovery.build('compute', 'v1',
                                       credentials=self.MOCK_CREDENTIALS)
        self.project = 'mock_project'
        self.region = 'mock_region'

    def test_not_preserve_external_ip(self, *mocks):
        address = Address(self.compute, self.project, self.region)
        address.external_ip = "123.123.123.123"
        address.preserve_ip_addresses_handler(False)
        self.assertIsNone(address.external_ip)

    def test_external_ip_is_none(self, *mocks):
        address = Address(self.compute, self.project, self.region)
        address.external_ip = None
        address.preserve_ip_addresses_handler(False)
        self.assertIsNone(address.external_ip)
        address.preserve_ip_addresses_handler(True)
        self.assertIsNone(address.external_ip)

    def test_preserve_external_ip_without_http_error(self, *mocks):
        mocks[1].return_value = {
            'name': 'good'}
        address = Address(self.compute, self.project, self.region)
        address.external_ip = "123.123.123.123"
        address.preserve_ip_addresses_handler(True)
        mocks[1].assert_called()
        self.assertTrue(address.external_ip, "123.123.123.123")

    def test_preserve_an_existing_static_external_ip(self, *mocks):
        self.errorResponse.reason = "HttpMock response: the IP address already exists"
        mocks[1].side_effect = HttpError(resp=self.errorResponse, content=b'')
        address = Address(self.compute, self.project, self.region)
        address.external_ip = "123.123.123.123"
        address.preserve_ip_addresses_handler(True)
        mocks[1].assert_called()
        self.assertTrue(address.external_ip, "123.123.123.123")

    def test_preserve_an_existing_static_ip_name(self, *mocks):
        # Expect: No error raises, and the original external IP will be used
        # in the new instance template

        self.errorResponse.reason = "HttpMock response: the IP's name already exists"
        mocks[1].side_effect = HttpError(resp=self.errorResponse, content=b'')
        address = Address(self.compute, self.project, self.region)
        address.external_ip = "123.123.123.123"
        address.preserve_ip_addresses_handler(True)
        mocks[1].assert_called()
        self.assertTrue(address.external_ip, "123.123.123.123")

    def test_other_http_error(self, *mocks):
        # Expect: No error raises, and the original external IP will be used
        # in the new instance template
        self.errorResponse.reason = "HttpMock response: other http error"
        mocks[1].side_effect = HttpError(resp=self.errorResponse, content=b'')
        address = Address(self.compute, self.project, self.region)
        address.external_ip = "123.123.123.123"
        address.preserve_ip_addresses_handler(True)
        mocks[1].assert_called()
        self.assertIsNone(address.external_ip)
