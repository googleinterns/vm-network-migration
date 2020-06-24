import json
import os
from unittest.mock import patch

import httplib2
import unittest2 as unittest
from googleapiclient.discovery import build
from googleapiclient.http import HttpMock
from googleapiclient.http import RequestMockBuilder
from vm_network_migration.instance import (
    Instance,
    InstanceStatus,
)
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
    project = "mock_project"
    zone = "mock_us_central1_a"
    instance_name = "mock_instance"
    region = "mock_us_central1"

    def test_basic(self):
        instance = Instance("", self.project, self.instance_name,
                            self.region, self.zone, {
                                "disks": ["disk1", "disk2"]})
        disks = instance.get_disks_info_from_instance_template()
        self.assertEqual(disks, ["disk1", "disk2"])

    def test_no_disks(self):
        instance = Instance("", self.project, self.instance_name,
                            self.region, self.zone, {})
        with self.assertRaises(AttributeNotExistError):
            instance.get_disks_info_from_instance_template()


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


class TestModifyInstanceTemplateWithNewName(unittest.TestCase):
    project = "mock_project"
    zone = "mock_us_central1_a"
    instance_name = "mock_instance"
    region = "mock_us_central1"

    def test_basic(self):
        instance = Instance("", self.project, self.instance_name,
                            self.region, self.zone, {
                                "name": "origin-instance"})
        instance.modify_instance_template_with_new_name("new-instance")
        self.assertEqual(instance.instance_template["name"], "new-instance")


class TestModifyInstanceTemplateWithNewNetwork(unittest.TestCase):
    project = "mock_project"
    zone = "mock_us_central1_a"
    instance_name = "mock_instance"
    region = "mock_us_central1"

    def test_basic(self):
        instance_template = read_json_file(
            "sample_instance_template.json")
        instance = Instance("", self.project, self.instance_name,
                            self.region, self.zone, instance_template)
        new_network_link = "new_network_link"
        new_subnetwork_link = "new_subnetwork_link"
        instance.modify_instance_template_with_new_network(new_network_link,
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
        instance = Instance("", self.project, self.instance_name,
                            self.region, self.zone, instance_template)
        new_network_link = "new_network_link"
        new_subnetwork_link = "new_subnetwork_link"
        instance.modify_instance_template_with_new_network(new_network_link,
                                                           new_subnetwork_link)
        self.assertEqual(
            instance.instance_template['networkInterfaces'][0]['network'],
            new_network_link)
        self.assertEqual(
            instance.instance_template['networkInterfaces'][0]['subnetwork'],
            new_subnetwork_link)


class TestModifyInstanceTemplateWithExternalIp(unittest.TestCase):
    project = "mock_project"
    zone = "mock_us_central1_a"
    instance_name = "mock_instance"
    region = "mock_us_central1"

    def test_external_ip_is_none(self):
        instance_template = read_json_file(
            "sample_instance_template_legacy_network.json")
        instance = Instance("", self.project, self.instance_name,
                            self.region, self.zone, instance_template)

        instance.modify_instance_template_with_external_ip(None)
        self.assertFalse(
            "accessConfigs" in instance.instance_template['networkInterfaces'][
                0])
        self.assertFalse(
            "networkIP" in instance_template['networkInterfaces'][0])

        instance.instance_template = read_json_file(
            "sample_instance_template_no_external_ip.json")
        instance.modify_instance_template_with_external_ip(None)
        self.assertFalse(
            "accessConfigs" in instance.instance_template['networkInterfaces'][
                0])
        self.assertFalse(
            "networkIP" in instance_template['networkInterfaces'][0])

        instance.instance_template = read_json_file(
            "sample_instance_template_no_natIP.json")
        instance.modify_instance_template_with_external_ip(None)
        self.assertFalse(
            "accessConfigs" in instance.instance_template['networkInterfaces'][
                0])
        self.assertFalse(
            "networkIP" in instance_template['networkInterfaces'][0])

    def test_external_ip_not_none(self):
        mock_ip = "125.125.125.125"
        instance_template = read_json_file(
            "sample_instance_template_legacy_network.json")
        instance = Instance("", self.project, self.instance_name,
                            self.region, self.zone, instance_template)

        instance.modify_instance_template_with_external_ip(mock_ip)
        self.assertTrue(
            instance.instance_template['networkInterfaces'][0]['accessConfigs'][
                0]['natIP'], mock_ip)
        self.assertFalse(
            "networkIP" in instance_template['networkInterfaces'][0])

        instance.instance_template = read_json_file(
            "sample_instance_template_no_external_ip.json")

        instance.modify_instance_template_with_external_ip(mock_ip)
        self.assertTrue(
            instance.instance_template['networkInterfaces'][0]['accessConfigs'][
                0]['natIP'], mock_ip)
        self.assertFalse(
            "networkIP" in instance_template['networkInterfaces'][0])

        instance.instance_template = read_json_file(
            "sample_instance_template_no_natIP.json")

        instance.modify_instance_template_with_external_ip(mock_ip)
        self.assertTrue(
            instance.instance_template['networkInterfaces'][0]['accessConfigs'][
                0]['natIP'], mock_ip)
        self.assertFalse(
            "networkIP" in instance_template['networkInterfaces'][0])


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


@patch(
    "vm_network_migration.instance.Instance.retrieve_instance_template")  # index 0
class TestGetInstanceStatus(unittest.TestCase):
    project = "mock_project"
    zone = "mock_us_central1_a"
    instance_name = "mock_instance"
    region = "mock_us_central1"

    def test_instance_with_status_running(self, *mocks):
        mocks[0].return_value = {
            "status": "RUNNING"}
        instance = Instance("", self.project, self.instance_name,
                            self.region, self.zone)
        instance_status = instance.get_instance_status()
        self.assertEqual(instance_status.name, InstanceStatus.RUNNING.name)

    def test_instance_with_status_stopping(self, *mocks):
        mocks[0].return_value = {
            "status": "STOPPING"}
        instance = Instance("", self.project, self.instance_name,
                            self.region, self.zone)
        instance_status = instance.get_instance_status()
        self.assertEqual(instance_status.name, InstanceStatus.STOPPING.name)

    def test_instance_with_status_terminated(self, *mocks):
        mocks[0].return_value = {
            "status": "TERMINATED"}
        instance = Instance("", self.project, self.instance_name,
                            self.region, self.zone)
        instance_status = instance.get_instance_status()
        self.assertEqual(instance_status.name, InstanceStatus.TERMINATED.name)

    def test_instance_with_status_delete(self, *mocks):
        errorResponse = httplib2.Response({
            "status": 400})
        errorResponse.reason = "HttpMock response: instance is not found"
        mocks[0].side_effect = HttpError(resp=errorResponse, content=b'')
        instance = Instance("", self.project, self.instance_name,
                            self.region, self.zone)
        instance_status = instance.get_instance_status()
        self.assertEqual(instance_status.name, InstanceStatus.NOTEXISTS.name)

    def test_instance_with_other_http_error(self, *mocks):
        errorResponse = httplib2.Response({
            "status": 400})
        mocks[0].side_effect = HttpError(resp=errorResponse, content=b'')
        instance = Instance("", self.project, self.instance_name,
                            self.region, self.zone)
        with self.assertRaises(HttpError):
            instance.get_instance_status()
