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
Test main() function
"""

import json
import os
from unittest import mock
from unittest.mock import patch

import httplib2
import unittest2 as unittest
from googleapiclient.errors import HttpError
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


@patch(
    "vm_network_migration.vm_network_migration.roll_back_original_instance")  # index: 10
@patch("vm_network_migration.vm_network_migration.attach_disk")  # index: 9
@patch("vm_network_migration.vm_network_migration.delete_instance")  # index: 8
@patch("vm_network_migration.vm_network_migration.create_instance")  # index: 7
@patch("vm_network_migration.vm_network_migration.get_network")  # index: 6
@patch("vm_network_migration.vm_network_migration.get_zone")  # index: 5
@patch("vm_network_migration.vm_network_migration.detach_disk")  # index: 4
@patch(
    "vm_network_migration.vm_network_migration.retrieve_instance_template")  # index: 3
@patch(
    "vm_network_migration.vm_network_migration.wait_for_operation")  # index: 2
@patch("vm_network_migration.vm_network_migration.stop_instance")  # index: 1
@patch("google.auth.default")  # index 0
class MainFlowLogic(unittest.TestCase):
    MOCK_CREDENTIALS = mock.Mock(spec=google.auth.credentials.Credentials)
    errorResponse = httplib2.Response({
        "status": 404,
        "reason": "HttpMock response: invalid network"})
    project = "mock_project"
    zone = "mock_us_central1_a"

    def test_basic(self, *mocks):
        original_instance_template = read_json_file(
            "sample_instance_template.json")
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = original_instance_template
        mocks[5].return_value = {
            "region": "https://www.googleapis.com/compute/v1/projects/mock_project/mock-us-central-region"}
        mocks[6].return_value = read_json_file("sample_auto_mode_network.json")

        original_instance = "mock_original_instance"
        new_instance = "mock_new_instance"
        target_network = "target-network"
        target_subnetwork = "target-subnetwork"

        # No errors
        self.assertIsNone(
            main(self.project, self.zone, original_instance, new_instance,
                 target_network, target_subnetwork))
        # Check the new instance template is used to create a new VM
        # and it should have the same key-value pairs as the original one's
        # except for the network interface and the name
        new_instance_template = mocks[7].call_args[0][3]
        for k, v in new_instance_template.items():
            if k is "networkInterfaces":
                expected_network_interface = {
                    "network": "https://www.googleapis.com/compute/v1/projects/mock_project/global/networks/target-network",
                    "subnetwork": "https://www.googleapis.com/compute/v1/projects/mock_project/mock-us-central-region/target-network"
                }
                self.assertEquals(v, expected_network_interface)
            elif k is "name":
                self.assertEqual(v, new_instance)
            else:
                self.assertEqual(v, original_instance_template[k])

    def test_the_same_instance_name(self, *mocks):
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = read_json_file("sample_instance_template.json")
        mocks[6].return_value = read_json_file("sample_auto_mode_network.json")

        original_instance = "instance_1"
        new_instance = "instance_1"
        target_network = "target-network"
        target_subnetwork = "target-subnetwork"

        with self.assertRaises(UnchangedInstanceNameError):
            main(self.project, self.zone, original_instance, new_instance,
                 target_network, target_subnetwork)
            # check the original instance is not terminated
            mocks[0].assert_not_called()

    def test_new_instance_name_already_exists_in_project(self, *mocks):
        """The new instance name has existed in the project. The migration will be termintated and a rollback procedure will be called."""
        sample_instance_template = read_json_file(
            "sample_instance_template.json")
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = sample_instance_template
        mocks[6].return_value = read_json_file("sample_auto_mode_network.json")
        mocks[7].side_effect = HttpError(resp=self.errorResponse, content=b'')

        original_instance = "original_instance"
        new_instance = "new_instance"
        target_network = "target-network"
        target_subnetwork = "target-subnetwork"

        main(self.project, self.zone, original_instance, new_instance,
             target_network, target_subnetwork)
        # rollback will be called
        mocks[10].assert_called()
        # check all the disks are reattached in rollback
        self.assertEqual(mocks[10].call_args[0][4],
                         sample_instance_template["disks"])
        # check the original instance restarts in rollback
        self.assertEqual(mocks[10].call_args[0][3], original_instance)

    def test_migrating_to_legacy_network(self, *mocks):
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = read_json_file("sample_instance_template.json")
        mocks[6].return_value = read_json_file("sample_legacy_network.json")

        original_instance = "original_instance"
        new_instance = "new_instance"
        target_network = "target-network"
        target_subnetwork = "target-subnetwork"

        with self.assertRaises(InvalidTargetNetworkError):
            main(self.project, self.zone, original_instance, new_instance,
                 target_network, target_subnetwork)
            # check the original instance is not terminated
            mocks[0].assert_not_called()

    def test_invalid_target_network(self, *mocks):
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = read_json_file("sample_instance_template.json")
        mocks[6].side_effect = HttpError(resp=self.errorResponse, content=b'')

        original_instance = "original_instance"
        new_instance = "new_instance"
        target_network = "target-network"
        target_subnetwork = "target-subnetwork"

        with self.assertRaises(HttpError):
            main(self.project, self.zone, original_instance, new_instance,
                 target_network, target_subnetwork)
            # check the original instance is not terminated
            mocks[0].assert_not_called()

    def test_invalid_subnetwork_for_any_network_mode(self, *mocks):
        """The subnetwork doesn't exist. The migration will be termintated and a rollback procedure will be called. """
        sample_instance_template = read_json_file(
            "sample_instance_template.json")
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = sample_instance_template
        mocks[6].return_value = read_json_file("sample_auto_mode_network.json")
        mocks[7].side_effect = HttpError(resp=self.errorResponse, content=b'')

        original_instance = "original_instance"
        new_instance = "new_instance"
        target_network = "target-network"
        target_subnetwork = "target-subnetwork"

        main(self.project, self.zone, original_instance, new_instance,
             target_network, target_subnetwork)
        # rollback will be called
        mocks[10].assert_called()
        # check all the disks are reattached in rollback
        self.assertEqual(mocks[10].call_args[0][4],
                         sample_instance_template["disks"])
        # checl the original instance restarts in rollback
        self.assertEqual(mocks[10].call_args[0][3], original_instance)

    def test_auto_network_with_no_subnetwork_specified(self, *mocks):
        """The subnetwork is not specified, and the network is in auto mode """
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = read_json_file("sample_instance_template.json")
        mocks[6].return_value = read_json_file("sample_auto_mode_network.json")

        original_instance = "original_instance"
        new_instance = "new_instance"
        target_network = "mock_target_network"
        target_subnetwork = None

        self.assertIsNone(
            main(self.project, self.zone, original_instance, new_instance,
                 target_network, target_subnetwork))

    def test_non_auto_network_with_no_subnetwork_specified(self, *mocks):
        """No specified subnetwork with a non-auto VPC network"""
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = read_json_file("sample_instance_template.json")
        mocks[6].return_value = read_json_file(
            "sample_non_auto_mode_network.json")

        original_instance = "original_instance"
        new_instance = "new_instance"
        target_network = "target-network"
        target_subnetwork = None

        with self.assertRaises(MissingSubnetworkError):
            main(self.project, self.zone, original_instance, new_instance,
                 target_network, target_subnetwork)
            # check the original instance is not terminated
            mocks[0].assert_not_called()

    def test_original_instance_with_no_disks(self, *mocks):
        """The original instance doesn't have a disk.
        In this case, rollback procedure will not be called,
        since it is not allowed to start a VM without a boot disk """

        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = read_json_file(
            "sample_instance_template_with_no_disks.json")
        mocks[6].return_value = read_json_file(
            "sample_non_auto_mode_network.json")

        original_instance = "original_instance"
        new_instance = "new_instance"
        target_network = "target-network"
        target_subnetwork = "target-subnetwork"

        main(self.project, self.zone, original_instance, new_instance,
             target_network, target_subnetwork)
        # check the rollback is called
        mocks[10].assert_called()
        # check the original instance is not terminated
        mocks[0].assert_called()


@patch(
    "vm_network_migration.vm_network_migration.roll_back_original_instance")  # index: 10
@patch("vm_network_migration.vm_network_migration.attach_disk")  # index: 9
@patch("vm_network_migration.vm_network_migration.delete_instance")  # index: 8
@patch("vm_network_migration.vm_network_migration.create_instance")  # index: 7
@patch("vm_network_migration.vm_network_migration.get_network")  # index: 6
@patch("vm_network_migration.vm_network_migration.get_zone")  # index: 5
@patch("vm_network_migration.vm_network_migration.detach_disk")  # index: 4
@patch(
    "vm_network_migration.vm_network_migration.retrieve_instance_template")  # index: 3
@patch(
    "vm_network_migration.vm_network_migration.wait_for_operation")  # index: 2
@patch("vm_network_migration.vm_network_migration.stop_instance")  # index: 1
@patch("google.auth.default")  # index 0
class MainFlowHttpErrorHandling(unittest.TestCase):
    MOCK_CREDENTIALS = mock.Mock(spec=google.auth.credentials.Credentials)
    errorResponse = httplib2.Response({
        "status": 404,
        "reason": "HttpMock response: invalid network"})
    project = "mock_project"
    zone = "mock_us_central1_a"

    def test_stop_instance_failed(self, *mocks):
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[1].side_effect = HttpError(resp=self.errorResponse, content=b'')
        mocks[3].return_value = read_json_file(
            "sample_instance_template_with_no_disks.json")
        mocks[6].return_value = read_json_file(
            "sample_non_auto_mode_network.json")

        original_instance = "original-instance"
        new_instance = "new-instance"
        target_network = "target-network"
        target_subnetwork = "target-subnetwork"

        with self.assertRaises(HttpError):
            main(self.project, self.zone, original_instance, new_instance,
                 target_network, target_subnetwork)

    def test_get_network_failed(self, *mocks):
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = read_json_file(
            "sample_instance_template.json")
        mocks[6].side_effect = HttpError(resp=self.errorResponse, content=b'')

        original_instance = "original-instance"
        new_instance = "new-instance"
        target_network = "target-network"
        target_subnetwork = "target-subnetwork"

        with self.assertRaises(HttpError):
            main(self.project, self.zone, original_instance, new_instance,
                 target_network, target_subnetwork)

    def test_retrieve_instance_template_failed(self, *mocks):
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].side_effect = HttpError(resp=self.errorResponse, content=b'')
        mocks[6].return_value = read_json_file(
            "sample_non_auto_mode_network.json")

        original_instance = "original-instance"
        new_instance = "new-instance"
        target_network = "target-network"
        target_subnetwork = "target-subnetwork"

        # with self.assertRaises(HttpError):
        main(self.project, self.zone, original_instance, new_instance,
             target_network, target_subnetwork)
        # check rollback is called
        mocks[10].assert_called()

    def test_detach_disk_failed(self, *mocks):
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = read_json_file(
            "sample_instance_template.json")
        mocks[4].side_effect = HttpError(resp=self.errorResponse, content=b'')
        mocks[6].return_value = read_json_file(
            "sample_non_auto_mode_network.json")

        original_instance = "original-instance"
        new_instance = "new-instance"
        target_network = "target-network"
        target_subnetwork = "target-subnetwork"

        # with self.assertRaises(HttpError):
        main(self.project, self.zone, original_instance, new_instance,
             target_network, target_subnetwork)
        # check rollback is called
        mocks[10].assert_called()

    def test_get_zone_failed(self, *mocks):
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = read_json_file(
            "sample_instance_template.json")
        mocks[5].side_effect = HttpError(resp=self.errorResponse, content=b'')
        mocks[6].return_value = read_json_file(
            "sample_non_auto_mode_network.json")

        original_instance = "original-instance"
        new_instance = "new-instance"
        target_network = "target-network"
        target_subnetwork = "target-subnetwork"

        # with self.assertRaises(HttpError):
        main(self.project, self.zone, original_instance, new_instance,
             target_network, target_subnetwork)
        # check rollback is called
        mocks[10].assert_called()

    def test_create_instance_failed(self, *mocks):
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = read_json_file(
            "sample_instance_template.json")
        mocks[6].return_value = read_json_file(
            "sample_non_auto_mode_network.json")
        mocks[7].side_effect = HttpError(resp=self.errorResponse, content=b'')

        original_instance = "original-instance"
        new_instance = "new-instance"
        target_network = "target-network"
        target_subnetwork = "target-subnetwork"

        # with self.assertRaises(HttpError):
        main(self.project, self.zone, original_instance, new_instance,
             target_network, target_subnetwork)
        # check rollback is called
        mocks[10].assert_called()

    def test_delete_instance_failed(self, *mocks):
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = read_json_file(
            "sample_instance_template.json")
        mocks[6].return_value = read_json_file(
            "sample_non_auto_mode_network.json")
        mocks[8].side_effect = HttpError(resp=self.errorResponse, content=b'')

        original_instance = "original-instance"
        new_instance = "new-instance"
        target_network = "target-network"
        target_subnetwork = "target-subnetwork"

        with self.assertRaises(HttpError):
            main(self.project, self.zone, original_instance, new_instance,
                 target_network, target_subnetwork)

    def test_attach_disk_failed(self, *mocks):
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        mocks[3].return_value = read_json_file(
            "sample_instance_template.json")
        mocks[6].return_value = read_json_file(
            "sample_non_auto_mode_network.json")
        mocks[8].side_effect = HttpError(resp=self.errorResponse, content=b'')

        original_instance = "original-instance"
        new_instance = "new-instance"
        target_network = "target-network"
        target_subnetwork = "target-subnetwork"

        with self.assertRaises(HttpError):
            main(self.project, self.zone, original_instance, new_instance,
                 target_network, target_subnetwork)
