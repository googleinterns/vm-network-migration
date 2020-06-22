import time
from vm_network_migration.errors import *

class Operations:
    def __init__(self, compute, project, zone, region):
        self.compute = compute
        self.project = project
        self.zone = zone
        self.region = region

    def wait_for_zone_operation(self, operation):
        """ Keep waiting for a zone operation until it finishes

            Args:
                compute: google API compute engine service
                project: project ID
                zone: zone of the VM
                operation: name of the Operations resource to return

            Returns:
                a deserialized object of the response

            Raises:
                ZoneOperationsError: if the operation has an error
                googleapiclient.errors.HttpError: invalid request
        """
        print('Waiting ...')
        while True:
            result = self.compute.zoneOperations().get(
                project=self.project,
                zone=self.zone,
                operation=operation).execute()
            if result['status'] == 'DONE':
                print("The current operation is done.")
                if 'error' in result:
                    raise ZoneOperationsError(result['error'])
                return result
            time.sleep(1)

    def wait_for_region_operation(self, operation):
        """ Keep waiting for a region operation until it finishes

            Args:
                compute: google API compute engine service
                project: project ID
                region: zone of the VM
                operation: name of the Operations resource to return

            Returns:
                a deserialized object of the response

            Raises:
                RegionOperationsError: if the operation has an error
                googleapiclient.errors.HttpError: invalid request
        """
        print('Waiting ...')
        while True:
            result = self.compute.regionOperations().get(
                project=self.project,
                region=self.region,
                operation=operation).execute()
            if result['status'] == 'DONE':
                print("The current operation is done.")
                if 'error' in result:
                    print('Region operations error', result['error'])
                    raise RegionOperationsError(result['error'])
                return result
            time.sleep(1)
