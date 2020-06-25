import warnings

from googleapiclient.errors import HttpError
from vm_network_migration.errors import *
from vm_network_migration.operations import Operations
from vm_network_migration.utils import generate_timestamp_string


class Address:
    def __init__(self, compute, project, region, external_ip=None):
        self.compute = compute
        self.project = project
        self.region = region
        self.operations = Operations(compute, project, None, region)
        self.external_ip = external_ip

    def retrieve_ip_from_network_interface(self, network_interface):
        if 'accessConfigs' in network_interface and 'natIP' in network_interface['accessConfigs'][0]:
            self.external_ip = network_interface['accessConfigs'][0][
                'natIP']
        else:
            self.external_ip = None

    def preserve_ip_addresses_handler(self, preserve_external_ip):
        """Preserve the external IP address.

        Args:
            compute: google API compute engine service
            project: project ID
            new_instance_name: name of the new VM
            new_network_info: selfLinks of current network and subnet
            original_network_interface: network interface of the original VM
            region: region of original VM
            preserve_external_ip: preserve the external ip or not

        Returns:
            network interface of the new VM
        """

        if preserve_external_ip and self.external_ip != None:
            print('Preserving the external IP address')
            # There is no external ip assigned to the original VM
            # An ephemeral external ip will be assigned to the new VM

            external_ip_address_body = self.generate_external_ip_address_body()
            try:
                preserve_external_ip_operation = self.preserve_external_ip_address(
                    external_ip_address_body)
                self.operations.wait_for_region_operation(
                    preserve_external_ip_operation[
                        'name'])
            except HttpError as e:
                error_reason = e._get_reason()
                # The external IP is already preserved as a static IP,
                # or the current name of the external IP already exists
                if 'already' in error_reason:
                    warnings.warn(error_reason, Warning)
                else:
                    warnings.warn(
                        'Failed to preserve the external IP address as a static IP.',
                        Warning)
                    print(e._get_reason())
                    print('An ephemeral external IP address will be assigned.')
                    self.external_ip = None
            else:
                print(
                    'The external IP address is reserved as a static IP address.')
        else:
            self.external_ip = None

    def preserve_external_ip_address(self, address_body):
        """ Preserve the external IP address.

        Args:
            compute: google API compute engine service
            project: project ID
            region: project region
            address_body: internal IP address information, such as
               {
                  name: "ADDRESS_NAME",
                  address: "IP_ADDRESS"
                }
        Returns: a deserialized object of the response

        Raises:
            googleapiclient.errors.HttpError: If the IP
            address is already a static one, or if the IP is not being
            used by any instance, or invalid request, it will raise an Http error
        """
        preserve_external_ip_operation = self.compute.addresses().insert(
            project=self.project, region=self.region,
            body=address_body).execute()
        self.operations.wait_for_region_operation(
            preserve_external_ip_operation['name'])
        return preserve_external_ip_operation

    def generate_external_ip_address_body(self):
        """Generate external IP address.

        Args:
            external_ip_address: IPV4 format address
            new_instance_name: name of the new VM

        Returns:
              {
              name: "ADDRESS_NAME",
              address: "IP_ADDRESS"
            }
        """
        if self.external_ip == None:
            raise AttributeNotExistError
        external_ip_address_body = {}
        external_ip_address_body[
            'name'] = self.project + '-' + self.region + '-' + generate_timestamp_string()
        external_ip_address_body['address'] = self.external_ip
        return external_ip_address_body
