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
Helper functions for tests
"""

import os
import json
import httplib2
from googleapiclient.http import RequestMockBuilder


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
def build_request_builder(instance_template, target_subnet_network_template):
    successResponse = httplib2.Response({
        "status": 200,
        "reason": "HttpMock response: Successful"
    })

    request_builder = RequestMockBuilder({
        "compute.instances.get": (
            successResponse, json.dumps(instance_template)),
        "compute.zones.get": (
            successResponse, '{"region":"http://regions/mock-region"}'),
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