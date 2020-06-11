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
from __future__ import absolute_import
import json
import os

import google
import httplib2
import mock
import timeout_decorator
import unittest2 as unittest
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import HttpMock
from googleapiclient.http import RequestMockBuilder
from mock import patch
from vm_network_migration import *

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def datafile(filename):
    return os.path.join(DATA_DIR, filename)


def read_json_file(filename):
    with open(datafile(filename)) as f:
        res = json.load(f)
        f.close()
    return res


class BasicGoogleAPICalls(unittest.TestCase):
    project = "mock_project"
    zone = "mock_us_central1_a"
    instance = "mock_instance_legacy"
    boot_disk = "mock_boot_disk"
    target_network = "mock_target_network"
    target_subnetwork = "mock_target_subnetwork"
    instance_template = {
        "mock_instance_template": "mocking"}

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

    def test_wait_for_operation_success(self):
        request_builder = RequestMockBuilder(
            {
                "compute.zoneOperations.get": (
                    self.successResponse, '{"status": "DONE"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        wait_response = wait_for_operation(compute, self.project, self.zone, {})

        self.assertEqual(
            wait_response,
            {
                "status": "DONE"}
        )

    def test_wait_for_operation_failure(self):
        request_builder = RequestMockBuilder(
            {
                "compute.zoneOperations.get": (
                    self.errorResponse, b'Invalid Resource')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        with self.assertRaises(HttpError):
            wait_for_operation(compute, self.project, self.zone, {})


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
    def test_basic_waiting(self):
        request_builder = RequestMockBuilder(
            {
                "compute.zoneOperations.get": (
                    self.successResponse,
                    '{"status":"RUNNING"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        with self.assertRaises(StopIteration):
            wait_for_operation(compute, self.project,
                               self.zone, {})

    def test_error_in_response(self):
        request_builder = RequestMockBuilder(
            {
                "compute.zoneOperations.get": (
                    self.successResponse,
                    '{"status":"DONE", "error":"something wrong"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        with self.assertRaises(ZoneOperationsError):
            wait_for_operation(compute, self.project,
                               self.zone, {})


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


class RollBackOriginalInstance(unittest.TestCase):
    project = "mock_project"
    zone = "mock_us_central1_a"
    instance = "mock_instance_legacy"

    http = HttpMock(datafile("compute_rest.json"), {
        "status": "200"})
    errorResponse = httplib2.Response({
        "status": 404,
        "reason": "HttpMock response: the resource is not found"})
    successResponse = httplib2.Response({
        "status": 200,
        "reason": "HttpMock response: Successful"
    })

    def test_basic(self):
        all_disks_info = '[{"deviceName": "mock_disk_0", "boot":true}]'
        request_builder = RequestMockBuilder(
            {
                "compute.instances.attachDisk": (
                    self.successResponse, '{"name": "bar"}'),
                "compute.instances.start": (
                    self.successResponse, '{"name": "bar"}'),
                "compute.zoneOperations.get": (
                    self.successResponse,
                    '{"status":"DONE"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        roll_back_result = roll_back_original_instance(compute, self.project,
                                                       self.zone,
                                                       self.instance,
                                                       all_disks_info)
        self.assertIsNone(roll_back_result)

    def test_multiple_disks(self):
        all_disks_info = '[{"deviceName": "mock_disk_0", "boot":true}]'
        request_builder = RequestMockBuilder(
            {
                "compute.instances.attachDisk": (
                    self.successResponse, '{"name": "bar"}'),
                "compute.instances.start": (
                    self.successResponse, '{"name": "bar"}'),
                "compute.zoneOperations.get": (
                    self.successResponse,
                    '{"status":"DONE"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        roll_back_result = roll_back_original_instance(compute, self.project,
                                                       self.zone,
                                                       self.instance,
                                                       all_disks_info)
        self.assertIsNone(roll_back_result)

    def test_attach_disk_failed(self):
        all_disks_info = '[{"deviceName": "mock_disk_0", "boot":true},' \
                         '{"deviceName": "mock_disk_1", "boot": false}]'
        request_builder = RequestMockBuilder(
            {
                "compute.instances.attachDisk": (
                    self.errorResponse, b'Unable to attach disk.'),
                "compute.instances.start": (
                    self.successResponse, '{"name": "bar"}'),
                "compute.zoneOperations.get": (
                    self.successResponse,
                    '{"status":"DONE"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        try:
            roll_back_original_instance(compute, self.project, self.zone,
                                        self.instance, all_disks_info)
        except HttpError as e:
            self.assertEqual(e.resp.status, 404)

    def test_start_instance_failed(self):
        all_disks_info = '[{"deviceName": "mock_disk_0", "boot":true}]'
        request_builder = RequestMockBuilder(
            {
                "compute.instances.attachDisk": (
                    self.successResponse, '{"name": "bar"}'),
                "compute.instances.start": (
                    self.errorResponse, b'Unable to attach disk.'),
                "compute.zoneOperations.get": (
                    self.successResponse,
                    '{"status":"DONE"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        try:
            roll_back_original_instance(compute, self.project, self.zone,
                                        self.instance, all_disks_info)
        except HttpError as e:
            self.assertEqual(e.resp.status, 404)

    def test_zone_operation_failed(self):
        all_disks_info = '[{"deviceName": "mock_disk_0", "boot":true}]'
        request_builder = RequestMockBuilder(
            {
                "compute.instances.attachDisk": (
                    self.successResponse, '{"name": "bar"}'),
                "compute.instances.start": (
                    self.successResponse, '{"name": "bar"}'),
                "compute.zoneOperations.get": (
                    self.errorResponse,
                    b'Invalid input')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)

        try:
            roll_back_original_instance(compute, self.project, self.zone,
                                        self.instance, all_disks_info)
        except HttpError as e:
            self.assertEqual(e.resp.status, 404)

@patch("vm_network_migration.roll_back_original_instance") # index: 10
@patch("vm_network_migration.attach_disk")  # index: 9
@patch("vm_network_migration.delete_instance")  # index: 8
@patch("vm_network_migration.create_instance")  # index: 7
@patch("vm_network_migration.get_network")  # index: 6
@patch("vm_network_migration.get_zone")  # index: 5
@patch("vm_network_migration.detach_disk")  # index: 4
@patch("vm_network_migration.retrieve_instance_template")  # index: 3
@patch("vm_network_migration.wait_for_operation")  # index: 2
@patch("vm_network_migration.stop_instance")  # index: 1
@patch("google.auth.default")  # index 0
class MainFlow(unittest.TestCase):
    MOCK_CREDENTIALS = mock.Mock(spec=google.auth.credentials.Credentials)

    project = "mock_project"
    zone = "mock_us_central1_a"

    def test_basic(self, *mocks):
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = read_json_file("sample_instance_template.json")
        mocks[6].return_value = read_json_file("sample_auto_mode_network.json")

        original_instance = "mock_original_instance"
        new_instance = "mock_new_instance"
        target_network = "mock_target_network"
        target_subnetwork = "mock_target_subnetwork"
        self.assertIsNone(main(self.project, self.zone, new_instance, original_instance,
             target_network, target_subnetwork))

    def test_unchanged_instance_name(self, *mocks):
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = read_json_file("sample_instance_template.json")
        mocks[6].return_value = read_json_file("sample_auto_mode_network.json")

        original_instance = "instance_1"
        new_instance = "instance_1"
        target_network = "mock_target_network"
        target_subnetwork = "mock_target_subnetwork"

        with self.assertRaises(UnchangedInstanceNameError):
            main(self.project, self.zone, original_instance, new_instance,
                 target_network, target_subnetwork)

    def test_new_instance_name_already_exists_in_project(self, *mocks):
        """The new instance name has existed in the project. The migration will be termintated and a rollback procedure will be called."""
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = read_json_file("sample_instance_template.json")
        mocks[6].return_value = read_json_file("sample_auto_mode_network.json")
        errorResponse = httplib2.Response({
            "status": 404,
            "reason": "HttpMock response: the resource is not found"})
        mocks[7].side_effect = HttpError(resp=errorResponse, content=b'')

        original_instance = "original_instance"
        new_instance = "new_instance"
        target_network = "mock_target_network"
        target_subnetwork = "mock_target_subnetwork"

        main(self.project, self.zone, original_instance, new_instance,
             target_network, target_subnetwork)
        mocks[10].assert_called()

    def test_migrating_to_legacy_network(self, *mocks):
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = read_json_file("sample_instance_template.json")
        mocks[6].return_value = read_json_file("sample_legacy_network.json")

        original_instance = "original_instance"
        new_instance = "new_instance"
        target_network = "mock_target_network"
        target_subnetwork = "mock_target_subnetwork"

        with self.assertRaises(InvalidTargetNetworkError):
            main(self.project, self.zone, original_instance, new_instance,
                 target_network, target_subnetwork)

    def test_invalid_vpc_network(self, *mocks):
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = read_json_file("sample_instance_template.json")
        errorResponse = httplib2.Response({
            "status": 404,
            "reason": "HttpMock response: invalid network"})
        mocks[6].side_effect = HttpError(resp=errorResponse, content=b'')

        original_instance = "original_instance"
        new_instance = "new_instance"
        target_network = "mock_target_network"
        target_subnetwork = "mock_target_subnetwork"

        with self.assertRaises(HttpError):
            main(self.project, self.zone, original_instance, new_instance,
                 target_network, target_subnetwork)

    def test_invalid_subnetwork_for_any_network_mode(self, *mocks):
        """The subnetwork doesn't exist. The migration will be termintated and a rollback procedure will be called. """
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = read_json_file("sample_instance_template.json")
        mocks[6].return_value = read_json_file("sample_auto_mode_network.json")
        errorResponse = httplib2.Response({
            "status": 404,
            "reason": "HttpMock response: the subnetwork doens't exist"})
        mocks[7].side_effect = HttpError(resp=errorResponse, content=b'')

        original_instance = "original_instance"
        new_instance = "new_instance"
        target_network = "mock_target_network"
        target_subnetwork = "mock_target_subnetwork"


        main(self.project, self.zone, original_instance, new_instance,
             target_network, target_subnetwork)
        mocks[10].assert_called()

    def test_auto_network_with_no_subnetwork_specified(self, *mocks):
        """The subnetwork is not specified, and the network is in auto mode """
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = read_json_file("sample_instance_template.json")
        mocks[6].return_value = read_json_file("sample_auto_mode_network.json")

        original_instance = "original_instance"
        new_instance = "new_instance"
        target_network = "mock_target_network"
        target_subnetwork = None

        self.assertIsNone(main(self.project, self.zone, original_instance, new_instance,
             target_network, target_subnetwork))

    def test_non_auto_network_with_no_subnetwork_specified(self, *mocks):
        """No specified subnetwork with a non-auto VPC network"""
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = read_json_file("sample_instance_template.json")
        mocks[6].return_value = read_json_file("sample_non_auto_mode_network.json")

        original_instance = "original_instance"
        new_instance = "new_instance"
        target_network = "mock_target_network"
        target_subnetwork = None

        with self.assertRaises(MissingSubnetworkError):
            main(self.project, self.zone, original_instance, new_instance,
                 target_network, target_subnetwork)

    def test_original_instance_with_no_disks(self, *mocks):
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = read_json_file("sample_instance_template_with_no_disks.json")
        mocks[6].return_value = read_json_file("sample_non_auto_mode_network.json")

        original_instance = "original_instance"
        new_instance = "new_instance"
        target_network = "mock_target_network"
        target_subnetwork = "mock_target_network"

        with self.assertRaises(AttributeNotExistError):
            main(self.project, self.zone, original_instance, new_instance,
                 target_network, target_subnetwork)


