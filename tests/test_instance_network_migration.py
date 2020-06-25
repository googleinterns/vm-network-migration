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
Test instance_network_migration.py
"""

from unittest.mock import patch

import httplib2
import mock
import unittest2 as unittest
from googleapiclient.discovery import build
from googleapiclient.http import HttpMock
from googleapiclient.http import RequestMockBuilder
from utils import *
from vm_network_migration.instance import (
    InstanceStatus,
)
from vm_network_migration.instance_network_migration import InstanceNetworkMigration
from vm_network_migration.subnet_network import SubnetNetwork
from vm_network_migration.vm_network_migration import *


@patch(
    "vm_network_migration.instance_network_migration.InstanceNetworkMigration.set_compute_engine")  # index 0
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
        instance_network_migration = InstanceNetworkMigration(self.project,
                                                              self.zone)
        region = instance_network_migration.get_region()
        self.assertEqual(region, "mock_region")

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


class TestRollbackOriginalInstance(unittest.TestCase):

    def test_rollback_without_original_instance_template(self):
        instance_network_migration = mock.MagicMock()
        instance_network_migration.original_instance.instance_template = None
        InstanceNetworkMigration.rollback_original_instance(
            instance_network_migration)
        instance_network_migration.get_instance_status.assert_not_called()

    def test_rollback_with_running_instance(self):
        instance_network_migration = mock.MagicMock()
        instance_network_migration.original_instance.instance_template = "mock_template"
        instance_network_migration.original_instance.get_instance_status.return_value = InstanceStatus.RUNNING
        InstanceNetworkMigration.rollback_original_instance(
            instance_network_migration)

        instance_network_migration.original_instance.create_instance.assert_not_called()
        instance_network_migration.original_instance.attach_disks.assert_not_called()

    def test_rollback_with_deleted_instance(self):
        instance_network_migration = mock.MagicMock()
        instance_network_migration.original_instance.instance_template = "mock_template"
        instance_network_migration.original_instance.get_instance_status.return_value = InstanceStatus.NOTEXISTS
        InstanceNetworkMigration.rollback_original_instance(
            instance_network_migration)
        instance_network_migration.original_instance.create_instance.assert_called()

    def test_rollback_with_terminated_instance(self):
        instance_network_migration = mock.MagicMock()
        instance_network_migration.original_instance.instance_template = "mock_template"
        instance_network_migration.original_instance.get_instance_status.return_value = InstanceStatus.TERMINATED
        InstanceNetworkMigration.rollback_original_instance(
            instance_network_migration)
        instance_network_migration.original_instance.create_instance.assert_not_called()
        instance_network_migration.original_instance.attach_disks.assert_called()
        instance_network_migration.original_instance.start_instance.assert_called()


class TestRollbackFailureProtection(unittest.TestCase):
    def test_rollback_success(self):
        instance_network_migration = mock.MagicMock()
        instance_network_migration.rollback_original_instance.side_effect = None
        rollback_result = InstanceNetworkMigration.rollback_failure_protection(
            instance_network_migration)
        self.assertTrue(rollback_result)

    def test_rollback_failure(self):
        instance_network_migration = mock.MagicMock()
        instance_network_migration.rollback_original_instance.side_effect = Exception
        rollback_result = InstanceNetworkMigration.rollback_failure_protection(
            instance_network_migration)
        self.assertFalse(rollback_result)


class TestGenerateAddress(unittest.TestCase):

    def test_generate_address(self):
        instance_network_migration = mock.MagicMock()
        instance_template = read_json_file("sample_instance_template.json")
        address = InstanceNetworkMigration.generate_address(
            instance_network_migration, instance_template)
        self.assertEqual(address.project, instance_network_migration.project)
        self.assertEqual(address.region, instance_network_migration.region)
        self.assertEqual(address.external_ip,
                         instance_template['networkInterfaces'][0][
                             'accessConfigs'][0]['natIP'])

    def test_generate_address_no_external_ip(self):
        instance_network_migration = mock.MagicMock()
        instance_template = read_json_file(
            "sample_instance_template_no_external_ip.json")
        address = InstanceNetworkMigration.generate_address(
            instance_network_migration, instance_template)
        self.assertEqual(address.project, instance_network_migration.project)
        self.assertEqual(address.region, instance_network_migration.region)
        self.assertEqual(address.external_ip, None)


class TestGenerateNetwork(unittest.TestCase):

    def test_generate_network(self):
        instance_network_migration = mock.MagicMock()
        SubnetNetwork.check_network_auto_mode = mock.MagicMock()
        network = InstanceNetworkMigration.generate_network(
            instance_network_migration, "mock-network", "mock-subnetwork")
        self.assertEqual(network.network, "mock-network")
        self.assertEqual(network.subnetwork, "mock-subnetwork")


@patch(
    "vm_network_migration.instance_network_migration.InstanceNetworkMigration.rollback_failure_protection")  # index 2
@patch("vm_network_migration.instance.Instance.create_instance")  # index 1
@patch(
    "vm_network_migration.instance_network_migration.InstanceNetworkMigration.set_compute_engine")  # index 0
class TestNetworkMigration(unittest.TestCase):
    def setUp(self) -> None:
        self.project = "mock_project"
        self.zone = "mock_us_central1_a"
        self.http = HttpMock(datafile("compute_rest.json"), {
            "status": "200"})

    def test_migrate_without_preserving_ip(self, *mocks):
        instance_template = read_json_file(
            "sample_instance_template_legacy_network.json")
        network_template = read_json_file("sample_auto_mode_network.json")
        request_builder = build_request_builder(instance_template,
                                                network_template)
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        mocks[0].return_value = compute

        instance_network_migration = InstanceNetworkMigration(self.project,
                                                              self.zone)
        instance_network_migration.new_instance = mock.MagicMock()
        instance_network_migration.network_migration("original-instance",
                                                     "new-instance",
                                                     "mock-network",
                                                     "mock-subnetwork", False)
        new_instance_template = instance_network_migration.new_instance.instance_template
        self.assertEqual(new_instance_template["name"], "new-instance")
        self.assertTrue(
            "mock-network" in new_instance_template['networkInterfaces'][0][
                'network'])
        self.assertTrue(
            "mock-subnetwork" in new_instance_template['networkInterfaces'][0][
                'subnetwork'])
        self.assertFalse(
            "accessConfigs" in new_instance_template['networkInterfaces'][0])
        instance_network_migration.new_instance.create_instance.assert_called()
        mocks[2].assert_not_called()

    def test_migrate_no_external_ip_instance_without_preserving_ip(self,
                                                                   *mocks):
        instance_template = read_json_file(
            "sample_instance_template_no_external_ip.json")
        network_template = read_json_file("sample_auto_mode_network.json")
        request_builder = build_request_builder(instance_template,
                                                network_template)

        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        mocks[0].return_value = compute

        instance_network_migration = InstanceNetworkMigration(self.project,
                                                              self.zone)
        instance_network_migration.new_instance = mock.MagicMock()
        instance_network_migration.network_migration("original-instance",
                                                     "new-instance",
                                                     "mock-network",
                                                     "mock-subnetwork", False)
        new_instance_template = instance_network_migration.new_instance.instance_template
        self.assertEqual(new_instance_template["name"], "new-instance")
        self.assertTrue(
            "mock-network" in new_instance_template['networkInterfaces'][0][
                'network'])
        self.assertTrue(
            "mock-subnetwork" in new_instance_template['networkInterfaces'][0][
                'subnetwork'])
        self.assertFalse(
            'accessConfigs' in new_instance_template['networkInterfaces'][0])
        instance_network_migration.new_instance.create_instance.assert_called()
        mocks[2].assert_not_called()

    def test_migrate_with_preserving_ip(self, *mocks):
        instance_template = read_json_file(
            "sample_instance_template_legacy_network.json")
        network_template = read_json_file("sample_auto_mode_network.json")
        request_builder = build_request_builder(instance_template,
                                                network_template)

        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        mocks[0].return_value = compute

        instance_network_migration = InstanceNetworkMigration(self.project,
                                                              self.zone)
        instance_network_migration.new_instance = mock.MagicMock()
        instance_network_migration.network_migration("original-instance",
                                                     "new-instance",
                                                     "mock-network",
                                                     "mock-subnetwork", True)
        new_instance_template = instance_network_migration.new_instance.instance_template
        self.assertEqual(new_instance_template["name"], "new-instance")
        self.assertTrue(
            "mock-network" in new_instance_template['networkInterfaces'][0][
                'network'])
        self.assertTrue(
            "mock-subnetwork" in new_instance_template['networkInterfaces'][0][
                'subnetwork'])
        self.assertEqual(
            new_instance_template['networkInterfaces'][0]['accessConfigs'],
            instance_template['networkInterfaces'][0]['accessConfigs'])
        instance_network_migration.new_instance.create_instance.assert_called()
        mocks[2].assert_not_called()

    def test_migrate_no_external_ip_instance_with_preserving_ip(self, *mocks):
        instance_template = read_json_file(
            "sample_instance_template_no_external_ip.json")
        network_template = read_json_file("sample_auto_mode_network.json")
        request_builder = build_request_builder(instance_template,
                                                network_template)
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        mocks[0].return_value = compute

        instance_network_migration = InstanceNetworkMigration(self.project,
                                                              self.zone)
        instance_network_migration.new_instance = mock.MagicMock()
        instance_network_migration.network_migration("original-instance",
                                                     "new-instance",
                                                     "mock-network",
                                                     "mock-subnetwork", True)
        new_instance_template = instance_network_migration.new_instance.instance_template
        self.assertEqual(new_instance_template["name"], "new-instance")
        self.assertTrue(
            "mock-network" in new_instance_template['networkInterfaces'][0][
                'network'])
        self.assertTrue(
            "mock-subnetwork" in new_instance_template['networkInterfaces'][0][
                'subnetwork'])
        self.assertFalse(
            'accessConfigs' in new_instance_template['networkInterfaces'][0])

        instance_network_migration.new_instance.create_instance.assert_called()
        mocks[2].assert_not_called()

    def test_preserving_a_static_ip(self, *mocks):
        instance_template = read_json_file(
            "sample_instance_template_legacy_network.json")
        network_template = read_json_file("sample_auto_mode_network.json")
        request_builder = build_request_builder(instance_template,
                                                network_template)
        errorResponse = httplib2.Response({
            "status": 404,
            "reason": "HttpMock response: the IP address already exists"})
        request_builder.responses["compute.addresses.insert"] = (
            errorResponse, b'')
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        mocks[0].return_value = compute

        instance_network_migration = InstanceNetworkMigration(self.project,
                                                              self.zone)
        instance_network_migration.new_instance = mock.MagicMock()

        instance_network_migration.network_migration("original-instance",
                                                     "new-instance",
                                                     "mock-network",
                                                     "mock-subnetwork", True)
        new_instance_template = instance_network_migration.new_instance.instance_template
        self.assertEqual(new_instance_template["name"], "new-instance")
        self.assertTrue(
            "mock-network" in new_instance_template['networkInterfaces'][0][
                'network'])
        self.assertTrue(
            "mock-subnetwork" in new_instance_template['networkInterfaces'][0][
                'subnetwork'])
        self.assertEqual(
            new_instance_template['networkInterfaces'][0]['accessConfigs'],
            instance_template['networkInterfaces'][0]['accessConfigs'])
        instance_network_migration.new_instance.create_instance.assert_called()
        mocks[2].assert_not_called()

    def test_unchanged_new_instance_name(self, *mocks):
        instance_template = read_json_file(
            "sample_instance_template_legacy_network.json")
        network_template = read_json_file("sample_auto_mode_network.json")
        request_builder = build_request_builder(instance_template,
                                                network_template)
        successResponse = httplib2.Response({
            "status": 200,
            "reason": "H"})
        request_builder.responses["compute.networks.get"] = (
            successResponse, b'')
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
        instance_template = read_json_file(
            "sample_instance_template_legacy_network.json")
        network_template = read_json_file("sample_auto_mode_network.json")
        request_builder = build_request_builder(instance_template,
                                                network_template)
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
        self.assertTrue(
            "mock-network" in new_instance_template['networkInterfaces'][0][
                'network'])
        self.assertTrue(
            "mock-network" in new_instance_template['networkInterfaces'][0][
                'subnetwork'])
        self.assertFalse(
            'accessConfigs' in new_instance_template['networkInterfaces'][0])
        instance_network_migration.new_instance.create_instance.assert_called()
        mocks[2].assert_not_called()

    def test_no_subnetwork_in_non_auto_network_mode(self, *mocks):
        instance_template = read_json_file(
            "sample_instance_template_legacy_network.json")
        network_template = read_json_file("sample_non_auto_mode_network.json")
        request_builder = build_request_builder(instance_template,
                                                network_template)
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
