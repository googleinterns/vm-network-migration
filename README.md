# VM Network Migration
**This is not an officially supported Google product.**
## Description

This Python library is used to migrate a VM instance or an instance group from its legacy network to a
subnetwork with downtime. The project uses Google APIs Python client library (Compute Engine APIs) to manage the 
Compute Engine resources. 

## Requirements and Limitations
### Single VM network migration:
1. A new VM will be created in the target subnetwork, and the original VM will be deleted. 
2. The customer can choose to preserve the external IP.
3. If the original VM uses a Ephemeral external IP, and the customer chooses to preserve it, it will become a static external IP after the migration.
4. Support migrating a VM from a legacy network to a subnetwork, or from one VPC network to another. Within a network, a VM can also be migrated from one subnet to another. Migration from any network to a legacy network is not allowed.
5. The original VM should only have one NIC.
6. The original VM and the new VM will have the same configuration except for the network interface. Therefore, they are in the same project, same zone, and same region.
7. The original VM must not be part of any instance group before changing the network it is associated with, since VMs in an instance group have to be in the same network. 
8. The original VM is assumed to be standalone. Other cases, for example, if the original instance is served as a backend of other services are not considered in the current scope.
9. There is a possibility that the main flow runs into an error and the rollback procedure also fails. In this case, the customer may lose both the original VM and the new VM. The original VM’s configuration will be printed out as a reference.  

### Instance group network migration:
1. For a managed instance group, after the migration, the VM instances of this group will be recreated with new disks and new IP addresses. A new instance template will be inserted without deleting the original instance template.
2. For an unmanaged instance group, the customer can choose to preserve the instances’ external addresses.
3. If the instance group is the backend of other services, the connection may be lost after the migration.
4. The rollback procedure may also fail. In this case, the customer may lose both the original instance group and the new instance group. The original instance group’s configuration will be printed out as a reference.

## Backend service network migration:
1. Both external and internal backend services are supported.
2. The backends in the backend service will be migrated from a legacy network to a VPC network. Migration from a VPC network to any network is not supported. 
3. For a backend service which is serving an internal-managed load balancer (internal HTTPs load balancer), the backends will be migrated to the target VPC network. The network of the load balancer itself will remain unchanged, since an internal-managed load balancer must have already been on a VPC network.
4. For an external or an internal-managed backend service with multiple backends, the migration can have no downtime. Because the tool will migrate backends one by one, the load balancer can distribute the traffic to other backends while migrating one of the backends. (Backends with mixing networks can exist at the same time and can serve the load balancer together.) If the backend service only has one backend, then the downtime will be several minutes.
5. For an internal backend service, its associated forwarding rule will be deleted and recreated after the migration. It requires downtime.

## Target pool network migration:

1. The instances in the target pool will be migrated from its legacy network to a VPC network. Migration from a VPC network to any network is not supported.
2. If the instance is within an instance group, then the tool will run the instance group migration to migrate the whole instance group from its legacy network to a VPC network.
3. If an instance is serving multiple target pools or backends, it is not recommended to migrate, since the unknown errors may happen to other target pools or backends after the migration.

## Forwarding rule network migration:
1. It is not supposed to migrate a forwarding rule. The tool will migrate all the backend services or the target pool pointed by the forwarding rule from a legacy network to a VPC network.

## Before Running
    1. If not already done, enable the Compute Engine API
       and check the quota for your project at
       https://console.developers.google.com/apis/api/compute
    2. This sample uses Application Default Credentials for authentication.
       If not already done, install the gcloud CLI from
       https://cloud.google.com/sdk and run
       `gcloud beta auth application-default login`.
       For more information, see
       https://developers.google.com/identity/protocols/application-default-credentials
    3. Install the Python client library for Google APIs by running
       `pip3 install --upgrade google-api-python-client`
## Set Up
    cd vm_network_migration
    pip3 install .
## Run
#### Single VM network migration. [See more examples](./VM_INSTANCE_README.md)
     python3 instance_network_migration.py  --project=my-project \
     --zone=us-central1-a  --original_instance=my-original-instance  \
     --network=my-network  --subnetwork=my-network-subnet1 \
     --preserve_external_ip=False 
#### Instance group network migration
     python3  instance_group_network_migration.py  --project=my-project \
     --instance_group=my-original-instance-group  --region=us-central \
     --zone=None --network=my-network  --subnetwork=my-network-subnet1 \
     --preserve_external_ip=False
     (Note: either --region or --zone must be specified.)
     
## Source Code Headers

Every file containing source code must include copyright and license
information. This includes any JS/CSS files that you might be serving out to
browsers. (This is to help well-intentioned people avoid accidental copying that
doesn't comply with the license.)

Apache header:

    Copyright 2020 Google LLC

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        https://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
