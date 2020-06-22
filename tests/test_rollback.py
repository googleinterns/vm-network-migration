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
Test roll_back_original_instance() function
"""

import json
import os
from unittest import mock
from unittest.mock import patch

import google.auth.credentials
import httplib2
import unittest2 as unittest
from vm_network_migration.vm_network_migration import *

from googleapiclient.http import HttpMock

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

@patch("vm_network_migration.vm_network_migration.retrieve_instance_template") # index: 5
@patch("vm_network_migration.vm_network_migration.create_instance")  # index: 4
@patch("vm_network_migration.vm_network_migration.attach_disk")  # index: 3
@patch(
    "vm_network_migration.vm_network_migration.wait_for_zone_operation")  # index: 2
@patch("vm_network_migration.vm_network_migration.start_instance")  # index: 1
@patch("google.auth.default")  # index 0
class RollBackOriginalInstance(unittest.TestCase):
    MOCK_CREDENTIALS = mock.Mock(spec=google.auth.credentials.Credentials)
    compute = discovery.build('compute', 'v1',
                              credentials=MOCK_CREDENTIALS)
    errorResponse = httplib2.Response({
        "status": 400})

    http = HttpMock(datafile("compute_rest.json"), {
        "status": "200"})
    project = "mock_project"
    zone = "mock_us_central1_a"
    instance = "mock_original_instance"
    original_instance_template = read_json_file(
        "sample_instance_template.json")

    def test_rollback_after_instance_deleted(self, *mocks):
        self.errorResponse.reason = "HttpMock response: not found"
        mocks[5].side_effect = HttpError(resp=self.errorResponse, content=b'')
        disk = ['{"deviceName": "mock_disk_0", "boot":true}']
        rollback_failure_protection(self.compute, self.project, self.zone,
                                    self.instance,
                                    self.original_instance_template, disk, True)
        # recreate the original instance
        mocks[4].assert_called()
        # no disks are reattached
        mocks[3].assert_not_called()
        # the original instance is not rebooted
        mocks[1].assert_not_called()

    def test_rollback_after_instance_terminated(self, *mocks):
        mocks[5].return_value = {"status": "TERMINATED"}
        disk = ['{"deviceName": "mock_disk_0", "boot":true}']
        rollback_failure_protection(self.compute, self.project, self.zone,
                                    self.instance,
                                    self.original_instance_template, disk, True)
        # recreate the original instance
        mocks[4].assert_not_called()
        # disks are reattached
        mocks[3].assert_called()
        # the original instance is rebooted
        mocks[1].assert_called()

    def test_rollback_with_instance_running(self, *mocks):
        mocks[5].return_value = {"status": "RUNNING"}
        disk = ['{"deviceName": "mock_disk_0", "boot":true}']
        rollback_failure_protection(self.compute, self.project, self.zone,
                                    self.instance,
                                    self.original_instance_template, disk, True)
        # recreate the original instance
        mocks[4].assert_not_called()
        # disks are not reattached
        mocks[3].assert_not_called()
        # the original instance is not rebooted
        mocks[1].assert_not_called()

    def test_single_disk_instance_rollback(self, *mocks):

        mocks[5].return_value = {'status': "TERMINATED"}
        single_disk = ['{"deviceName": "mock_disk_0", "boot":true}']
        rollback_failure_protection(self.compute, self.project, self.zone,
                                    self.instance,
                                    self.original_instance_template,
                                    single_disk, False)
        # check the disk is reattached
        self.assertTrue(mocks[3].call_count, 1)
        # check the instance restarts
        self.assertEqual(mocks[1].call_args[0][3], self.instance)

    def test_no_disk_info(self, *mocks):
        mocks[5].return_value = {
            'status': "TERMINATED"}
        rollback_failure_protection(self.compute, self.project, self.zone,
                                    self.instance,
                                    self.original_instance_template)
        # check the instance restarts
        self.assertEqual(mocks[1].call_args[0][3], self.instance)

    def test_multi_disks_instance_rollback(self, *mocks):
        mocks[5].return_value = {
            'status': "TERMINATED"}
        multi_disk = ['{"deviceName": "mock_disk_0", "boot":true}',
                      '{"deviceName": "mock_disk_1", "boot":false}']
        rollback_failure_protection(self.compute, self.project, self.zone,
                                    self.instance,
                                    self.original_instance_template, multi_disk)
        self.assertTrue(mocks[3].call_count, 2)
        # check the instance restarts
        self.assertEqual(mocks[1].call_args[0][3], self.instance)

    def test_start_instance_failed(self, *mocks):
        # An error happens during the rollback procedure
        mocks[1].side_effect = HttpError(resp=self.errorResponse, content=b'')
        disk = ['{"deviceName": "mock_disk_0", "boot":true}']
        self.assertFalse(
            rollback_failure_protection(self.compute, self.project, self.zone,
                                        self.instance,
                                        self.original_instance_template, disk,
                                        False))

    def test_attach_disk_failed(self, *mocks):
        # An error happens during the rollback procedure
        mocks[3].side_effect = HttpError(resp=self.errorResponse, content=b'')
        disk = ['{"deviceName": "mock_disk_0", "boot":true}']
        self.assertFalse(rollback_failure_protection(self.compute, self.project, self.zone,
                                    self.instance,
                                    self.original_instance_template, disk,
                                    False))


    def test_wait_for_zone_operation_failed(self, *mocks):
        # An error happens during the rollback procedure
        mocks[2].side_effect = ZoneOperationsError
        disk = ['{"deviceName": "mock_disk_0", "boot":true}']
        self.assertFalse(rollback_failure_protection(self.compute, self.project, self.zone,
                                    self.instance,
                                    self.original_instance_template, disk,
                                    False))
