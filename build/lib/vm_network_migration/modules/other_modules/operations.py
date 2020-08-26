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
""" Operation related methods
"""
import time

from vm_network_migration.errors import *
from vm_network_migration.utils import initializer

class Operations:
    @initializer
    def __init__(self, compute, project, zone=None, region=None):
        """ Initialize an Operation object

        Args:
            compute: google compute engine
            project: project ID
            zone: zone name
            region: region name
        """
        pass

    def wait_for_zone_operation(self, operation):
        """ Keep waiting for a zonal operation until it finishes

            Args:
                operation: name of the Operations resource to return

            Returns:
                a deserialized object of the response

            Raises:
                ZoneOperationsError: if the operation has an error
                googleapiclient.errors.HttpError: invalid request
        """
        print('Waiting for %s.' %(operation))
        while True:
            result = self.compute.zoneOperations().get(
                project=self.project,
                zone=self.zone,
                operation=operation).execute()
            if result['status'] == 'DONE':
                print("Done.")
                if 'error' in result:
                    raise ZoneOperationsError(result['error'])
                return result
            time.sleep(1)

    def wait_for_region_operation(self, operation):
        """ Keep waiting for a regional operation until it finishes

            Args:
                operation: name of the Operations resource to return

            Returns:
                a deserialized object of the response

            Raises:
                RegionOperationsError: if the operation has an error
                googleapiclient.errors.HttpError: invalid request
        """
        print('Waiting for %s.' %(operation))
        while True:
            result = self.compute.regionOperations().get(
                project=self.project,
                region=self.region,
                operation=operation).execute()
            if result['status'] == 'DONE':
                print("Done.")
                if 'error' in result:
                    print('Region operations error', result['error'])
                    raise RegionOperationsError(result['error'])
                return result
            time.sleep(1)

    def wait_for_global_operation(self, operation):
        """ Keep waiting for a global operation until it finishes

            Args:
                operation: name of the Operations resource to return

            Returns:
                a deserialized object of the response

            Raises:
                RegionOperationsError: if the operation has an error
                googleapiclient.errors.HttpError: invalid request
        """
        print('Waiting for %s.' % (operation))
        while True:
            result = self.compute.globalOperations().get(
                project=self.project,
                operation=operation).execute()
            if result['status'] == 'DONE':
                print("Done.")
                if 'error' in result:
                    print('Global operations error', result['error'])
                    raise RegionOperationsError(result['error'])
                return result
            time.sleep(1)

