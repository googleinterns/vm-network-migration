# Legacy Network Resource Migration
**This is not an officially supported Google product.**
## Description
This tool is used to migrate Google Compute Engine (GCE) resources from a legacy network to a
VPC subnet with downtime. It uses Google APIs Python client library to manage the 
GCE resources. 
## Use cases
### Supported GCE resources:
* VM instance (with IP preservation)
* Target instance (with IP preservation)
* Instance group
    * Unmanaged
    * Managed 
* Target pool
* Backend service
    * INTERNAL
    * EXTERNAL
    * INTERNAL-SELF-MANAGED
* Forwarding rule 
    * INTERNAL 
    * EXTERNAL (without changing external IP)
    * INTERNAL-SELF-MANAGED 
### Unsupported GCE resources:
*They are unsupported, because they are new features using VPC subnets and they don't use legacy networks*.
* Backend service
    * INTERNAL-MANAGED
* Forwarding rule
    * INTERNAL-MANAGED
* NEG
### How to migrate a load balancer?
A load balancer is not a GCE resource, but a combination of different GCE resources.
You can try to migrate a load balancer's forwarding rule so that the tool will migrate all the resources in use by this load balancer.        
## Characteristics:
* The tool has simple validation checks before the migration starts. If the resource can not be migrated, the migration process will not start and won't affect the original resource.
* In some cases, the validation checks are passed, but the resource is still not able to be safely migrated, the migration will fail and roll back the resource to its original network. A 'MigrationFailed' error will raise after the rollback finishes. With the rollback mechanism, the tool can preserve the target resource's original configuration if the migration fails. 
* Explanation about how the tool handles the external IP preservation: the tool will reserve the IP as a static IP though addresses.insert API. If the original external IP is ephemeral, it will become a static IP after calling the IP_preservation_handler. This action is not invertible, even though the original VM rollbacks due to pitfalls.  ## Limitations
### General limitations:
* You should not manually change any GCE resources during the migration. Otherwise, some errors might happen. E.g., resources that can not be found or out of quota issues. 
* Downtime is required in general. (*Downtime:* during the migration, the resource will be out of service. The downtime varies from several minutes to several ten minutes.)
* If the target subnet can not serve the target resource, the migration will not succeed. For example, the target subnet only exists in region A, but the target resource is in region B, the migration will not succeed. 
* The resource will remain in the same project after the migration.
* Only handle the external IP preservation, but not internal IP. The internal IP will change no matter whether the migration is successful or not.
* IP preservation action is not reversible even though the migration fails. You need to release the external IP manually after the migration.
* If the resource has an Ephemeral external IP and the rollback happens during the migration, its external IP may change after the rollback.
### Specific limitations:
#### [VM migration.](readme/VM_INSTANCE_README.md)
#### [Instance group migration.](readme/INSTANCE_GROUP_README.md)
#### [Target pool migration.](readme/TARGET_POOL_README.md)
#### [Backend service migration.](readme/BACKEND_SERVICE_README.md)
#### [Forwarding rule migration.](readme/FORWARDING_RULE_README.md)
## Requirements:
* Python 3.6+. 
* Pip must be installed for the Python binary you will use. E.g. Try `python3 -m pip`
## Before running
1. If not already done, enable the Compute Engine API
  and check the quota for your project at
  https://console.developers.google.com/apis/api/compute
2. This sample uses Application Default Credentials for authentication.
  If not already done, install the gcloud CLI from
  https://cloud.google.com/sdk and run \
    `gcloud beta auth application-default login` \
  For more information, see
  https://developers.google.com/identity/protocols/application-default-credentials
3. Install the Python client library for Google APIs by running \
    `pip3 install --upgrade google-api-python-client`
4. Download the repository and go to the root folder \
    `cd vm-network-migration` \
    `pip3 install . `
## Run
#### Migrate by selfLink (It is the easiest way to use the tool. [Read more about how to find a resource's selfLink](readme/FIND_SELFLINK_README.md))
| Flag  | Description | Flag Type| 
| ------------- | ------------- | ---|
| selfLink | The URL selfLink of the target resource. [Details about the selfLink.](readme/FIND_SELFLINK_README.md)| string |
| network | The name of the target VPC network. | string |
| subnetwork | Default: None.  The name of the target VPC subnetwork. This flag is optional for an auto-mode VPC network. For other subnet creation modes, this flag should be specified; otherwise, an error will be thrown.  | string |
| preserve_instance_external_ip | Default: False. Preserve the external IPs of the VM instances serving the target resource. Be cautious: If the VM instance is in a managed instance group, its external IP cannot be preserved. | boolean |

     python3 migrate_by_selfLink.py --selfLink=selfLink-of-target-resource  \
     --network=my-network  --subnetwork=my-network-subnet \
     --preserve_instance_external_ip=True     
     
### If you can not find the selfLink of the target resource, try the following methods:
| Flag  | Description | Flag Type| 
| ------------- | ------------- | ---|
| project_id | The project ID of the target resource.  | string |
| target_resource_name | The name of the target resource.  | string |
| region | Default: None. If it is a regional resource, this flag must be specified. If it is a zonal/global resource, this field should be blank.| string |
| zone | Default: None. If it is a zonal resource (E.g., a VM instance is a zonal resource), this flag must be specified. If it is a regional/global resource, this field should be blank.| string |
| network | The name of the target VPC network  | string |
| subnetwork | Default: None.  The name of the target VPC subnetwork. This flag is optional for an auto-mode VPC network. This flag should be specified for other subnet creation modes; otherwise,  an error will be thrown.    | string |
| preserve_instance_external_ip | Default: False. Preserve the external IPs of the VM instances serving the target resource. Be cautious: If the VM instance is in a managed instance group, its external IP cannot be preserved. | boolean |

#### VM instance network migration. [See more examples.](readme/VM_INSTANCE_README.md)
     python3 instance_migration.py  --project_id=my-project \
     --target_resource_name=my-original-instance --zone=us-central1-a  \
     --network=my-network \ 
     [--subnetwork=my-network-subnet1 --preserve_instance_external_ip=False] 
#### Target instance network migration. [See more examples.](readme/TARGET_INSTANCE_README.md)
     python3 instance_migration.py  --project_id=my-project \
     --target_resource_name=my-target-instance --zone=us-central1-a  \
     --network=my-network \ 
     [--subnetwork=my-network-subnet1 --preserve_instance_external_ip=False]      
#### Instance group network migration. [See more examples.](readme/INSTANCE_GROUP_README.md)
     python3  instance_group_migration.py  --project_id=my-project \
     --target_resource_name=my-original-instance-group  --region=us-central1 \
     --network=my-network \
     [--subnetwork=my-network-subnet1 --preserve_instance_external_ip=False]
Note: either --zone or --region must be specified.
#### Target pool network migration. [See more examples.](readme/TARGET_POOL_README.md)
    python3 target_pool_migration.py  --project_id=my-project \
    --target_resource_name=my-target-pool --region=us-central1 \
    --network=my-network \
    [--subnetwork=my-network-subnet --preserve_instance_external_ip=False]
    
#### Backend service migration. [See more examples.](readme/BACKEND_SERVICE_README.md)
    python3 backend_service_migration.py  --project_id=my-project \
    --target_resource_name=my-backend-service \
    --network=my-network \
    [--subnetwork=my-network-subnet --preserve_instance_external_ip=False]
Note: --region is only needed for a regional backend service.    
#### Forwarding rule migration. [See more examples.](readme/FORWARDING_RULE_README.md)
    python3 forwarding_rule_migration.py  --project_id=my-project \
    --target_resource_name=my-forwarding-rule 
    --network=my-network \ 
    [--subnetwork=my-network-subnet1 --preserve_instance_external_ip=False]
Note: --region is only needed for a regional forwarding rule.

## Troubleshooting: 
1. The tool cannot run and has an import issue. 
    * You should check the Python version and ensure pip3 matches Python3.
    * Follow the 'Before running' section and install it again.
2. After the migration, all the resources migrated, but the resource's external IP is not accessible. 
    * You should check out the target network's firewall. You need to set up all the firewalls in the target network manually. The easiest way is to follow all the original network's firewall settings and create the target VPC network's firewalls.
3. The rollback is failed and throws a 'RollbackFailed' error:
    * The rollback can fail due to network issues or quota limitation issues. 
    * In this scenario, you can refer to the ‘backup.log’ file, which is located in the root folder. 
    You can recreate the lost resources by yourself. The configuration of all the legacy resources that the tool might have possibly
     touched are saved in the 'backup.log' file. 
4. The tool throws a 'MigrationFailed' error:
    * The migration has failed. The tool rolls back the target resource to the legacy network. You should be cautious that the internal IPs may have already changed after the rollback.
5. The tool terminates with some other errors, such as 'InvalidTargetNetworkError' or 'HttpError':
    * The migration didn't start due to that error. The tool didn't modify the target resource.   
 
## Run end-to-end tests:
#### Before running:
An existing GCP project_id is needed. Run in command line: \
```
export PROJECT_ID='some test project'
```
#### Run all the tests together:    
    python3 -m unittest discover
#### Run a single test file:
    python3 test_file_name.py
#### Run a single test case:
    python3 test_file_name.py TestClassName.testMethodName
    
## Source code headers

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
