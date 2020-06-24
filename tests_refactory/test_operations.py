
import json
import os

import httplib2
import timeout_decorator
import unittest2 as unittest
from googleapiclient.discovery import build
from googleapiclient.http import HttpMock
from googleapiclient.http import RequestMockBuilder
from vm_network_migration.vm_network_migration import *
from vm_network_migration.subnet_network import SubnetNetwork
import mock
from unittest.mock import patch
from google.auth import credentials


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





