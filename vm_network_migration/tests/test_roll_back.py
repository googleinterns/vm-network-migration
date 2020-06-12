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
from __future__ import absolute_import

import google
import httplib2
import mock
import unittest2 as unittest
from googleapiclient.errors import HttpError
from mock import patch
from utils import *
from vm_network_migration import *


@patch("vm_network_migration.attach_disk")  # index: 3
@patch("vm_network_migration.wait_for_operation")  # index: 2
@patch("vm_network_migration.start_instance")  # index: 1
@patch("google.auth.default")  # index 0
class RollBackOriginalInstance(unittest.TestCase):
    MOCK_CREDENTIALS = mock.Mock(spec=google.auth.credentials.Credentials)
    compute = discovery.build('compute', 'v1',
                              credentials=MOCK_CREDENTIALS)
    errorResponse = httplib2.Response({
        "status": 404,
        "reason": "HttpMock request is failed"})
    project = "mock_project"
    zone = "mock_us_central1_a"
    instance = "mock_original_instance"

    def test_single_disk_reattach(self, *mocks):
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        single_disk = ['{"deviceName": "mock_disk_0", "boot":true}']
        roll_back_original_instance(self.compute, self.project, self.zone,
                                    self.instance, single_disk)
        self.assertTrue(mocks[3].call_count, 1)

    def test_mutli_disks_reattach(self, *mocks):
        mocks[0].return_value = (self.MOCK_CREDENTIALS, self.project)
        multi_disk = ['{"deviceName": "mock_disk_0", "boot":true}',
                      '{"deviceName": "mock_disk_1", "boot":false}']
        roll_back_original_instance(self.compute, self.project, self.zone,
                                    self.instance, multi_disk)
        self.assertTrue(mocks[3].call_count, 2)

    def test_start_instance_failed(self, *mocks):
        mocks[1].side_effect = HttpError(resp=self.errorResponse, content=b'')
        disk = ['{"deviceName": "mock_disk_0", "boot":true}']
        with self.assertRaises(HttpError):
            roll_back_original_instance(self.compute, self.project, self.zone,
                                        self.instance, disk)

    def test_attach_disk_failed(self, *mocks):
        mocks[3].side_effect = HttpError(resp=self.errorResponse, content=b'')
        disk = ['{"deviceName": "mock_disk_0", "boot":true}']
        with self.assertRaises(HttpError):
            roll_back_original_instance(self.compute, self.project, self.zone,
                                        self.instance, disk)

    def test_wait_for_operation_failed(self, *mocks):
        mocks[2].side_effect = ZoneOperationsError
        disk = ['{"deviceName": "mock_disk_0", "boot":true}']
        with self.assertRaises(ZoneOperationsError):
            roll_back_original_instance(self.compute, self.project, self.zone,
                                        self.instance, disk)
