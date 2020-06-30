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
Test operations.py
"""

import httplib2
import timeout_decorator
import unittest2 as unittest
from googleapiclient.discovery import build
from googleapiclient.http import HttpMock
from googleapiclient.http import RequestMockBuilder
from googleapiclient.http import HttpError
from vm_network_migration.modules.operations import Operations
from vm_network_migration.errors import *
from utils import *


class TestWaitForZoneOperation(unittest.TestCase):
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

    def test_wait_for_zone_operation_success(self):
        request_builder = RequestMockBuilder(
            {
                "compute.zoneOperations.get": (
                    self.successResponse, '{"status": "DONE"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        operations = Operations(compute, self.project, self.region, self.zone)
        wait_response = operations.wait_for_zone_operation({})

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
        operations = Operations(compute, self.project, self.region, self.zone)
        with self.assertRaises(HttpError):
            operations.wait_for_zone_operation({})

    @timeout_decorator.timeout(3, timeout_exception=StopIteration)
    def test_basic_zone_waiting(self):
        request_builder = RequestMockBuilder(
            {
                "compute.zoneOperations.get": (
                    self.successResponse,
                    '{"status":"RUNNING"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        operations = Operations(compute, self.project, self.zone, self.region)
        with self.assertRaises(StopIteration):
            operations.wait_for_zone_operation({})

    def test_error_in_zone_waiting(self):
        request_builder = RequestMockBuilder(
            {
                "compute.zoneOperations.get": (
                    self.successResponse,
                    '{"status":"DONE", "error":"something wrong"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        operations = Operations(compute, self.project, self.zone, self.region)
        with self.assertRaises(ZoneOperationsError):
            operations.wait_for_zone_operation({})


class TestWaitForRegionOperation(unittest.TestCase):
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

    def test_wait_for_region_operation_success(self):
        request_builder = RequestMockBuilder(
            {
                "compute.regionOperations.get": (
                    self.successResponse, '{"status": "DONE"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        operations = Operations(compute, self.project, self.region, self.zone)
        wait_response = operations.wait_for_region_operation({})

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
        operations = Operations(compute, self.project, self.region, self.zone)
        with self.assertRaises(HttpError):
            operations.wait_for_region_operation({})

    @timeout_decorator.timeout(3, timeout_exception=StopIteration)
    def test_basic_region_waiting(self):
        request_builder = RequestMockBuilder(
            {
                "compute.regionOperations.get": (
                    self.successResponse,
                    '{"status":"RUNNING"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        operations = Operations(compute, self.project, self.zone, self.region)
        with self.assertRaises(StopIteration):
            operations.wait_for_region_operation({})

    def test_error_in_region_waiting(self):
        request_builder = RequestMockBuilder(
            {
                "compute.regionOperations.get": (
                    self.successResponse,
                    '{"status":"DONE", "error":"something wrong"}')})
        compute = build("compute", "v1", self.http,
                        requestBuilder=request_builder)
        operations = Operations(compute, self.project, self.zone, self.region)
        with self.assertRaises(RegionOperationsError):
            operations.wait_for_region_operation({})
