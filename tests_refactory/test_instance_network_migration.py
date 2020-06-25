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
from vm_network_migration.instance_network_migration import InstanceNetworkMigration
import mock
from google.auth import credentials
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

@patch("vm_network_migration.instance_network_migration.InstanceNetworkMigration.set_compute_engine") # index 0
class TestGetRegion(unittest.TestCase):
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

    def test_get_region_success(self, *mocks):
        request_builder = RequestMockBuilder(
            {
                "compute.zones.get": (
                    self.successResponse, '{"region": "mock_region"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        mocks[0].return_value = compute
        instance_network_migration = InstanceNetworkMigration(self.project, self.zone)
        region = instance_network_migration.get_region()
        self.assertEqual(region, "mock_region")

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

    def test_get_region_failure(self, *mocks):
        request_builder = RequestMockBuilder(
            {
                "compute.zones.get": (
                    self.errorResponse, b'{"region": "mock_region"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        mocks[0].return_value = compute
        with self.assertRaises(HttpError):
            InstanceNetworkMigration(self.project, self.zone)

@patch(
    "vm_network_migration.subnet_network.SubnetNetwork.check_network_auto_mode") # index 2
@patch("vm_network_migration.instance_network_migration.InstanceNetworkMigration.get_region") # index 1
@patch(
    "vm_network_migration.instance_network_migration.InstanceNetworkMigration.set_compute_engine")  # index 0
class TestGenerateAddress(unittest.TestCase):
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

    def test_generate_address(self, *mocks):
        request_builder = RequestMockBuilder({})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        mocks[0].return_value = compute
        mocks[1].return_value = "mock_region"
        instance_network_migration = InstanceNetworkMigration(self.project, self.zone)
        instance_template = read_json_file("sample_instance_template.json")
        address = instance_network_migration.generate_address(instance_template)
        self.assertEqual(address.project, self.project)
        self.assertEqual(address.region, instance_network_migration.region)
        self.assertEqual(address.external_ip, instance_template['networkInterfaces'][0]['accessConfigs'][0]['natIP'])

    def test_generate_network(self, *mocks):
        request_builder = RequestMockBuilder({})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        mocks[0].return_value = compute
        mocks[1].return_value = "mock_region"
        mocks[2].return_value = True

        instance_network_migration = InstanceNetworkMigration(self.project, self.zone)
        network_name = "mock-network"
        subnetwork_name = "mock-subnetwork"
        network = instance_network_migration.generate_network(network_name, subnetwork_name)

        self.assertEqual(network.network, network_name)
        self.assertEqual(network.subnetwork, subnetwork_name)
        self.assertIsNotNone(network.network_link)
        self.assertIsNotNone(network.subnetwork_link)

@patch(
    "vm_network_migration.instance_network_migration.InstanceNetworkMigration.rollback_failure_protection") # index 2
@patch("vm_network_migration.instance.Instance.create_instance") # index 1
@patch(
    "vm_network_migration.instance_network_migration.InstanceNetworkMigration.set_compute_engine")  # index 0
class TestNetworkMigration(unittest.TestCase):
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

    def test_migrate_without_preserving_ip(self, *mocks):
        instance_template = read_json_file("sample_instance_template_legacy_network.json")
        network_template = read_json_file("sample_auto_mode_network.json")
        request_builder = build_request_builder(instance_template, network_template)

        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        mocks[0].return_value = compute

        instance_network_migration = InstanceNetworkMigration(self.project,
                                                              self.zone)
        instance_network_migration.new_instance = mock.MagicMock()
        instance_network_migration.network_migration("original-instance", "new-instance", "mock-network", "mock-subnetwork", False)
        new_instance_template = instance_network_migration.new_instance.instance_template
        self.assertEqual(new_instance_template["name"], "new-instance")
        self.assertTrue("mock-network" in new_instance_template['networkInterfaces'][0]['network'])
        self.assertTrue("mock-subnetwork" in new_instance_template['networkInterfaces'][0]['subnetwork'])
        self.assertFalse("accessConfigs" in new_instance_template['networkInterfaces'][0])
        instance_network_migration.new_instance.create_instance.assert_called()
        mocks[2].assert_not_called()

    def test_migrate_no_external_ip_instance_without_preserving_ip(self, *mocks):
        instance_template = read_json_file("sample_instance_template_no_external_ip.json")
        network_template = read_json_file("sample_auto_mode_network.json")
        request_builder = build_request_builder(instance_template, network_template)

        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        mocks[0].return_value = compute

        instance_network_migration = InstanceNetworkMigration(self.project,
                                                              self.zone)
        instance_network_migration.new_instance = mock.MagicMock()
        instance_network_migration.network_migration("original-instance", "new-instance", "mock-network", "mock-subnetwork", False)
        new_instance_template = instance_network_migration.new_instance.instance_template
        self.assertEqual(new_instance_template["name"], "new-instance")
        self.assertTrue("mock-network" in new_instance_template['networkInterfaces'][0]['network'])
        self.assertTrue("mock-subnetwork" in new_instance_template['networkInterfaces'][0]['subnetwork'])
        self.assertFalse('accessConfigs' in new_instance_template['networkInterfaces'][0])
        instance_network_migration.new_instance.create_instance.assert_called()
        mocks[2].assert_not_called()



    def test_migrate_with_preserving_ip(self, *mocks):
        instance_template = read_json_file("sample_instance_template_legacy_network.json")
        network_template = read_json_file("sample_auto_mode_network.json")
        request_builder = build_request_builder(instance_template, network_template)

        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        mocks[0].return_value = compute

        instance_network_migration = InstanceNetworkMigration(self.project,
                                                              self.zone)
        instance_network_migration.new_instance = mock.MagicMock()
        instance_network_migration.network_migration("original-instance", "new-instance", "mock-network", "mock-subnetwork", True)
        new_instance_template = instance_network_migration.new_instance.instance_template
        self.assertEqual(new_instance_template["name"], "new-instance")
        self.assertTrue("mock-network" in new_instance_template['networkInterfaces'][0]['network'])
        self.assertTrue("mock-subnetwork" in new_instance_template['networkInterfaces'][0]['subnetwork'])
        self.assertEqual(new_instance_template['networkInterfaces'][0]['accessConfigs'], instance_template['networkInterfaces'][0]['accessConfigs'])
        instance_network_migration.new_instance.create_instance.assert_called()
        mocks[2].assert_not_called()

    def test_migrate_no_external_ip_instance_with_preserving_ip(self, *mocks):
        instance_template = read_json_file("sample_instance_template_no_external_ip.json")
        network_template = read_json_file("sample_auto_mode_network.json")
        request_builder = build_request_builder(instance_template, network_template)
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        mocks[0].return_value = compute

        instance_network_migration = InstanceNetworkMigration(self.project,
                                                              self.zone)
        instance_network_migration.new_instance = mock.MagicMock()
        instance_network_migration.network_migration("original-instance", "new-instance", "mock-network", "mock-subnetwork", True)
        new_instance_template = instance_network_migration.new_instance.instance_template
        self.assertEqual(new_instance_template["name"], "new-instance")
        self.assertTrue("mock-network" in new_instance_template['networkInterfaces'][0]['network'])
        self.assertTrue("mock-subnetwork" in new_instance_template['networkInterfaces'][0]['subnetwork'])
        self.assertFalse('accessConfigs' in new_instance_template['networkInterfaces'][0])

        instance_network_migration.new_instance.create_instance.assert_called()
        mocks[2].assert_not_called()


    def test_preserving_a_static_ip(self, *mocks):
        instance_template = read_json_file("sample_instance_template_legacy_network.json")
        network_template = read_json_file("sample_auto_mode_network.json")
        request_builder = build_request_builder(instance_template, network_template)
        errorResponse = httplib2.Response({
        "status": 404,
        "reason":  "HttpMock response: the IP address already exists"})
        request_builder.responses["compute.addresses.insert"] = (errorResponse, b'')
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        mocks[0].return_value = compute

        instance_network_migration = InstanceNetworkMigration(self.project,
                                                              self.zone)
        instance_network_migration.new_instance = mock.MagicMock()

        instance_network_migration.network_migration("original-instance", "new-instance", "mock-network", "mock-subnetwork", True)
        new_instance_template = instance_network_migration.new_instance.instance_template
        self.assertEqual(new_instance_template["name"], "new-instance")
        self.assertTrue("mock-network" in new_instance_template['networkInterfaces'][0]['network'])
        self.assertTrue("mock-subnetwork" in new_instance_template['networkInterfaces'][0]['subnetwork'])
        self.assertEqual(new_instance_template['networkInterfaces'][0]['accessConfigs'], instance_template['networkInterfaces'][0]['accessConfigs'])
        instance_network_migration.new_instance.create_instance.assert_called()
        mocks[2].assert_not_called()


    def test_unchanged_new_instance_name(self, *mocks):
        instance_template = read_json_file("sample_instance_template_legacy_network.json")
        network_template = read_json_file("sample_auto_mode_network.json")
        request_builder = build_request_builder(instance_template, network_template)
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        mocks[0].return_value = compute

        instance_network_migration = InstanceNetworkMigration(self.project,
                                                              self.zone)
        instance_network_migration.new_instance = mock.MagicMock()


        instance_network_migration.network_migration("original-instance",
                                                     "original-instance",
                                                     "mock-network",
                                                     "mock-subnetwork",
                                                     False)

        instance_network_migration.new_instance.create_instance.assert_not_called()
        mocks[2].assert_called()

    def test_no_subnetwork_in_auto_network_mode(self, *mocks):
        instance_template = read_json_file("sample_instance_template_legacy_network.json")
        network_template = read_json_file("sample_auto_mode_network.json")
        request_builder = build_request_builder(instance_template, network_template)
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        mocks[0].return_value = compute

        instance_network_migration = InstanceNetworkMigration(self.project,
                                                              self.zone)
        instance_network_migration.new_instance = mock.MagicMock()
        instance_network_migration.network_migration("original-instance",
                                                     "new-instance",
                                                     "mock-network",
                                                     None,
                                                     False)

        new_instance_template = instance_network_migration.new_instance.instance_template

        self.assertEqual(new_instance_template["name"], "new-instance")
        self.assertTrue("mock-network" in new_instance_template['networkInterfaces'][0]['network'])
        self.assertTrue("mock-network" in new_instance_template['networkInterfaces'][0]['subnetwork'])
        self.assertFalse('accessConfigs' in new_instance_template['networkInterfaces'][0])
        instance_network_migration.new_instance.create_instance.assert_called()
        mocks[2].assert_not_called()

    def test_no_subnetwork_in_non_auto_network_mode(self, *mocks):
        instance_template = read_json_file("sample_instance_template_legacy_network.json")
        network_template = read_json_file("sample_non_auto_mode_network.json")
        request_builder = build_request_builder(instance_template, network_template)
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        mocks[0].return_value = compute

        instance_network_migration = InstanceNetworkMigration(self.project,
                                                              self.zone)
        instance_network_migration.new_instance = mock.MagicMock()
        instance_network_migration.network_migration("original-instance",
                                                     "new-instance",
                                                     "mock-network",
                                                     None,
                                                     False)
        instance_network_migration.new_instance.create_instance.assert_not_called()
        mocks[2].assert_called()



def build_request_builder(instance_template, target_subnet_network_template):
    successResponse = httplib2.Response({
        "status": 200,
        "reason": "HttpMock response: Successful"
    })

    request_builder = RequestMockBuilder({
        "compute.instances.get": (
            successResponse, json.dumps(instance_template)),
        "compute.zones.get": (
            successResponse, '{"region":"mock-region"}'),
        "compute.networks.get": (
            successResponse,
            json.dumps(target_subnet_network_template)
        ),
        "compute.addresses.insert": (
            successResponse, '{"name": "bar"}'
        ),
        "compute.instances.start": (
            successResponse, '{"name": "bar"}'
        ),
        "compute.instances.stop": (
            successResponse, '{"name": "bar"}'
        ),
        "compute.instances.detachDisk": (
            successResponse, '{"name": "bar"}'
        ),
        "compute.instances.attachDisk": (
            successResponse, '{"name": "bar"}'
        ),
        "compute.instances.insert": (
            successResponse, '{"name": "bar"}'
        ),
        "compute.instances.delete": (
            successResponse, '{"name": "bar"}'
        ),
        "compute.zoneOperations.get": (
            successResponse, '{"status": "DONE"}'
        ),
        "compute.regionOperations.get": (
            successResponse, '{"status": "DONE"}'
        )})

    return request_builder
