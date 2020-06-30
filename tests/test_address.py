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
Test address.py
"""

import httplib2
import mock
import unittest2 as unittest
from googleapiclient.discovery import build
from googleapiclient.http import HttpError
from googleapiclient.http import HttpMock
from googleapiclient.http import RequestMockBuilder
from utils import *
from vm_network_migration.address import (
    Address,
    AddressFactory,
)


class TestRetrieveIpFromInstanceTemplate(unittest.TestCase):

    def test_basic_instance(self):
        original_instance_template = read_json_file(
            "sample_instance_template.json")
        address = mock.MagicMock()
        Address.retrieve_ip_from_network_interface(address,
                                                   original_instance_template[
                                                       'networkInterfaces'][0])
        self.assertEqual(address.external_ip,
                         original_instance_template['networkInterfaces'][0][
                             'accessConfigs'][0]['natIP'])

    def test_instance_no_external_ip(self):
        original_instance_template = read_json_file(
            "sample_instance_template_no_external_ip.json")
        address = mock.MagicMock()
        Address.retrieve_ip_from_network_interface(address,
                                                   original_instance_template[
                                                       'networkInterfaces'][0])
        self.assertEqual(address.external_ip, None)

    def test_instance_no_natIP(self):
        original_instance_template = read_json_file(
            "sample_instance_template_no_natIP.json")
        address = mock.MagicMock()
        Address.retrieve_ip_from_network_interface(address,
                                                   original_instance_template[
                                                       'networkInterfaces'][0])
        self.assertEqual(address.external_ip, None)


class TestPreserveExternalIpAddress(unittest.TestCase):
    project = "mock_project"
    region = "mock_us_central1"
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
        address = Address(compute, self.project, self.region)
        with self.assertRaises(HttpError):
            address.preserve_external_ip_address(
                self.external_ip_address_body)


class TestGenerateExternalIPAddressBody(unittest.TestCase):
    def test_basic(self):
        external_ip_address = "125.125.125.125"
        address = mock.MagicMock()
        address.external_ip = external_ip_address
        address.project = "mock-project"
        address.region = "mock-region"
        external_ip_address_body = Address.generate_external_ip_address_body(
            address)
        self.assertEqual(external_ip_address_body["address"],
                         external_ip_address)

        self.assertTrue(address.project in external_ip_address_body["name"])
        self.assertTrue(address.region in external_ip_address_body["name"])


class TestPreserveIPAddressHandler(unittest.TestCase):
    def setUp(self) -> None:
        self.errorResponse = httplib2.Response({
            "status": 404,
            "reason": "HttpMock response: invalid network"})

    def test_not_preserve_external_ip(self):
        address = mock.MagicMock()
        address.external_ip = "123.123.123.123"
        Address.preserve_ip_addresses_handler(address, False)
        self.assertIsNone(address.external_ip)

    def test_external_ip_is_none(self):
        address = mock.MagicMock()
        address.external_ip = None
        Address.preserve_ip_addresses_handler(address, False)
        self.assertIsNone(address.external_ip)
        Address.preserve_ip_addresses_handler(address, True)
        self.assertIsNone(address.external_ip)

    def test_preserve_external_ip_without_http_error(self):
        address = mock.MagicMock()
        address.external_ip = "123.123.123.123"
        Address.preserve_ip_addresses_handler(address, True)
        self.assertTrue(address.external_ip, "123.123.123.123")

    def test_preserve_an_existing_static_external_ip(self):
        self.errorResponse.reason = "HttpMock response: the IP's name already exists"
        address = mock.MagicMock()
        address.external_ip = "123.123.123.123"
        address.preserve_external_ip_address.side_effect = HttpError(
            resp=self.errorResponse, content=b'')
        Address.preserve_ip_addresses_handler(address, True)
        self.assertTrue(address.external_ip, "123.123.123.123")

    def test_preserve_an_existing_static_ip_name(self):
        # Expect: No error raises, and the original external IP will be used
        # in the new instance template

        self.errorResponse.reason = "HttpMock response: the IP's name already exists"
        address = mock.MagicMock()
        address.external_ip = "123.123.123.123"
        address.preserve_external_ip_address.side_effect = HttpError(
            resp=self.errorResponse, content=b'')
        Address.preserve_ip_addresses_handler(address, True)
        self.assertTrue(address.external_ip, "123.123.123.123")

    def test_other_http_error(self):
        # Expect: No error raises, and the original external IP will be used
        # in the new instance template
        self.errorResponse.reason = "HttpMock response: other http error"
        address = mock.MagicMock()
        address.external_ip = "123.123.123.123"
        address.preserve_external_ip_address.side_effect = HttpError(
            resp=self.errorResponse, content=b'')
        Address.preserve_ip_addresses_handler(address, True)
        self.assertIsNone(address.external_ip)


class TestGenerateAddress(unittest.TestCase):

    def test_generate_address(self):
        instance_network_migration = mock.MagicMock()
        instance_template = read_json_file("sample_instance_template.json")
        address_factory = AddressFactory(instance_network_migration.compute,
                                         instance_network_migration.project,
                                         instance_network_migration.region)
        address = address_factory.generate_address(instance_template)
        self.assertEqual(address.project, instance_network_migration.project)
        self.assertEqual(address.region, instance_network_migration.region)
        self.assertEqual(address.external_ip,
                         instance_template['networkInterfaces'][0][
                             'accessConfigs'][0]['natIP'])

    def test_generate_address_no_external_ip(self):
        instance_network_migration = mock.MagicMock()
        instance_template = read_json_file(
            "sample_instance_template_no_external_ip.json")
        address_factory = AddressFactory(instance_network_migration.compute,
                                         instance_network_migration.project,
                                         instance_network_migration.region)
        address = address_factory.generate_address(instance_template)
        self.assertEqual(address.project, instance_network_migration.project)
        self.assertEqual(address.region, instance_network_migration.region)
        self.assertEqual(address.external_ip, None)
