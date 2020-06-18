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

import json
import os

import httplib2
import timeout_decorator
import unittest2 as unittest
from googleapiclient.discovery import build
from googleapiclient.http import HttpMock
from googleapiclient.http import RequestMockBuilder
from vm_network_migration.vm_network_migration import *

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def datafile(filename):
    """Generate path of the file
    Args:
        filename: file name

    Returns: the file path

    """
    return os.path.join(DATA_DIR, filename)


def read_json_file(filename):
    """Read *.json file
    Args:
        filename: json file name

    Returns: a Python object

    """
    with open(datafile(filename)) as f:
        res = json.load(f)
        f.close()
    return res


class BasicGoogleAPICalls(unittest.TestCase):
    project = "mock_project"
    zone = "mock_us_central1_a"
    region = "mock_us_central1"
    instance = "mock_instance_legacy"
    boot_disk = "mock_boot_disk"
    target_network = "mock_target_network"
    target_subnetwork = "mock_target_subnetwork"
    instance_template = {
        "mock_instance_template": "mocking"}
    internal_ip_address_body = {
        "name": "example-internal-address",
        "addressType": "INTERNAL",
        "subnetwork": "regions/us-central1/subnetworks/my-custom-subnet",
        "address": "10.128.0.12"
    }
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

    def test_stop_instance_success(self):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.stop": (
                    self.successResponse, '{"foo": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        stop_instance_operation = stop_instance(compute, self.project,
                                                self.zone, self.instance)
        self.assertEqual(
            stop_instance_operation,
            {
                "foo": "bar"}
        )

    def test_stop_instance_failure(self):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.stop": (
                    self.errorResponse, b"{Invalid resource}")})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        with self.assertRaises(HttpError):
            stop_instance(compute, self.project, self.zone, self.instance)

    def test_start_instance_success(self):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.start": (
                    self.successResponse, '{"foo": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        start_instance_operation = start_instance(compute, self.project,
                                                  self.zone, self.instance)
        self.assertEqual(
            start_instance_operation,
            {
                "foo": "bar"}
        )

    def test_start_instance_failure(self):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.start": (
                    self.errorResponse, b"{Invalid resource}")})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        with self.assertRaises(HttpError):
            start_instance(compute, self.project, self.zone, self.instance)

    def test_retrieve_instance_template_success(self):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.get": (
                    self.successResponse, '{"foo": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        retrieve_template_operation = retrieve_instance_template(compute,
                                                                 self.project,
                                                                 self.zone,
                                                                 self.instance)
        self.assertEqual(
            retrieve_template_operation,
            {
                "foo": "bar"}
        )

    def test_retrieve_instance_template_failure(self):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.get": (
                    self.errorResponse, b"{Invalid resource}")})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        with self.assertRaises(HttpError):
            retrieve_instance_template(compute, self.project, self.zone,
                                       self.instance)

    def test_detach_disk_success(self):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.detachDisk": (
                    self.successResponse, '{"foo": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        detach_disk_operation = detach_disk(compute, self.project,
                                            self.zone, self.instance,
                                            self.boot_disk)
        self.assertEqual(
            detach_disk_operation,
            {
                "foo": "bar"}
        )

    def test_detach_disk_failure(self):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.detachDisk": (
                    self.errorResponse, b"{Invalid resource}")})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        with self.assertRaises(HttpError):
            detach_disk(compute, self.project, self.zone, self.instance,
                        self.boot_disk)

    def test_attach_disk_success(self):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.attachDisk": (
                    self.successResponse, '{"foo": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        attach_disk_operation = attach_disk(compute, self.project,
                                            self.zone, self.instance,
                                            self.boot_disk)
        self.assertEqual(
            attach_disk_operation,
            {
                "foo": "bar"}
        )

    def test_attach_disk_failure(self):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.attachDisk": (
                    self.errorResponse, b"{Invalid resource}")})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        with self.assertRaises(HttpError):
            attach_disk(compute, self.project, self.zone, self.instance,
                        self.boot_disk)

    def test_get_network_success(self):
        request_builder = RequestMockBuilder(
            {
                "compute.networks.get": (
                    self.successResponse, '{"foo": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        network_get_operation = get_network(compute, self.project,
                                            self.target_network)
        self.assertEqual(
            network_get_operation,
            {
                "foo": "bar"}
        )

    def test_get_network_failure(self):
        request_builder = RequestMockBuilder(
            {
                "compute.networks.get": (
                    self.errorResponse, b"{Invalid resource}")})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        with self.assertRaises(HttpError):
            get_network(compute, self.project, self.target_network)

    def test_create_instance_success(self):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.insert": (
                    self.successResponse, '{"foo": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        create_instance_operation = create_instance(compute, self.project,
                                                    self.zone,
                                                    self.instance_template)
        self.assertEqual(
            create_instance_operation,
            {
                "foo": "bar"}
        )

    def test_create_instance_failure(self):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.insert": (
                    self.errorResponse, b"{Invalid resource}")})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        with self.assertRaises(HttpError):
            create_instance(compute, self.project, self.zone,
                            self.instance_template)

    def test_delete_instance_success(self):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.delete": (
                    self.successResponse, '{"foo": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        delete_instance_operation = delete_instance(compute, self.project,
                                                    self.zone, self.instance)
        self.assertEqual(
            delete_instance_operation,
            {
                "foo": "bar"}
        )

    def test_delete_instance_failure(self):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.delete": (
                    self.errorResponse, b"{Invalid resource}")})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        with self.assertRaises(HttpError):
            delete_instance(compute, self.project, self.zone,
                            self.instance_template)

    def test_get_zone_success(self):
        request_builder = RequestMockBuilder(
            {
                "compute.zones.get": (
                    self.successResponse, '{"foo": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        get_zone_operation = get_zone(compute, self.project, self.zone)
        self.assertEqual(
            get_zone_operation,
            {
                "foo": "bar"}
        )

    def test_get_zone_failure(self):
        request_builder = RequestMockBuilder(
            {
                "compute.zones.get": (
                    self.errorResponse, b"{Invalid resource}")})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        with self.assertRaises(HttpError):
            get_zone(compute, self.project, self.zone)

    def test_check_network_auto_mode_success(self):
        request_builder = RequestMockBuilder(
            {
                "compute.networks.get": (
                    self.successResponse, '{"autoCreateSubnetworks": true}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        auto_mode_status = check_network_auto_mode(compute, self.project,
                                                   self.zone)
        self.assertEqual(auto_mode_status, True)

    def test_check_network_auto_mode_failure(self):
        request_builder = RequestMockBuilder(
            {
                "compute.networks.get": (
                    self.errorResponse, b"{Invalid resource}")})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        with self.assertRaises(HttpError):
            check_network_auto_mode(compute, self.project, self.zone)

    def test_wait_for_zone_operation_success(self):
        request_builder = RequestMockBuilder(
            {
                "compute.zoneOperations.get": (
                    self.successResponse, '{"status": "DONE"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        wait_response = wait_for_zone_operation(compute, self.project,
                                                self.zone, {})

        self.assertEqual(
            wait_response,
            {
                "status": "DONE"}
        )

    def test_wait_for_zone_operation_failure(self):
        request_builder = RequestMockBuilder(
            {
                "compute.zoneOperations.get": (
                    self.errorResponse, b'Invalid Resource')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        with self.assertRaises(HttpError):
            wait_for_zone_operation(compute, self.project, self.zone, {})

    def test_wait_for_region_operation_success(self):
        request_builder = RequestMockBuilder(
            {
                "compute.regionOperations.get": (
                    self.successResponse, '{"status": "DONE"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        wait_response = wait_for_region_operation(compute, self.project,
                                                  self.region, {})

        self.assertEqual(
            wait_response,
            {
                "status": "DONE"}
        )

    def test_wait_for_region_operation_failure(self):
        request_builder = RequestMockBuilder(
            {
                "compute.regionOperations.get": (
                    self.errorResponse, b'Invalid Resource')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        with self.assertRaises(HttpError):
            wait_for_region_operation(compute, self.project, self.region, {})

    def test_preserve_external_ip_success(self):
        request_builder = RequestMockBuilder(
            {
                "compute.addresses.insert": (
                    self.successResponse, '{"foo": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        preserve_external_ip_address_operation = preserve_external_ip_address(
            compute, self.project, self.region, self.external_ip_address_body)
        self.assertEqual(
            preserve_external_ip_address_operation,
            {
                "foo": "bar"}
        )

    def test_preserve_external_ip_failure(self):
        request_builder = RequestMockBuilder(
            {
                "compute.addresses.insert": (
                    self.errorResponse, b"{Invalid resource}")})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        with self.assertRaises(HttpError):
            preserve_external_ip_address(compute, self.project, self.region,
                                         self.external_ip_address_body)


class CheckNetworkAutoMode(unittest.TestCase):
    project = "mock_project"
    http = HttpMock(datafile("compute_rest.json"), {
        "status": "200"})
    errorResponse = httplib2.Response({
        "status": 404,
        "reason": "HttpMock response: the resource is not found"})
    successResponse = httplib2.Response({
        "status": 200,
        "reason": "HttpMock response: Successful"
    })

    def test_non_auto_mode_network(self):
        target_network_information = read_json_file(
            "sample_non_auto_mode_network.json")
        target_network = target_network_information["name"]
        request_builder = RequestMockBuilder(
            {
                "compute.networks.get": (
                    self.successResponse,
                    json.dumps(target_network_information))})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        auto_mode = check_network_auto_mode(compute, self.project,
                                            target_network)
        self.assertEqual(auto_mode, False)

    def test_auto_mode_network(self):
        target_network_information = read_json_file(
            "sample_auto_mode_network.json")
        target_network = target_network_information["name"]
        request_builder = RequestMockBuilder(
            {
                "compute.networks.get": (
                    self.successResponse,
                    json.dumps(target_network_information))})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        auto_mode = check_network_auto_mode(compute, self.project,
                                            target_network)
        self.assertEqual(auto_mode, True)

    def test_change_to_legacy_network(self):
        target_legacy_network_information = read_json_file(
            "sample_legacy_network.json")
        target_legacy_network = target_legacy_network_information["name"]
        request_builder = RequestMockBuilder(
            {
                "compute.networks.get": (
                    self.successResponse,
                    json.dumps(target_legacy_network_information))})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        with self.assertRaises(InvalidTargetNetworkError):
            check_network_auto_mode(compute, self.project,
                                    target_legacy_network)


class WaitForOperation(unittest.TestCase):
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

    @timeout_decorator.timeout(3, timeout_exception=StopIteration)
    def test_basic_zone_waiting(self):
        request_builder = RequestMockBuilder(
            {
                "compute.zoneOperations.get": (
                    self.successResponse,
                    '{"status":"RUNNING"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        with self.assertRaises(StopIteration):
            wait_for_zone_operation(compute, self.project,
                                    self.zone, {})

    def test_error_in_zone_waiting(self):
        request_builder = RequestMockBuilder(
            {
                "compute.zoneOperations.get": (
                    self.successResponse,
                    '{"status":"DONE", "error":"something wrong"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        with self.assertRaises(ZoneOperationsError):
            wait_for_zone_operation(compute, self.project,
                                    self.zone, {})

    @timeout_decorator.timeout(3, timeout_exception=StopIteration)
    def test_basic_region_waiting(self):
        request_builder = RequestMockBuilder(
            {
                "compute.regionOperations.get": (
                    self.successResponse,
                    '{"status":"RUNNING"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        with self.assertRaises(StopIteration):
            wait_for_region_operation(compute, self.project,
                                      self.region, {})

    def test_error_in_region_waiting(self):
        request_builder = RequestMockBuilder(
            {
                "compute.regionOperations.get": (
                    self.successResponse,
                    '{"status":"DONE", "error":"something wrong"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        with self.assertRaises(RegionOperationsError):
            wait_for_region_operation(compute, self.project,
                                      self.region, {})
