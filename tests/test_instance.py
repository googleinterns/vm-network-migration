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
Test instance.py
"""

from unittest.mock import patch

import httplib2
import mock
import unittest2 as unittest
from googleapiclient.discovery import build
from googleapiclient.http import HttpMock
from googleapiclient.http import RequestMockBuilder
from utils import *
from googleapiclient.http import HttpError
from vm_network_migration.errors import *
from vm_network_migration.instance import (
    Instance,
    InstanceStatus,
)


class TestRetrieveInstanceTemplate(unittest.TestCase):
    project = "mock_project"
    zone = "mock_us_central1_a"
    instance_name = "mock_instance"
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

    def test_retrieve_instance_template_success(self):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.get": (
                    self.successResponse, '{"status": "DONE"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        instance = Instance(compute, self.project, self.instance_name,
                            self.region, self.zone)
        retrieve_instance_template_operation = instance.retrieve_instance_template()

        self.assertEqual(
            retrieve_instance_template_operation,
            {
                "status": "DONE"}
        )
        self.assertEqual(instance.instance_template, {
            "status": "DONE"})

    def test_retrieve_instance_template_failure(self):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.get": (
                    self.errorResponse, b'{"status": "DONE"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        instance = Instance(compute, self.project, self.instance_name,
                            self.region, self.zone)
        with self.assertRaises(HttpError):
            instance.retrieve_instance_template()
        self.assertIsNone(instance.instance_template)


@patch(
    "vm_network_migration.operations.Operations.wait_for_zone_operation")  # index 0
class TestStartInstance(unittest.TestCase):
    project = "mock_project"
    zone = "mock_us_central1_a"
    instance_name = "mock_instance"
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

    def test_retrieve_instance_template_success(self, *mocks):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.start": (
                    self.successResponse, '{"name": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        instance = Instance(compute, self.project, self.instance_name,
                            self.region, self.zone)
        start_instance_operation = instance.start_instance()

        self.assertEqual(
            start_instance_operation,
            {
                "name": "bar"}
        )

    def test_start_instance_failure(self, *mocks):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.start": (
                    self.errorResponse, b'{"name": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        instance = Instance(compute, self.project, self.instance_name,
                            self.region, self.zone)

        with self.assertRaises(HttpError):
            instance.start_instance()


@patch(
    "vm_network_migration.operations.Operations.wait_for_zone_operation")  # index 0
class TestStopInstance(unittest.TestCase):
    project = "mock_project"
    zone = "mock_us_central1_a"
    instance_name = "mock_instance"
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

    def test_retrieve_instance_template_success(self, *mocks):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.stop": (
                    self.successResponse, '{"name": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        instance = Instance(compute, self.project, self.instance_name,
                            self.region, self.zone)
        stop_instance_operation = instance.stop_instance()

        self.assertEqual(
            stop_instance_operation,
            {
                "name": "bar"}
        )

    def test_start_instance_failure(self, *mocks):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.stop": (
                    self.errorResponse, b'{"name": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        instance = Instance(compute, self.project, self.instance_name,
                            self.region, self.zone)

        with self.assertRaises(HttpError):
            instance.stop_instance()


class TestGetDisksInfoFromInstanceTemplate(unittest.TestCase):

    def test_basic(self):
        instance = mock.MagicMock()
        instance.instance_template = read_json_file(
            "sample_instance_template.json")
        disks = Instance.get_disks_info_from_instance_template(instance)
        self.assertEqual(disks, instance.instance_template['disks'])

    def test_no_disks(self):
        instance = mock.MagicMock()
        instance.instance_template = read_json_file(
            "sample_instance_template_with_no_disks.json")
        with self.assertRaises(AttributeNotExistError):
            Instance.get_disks_info_from_instance_template(instance)


@patch(
    "vm_network_migration.operations.Operations.wait_for_zone_operation")  # index 0
class TestDetachDisk(unittest.TestCase):
    project = "mock_project"
    zone = "mock_us_central1_a"
    instance_name = "mock_instance"
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

    def test_detach_disk_success(self, *mocks):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.detachDisk": (
                    self.successResponse, '{"name": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        instance = Instance(compute, self.project, self.instance_name,
                            self.region, self.zone)
        detach_disk_operation = instance.detach_disk("mock-disk")

        self.assertEqual(
            detach_disk_operation,
            {
                "name": "bar"}
        )

    def test_detach_disk_failure(self, *mocks):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.detachDisk": (
                    self.errorResponse, b'{"name": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        instance = Instance(compute, self.project, self.instance_name,
                            self.region, self.zone)

        with self.assertRaises(HttpError):
            instance.detach_disk("mock-disk")


class TestDetachDisks(unittest.TestCase):
    def test_basic(self):
        instance = mock.MagicMock()
        disks = [{
                     "deviceName": 1}, {
                     "deviceName": 2}]
        instance.get_disks_info_from_instance_template.return_value = disks
        Instance.detach_disks(instance)
        self.assertEqual(instance.detach_disk.call_count, len(disks))


@patch(
    "vm_network_migration.operations.Operations.wait_for_zone_operation")  # index 0
class TestAttachDisk(unittest.TestCase):
    project = "mock_project"
    zone = "mock_us_central1_a"
    instance_name = "mock_instance"
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

    def test_attach_disk_success(self, *mocks):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.attachDisk": (
                    self.successResponse, '{"name": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        instance = Instance(compute, self.project, self.instance_name,
                            self.region, self.zone)
        attach_disk_operation = instance.attach_disk("mock-disk")

        self.assertEqual(
            attach_disk_operation,
            {
                "name": "bar"}
        )

    def test_attach_disk_failure(self, *mocks):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.attachDisk": (
                    self.errorResponse, b'{"name": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        instance = Instance(compute, self.project, self.instance_name,
                            self.region, self.zone)

        with self.assertRaises(HttpError):
            instance.attach_disk("mock-disk")


class TestAttachDisks(unittest.TestCase):
    def test_basic(self):
        instance = mock.MagicMock()
        disks = [{
                     "deviceName": 1}, {
                     "deviceName": 2}]
        instance.get_disks_info_from_instance_template.return_value = disks
        Instance.attach_disks(instance)
        self.assertEqual(instance.attach_disk.call_count, len(disks))


class TestModifyInstanceTemplateWithNewName(unittest.TestCase):
    def test_basic(self):
        instance = mock.MagicMock()
        instance.instance_template = {
            "name": "original-instance"}
        Instance.modify_instance_template_with_new_name(instance,
                                                        "new-instance")
        self.assertEqual(instance.instance_template["name"], "new-instance")


class TestModifyInstanceTemplateWithNewNetwork(unittest.TestCase):

    def test_instance_with_subnet(self):
        instance_template = read_json_file(
            "sample_instance_template.json")

        instance = mock.MagicMock()
        instance.instance_template = instance_template
        new_network_link = "new_network_link"
        new_subnetwork_link = "new_subnetwork_link"
        Instance.modify_instance_template_with_new_network(instance,
                                                           new_network_link,
                                                           new_subnetwork_link)
        self.assertEqual(
            instance.instance_template['networkInterfaces'][0]['network'],
            new_network_link)
        self.assertEqual(
            instance.instance_template['networkInterfaces'][0]['subnetwork'],
            new_subnetwork_link)

    def test_instance_with_legacy_network(self):
        instance_template = read_json_file(
            "sample_instance_template_legacy_network.json")
        instance = mock.MagicMock()
        instance.instance_template = instance_template
        new_network_link = "new_network_link"
        new_subnetwork_link = "new_subnetwork_link"
        Instance.modify_instance_template_with_new_network(instance,
                                                           new_network_link,
                                                           new_subnetwork_link)
        self.assertEqual(
            instance.instance_template['networkInterfaces'][0]['network'],
            new_network_link)
        self.assertEqual(
            instance.instance_template['networkInterfaces'][0]['subnetwork'],
            new_subnetwork_link)


class TestModifyInstanceTemplateWithExternalIp(unittest.TestCase):
    def test_external_ip_is_none(self):
        instance = mock.MagicMock()
        instance.instance_template = read_json_file(
            "sample_instance_template_legacy_network.json")
        Instance.modify_instance_template_with_external_ip(instance, None)
        self.assertFalse(
            "accessConfigs" in instance.instance_template['networkInterfaces'][
                0])
        self.assertFalse(
            "networkIP" in instance.instance_template['networkInterfaces'][0])

        instance.instance_template = read_json_file(
            "sample_instance_template_no_external_ip.json")
        Instance.modify_instance_template_with_external_ip(instance, None)
        self.assertFalse(
            "accessConfigs" in instance.instance_template['networkInterfaces'][
                0])
        self.assertFalse(
            "networkIP" in instance.instance_template['networkInterfaces'][0])

        instance.instance_template = read_json_file(
            "sample_instance_template_no_natIP.json")
        Instance.modify_instance_template_with_external_ip(instance, None)
        self.assertFalse(
            "accessConfigs" in instance.instance_template['networkInterfaces'][
                0])
        self.assertFalse(
            "networkIP" in instance.instance_template['networkInterfaces'][0])

    def test_external_ip_not_none(self):
        mock_ip = "125.125.125.125"
        instance = mock.MagicMock()
        instance.instance_template = read_json_file(
            "sample_instance_template_legacy_network.json")
        Instance.modify_instance_template_with_external_ip(instance, mock_ip)
        self.assertTrue(
            instance.instance_template['networkInterfaces'][0]['accessConfigs'][
                0]['natIP'], mock_ip)
        self.assertFalse(
            "networkIP" in instance.instance_template['networkInterfaces'][0])

        instance.instance_template = read_json_file(
            "sample_instance_template_no_external_ip.json")

        Instance.modify_instance_template_with_external_ip(instance, mock_ip)
        self.assertTrue(
            instance.instance_template['networkInterfaces'][0]['accessConfigs'][
                0]['natIP'], mock_ip)
        self.assertFalse(
            "networkIP" in instance.instance_template['networkInterfaces'][0])

        instance.instance_template = read_json_file(
            "sample_instance_template_no_natIP.json")

        Instance.modify_instance_template_with_external_ip(instance, mock_ip)
        self.assertTrue(
            instance.instance_template['networkInterfaces'][0]['accessConfigs'][
                0]['natIP'], mock_ip)
        self.assertFalse(
            "networkIP" in instance.instance_template['networkInterfaces'][0])


@patch(
    "vm_network_migration.operations.Operations.wait_for_zone_operation")  # index 0
class TestDeleteInstance(unittest.TestCase):
    project = "mock_project"
    zone = "mock_us_central1_a"
    instance_name = "mock_instance"
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

    def test_delete_instance_success(self, *mocks):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.delete": (
                    self.successResponse, '{"name": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        instance = Instance(compute, self.project, self.instance_name,
                            self.region, self.zone)
        delete_instance_operation = instance.delete_instance()

        self.assertEqual(
            delete_instance_operation,
            {
                "name": "bar"}
        )

    def test_delete_instance_failure(self, *mocks):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.delete": (
                    self.errorResponse, b'{"name": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        instance = Instance(compute, self.project, self.instance_name,
                            self.region, self.zone)

        with self.assertRaises(HttpError):
            instance.delete_instance()


@patch(
    "vm_network_migration.operations.Operations.wait_for_zone_operation")  # index 0
class TestCreateInstance(unittest.TestCase):
    project = "mock_project"
    zone = "mock_us_central1_a"
    instance_name = "mock_instance"
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

    def test_create_instance_success(self, *mocks):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.insert": (
                    self.successResponse, '{"name": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        instance = Instance(compute, self.project, self.instance_name,
                            self.region, self.zone)
        create_instance_operation = instance.create_instance()

        self.assertEqual(
            create_instance_operation,
            {
                "name": "bar"}
        )

    def test_create_instance_failure(self, *mocks):
        request_builder = RequestMockBuilder(
            {
                "compute.instances.insert": (
                    self.errorResponse, b'{"name": "bar"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        instance = Instance(compute, self.project, self.instance_name,
                            self.region, self.zone)

        with self.assertRaises(HttpError):
            instance.create_instance()


class TestGetInstanceStatus(unittest.TestCase):

    def test_instance_with_status_running(self):
        instance = mock.MagicMock()
        instance.retrieve_instance_template.return_value = {
            "status": "RUNNING"}
        instance_status = Instance.get_instance_status(instance)
        self.assertEqual(instance_status, InstanceStatus.RUNNING)

    def test_instance_with_status_stopping(self):
        instance = mock.MagicMock()
        instance.retrieve_instance_template.return_value = {
            "status": "STOPPING"}
        instance_status = Instance.get_instance_status(instance)
        self.assertEqual(instance_status, InstanceStatus.STOPPING)

    def test_instance_with_status_terminated(self):
        instance = mock.MagicMock()
        instance.retrieve_instance_template.return_value = {
            "status": "TERMINATED"}
        instance_status = Instance.get_instance_status(instance)
        self.assertEqual(instance_status, InstanceStatus.TERMINATED)

    def test_instance_with_status_delete(self):
        errorResponse = httplib2.Response({
            "status": 400})
        errorResponse.reason = "HttpMock response: instance is not found"
        instance = mock.MagicMock()
        instance.retrieve_instance_template.side_effect = HttpError(
            resp=errorResponse, content=b'')
        instance_status = Instance.get_instance_status(instance)
        self.assertEqual(instance_status, InstanceStatus.NOTEXISTS)

    def test_instance_with_other_http_error(self):
        errorResponse = httplib2.Response({
            "status": 400})
        errorResponse.reason = "HttpMock response: others"
        instance = mock.MagicMock()
        instance.retrieve_instance_template.side_effect = HttpError(
            resp=errorResponse, content=b'')
        with self.assertRaises(HttpError):
            Instance.get_instance_status(instance)
