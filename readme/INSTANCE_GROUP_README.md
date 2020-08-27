# Instance Group Network Migration
## Characteristics:
During the migration, the original instance group will be deleted and recreated using target network configuration
### Unmanaged instance group:
* All the instances of the instance group will be migrated to the target subnet.
* The external IP of the VM instances of the instance group can be preserved by setting --preserve_instance_external_ip=True
### Managed instance group:
* After the migration, the instance group's VM instances will be recreated with new disks and new IP addresses.  with new disks and new IP addresses. A new instance template will be inserted without deleting the original instance template. You should ensure your GCP quota allows a new instance template to be created. Otherwise, the migration will not start.
* The external IP of the VM instances of the instance group can not be preserved, even though you set --preserve_instance_external_ip=True
## Limitations:
* IP preservation feature is only valid for an unmanaged instance group. 
## Examples:
### Unmanaged instance group:
#### 1. Migrate an unmanaged instance group without preserving the external IP address:
     python3 instance_group_migration.py  --project=my-project \
        --zone=us-central1-a  --target_resource_name=my-instance-group \
        --network=my-network  
        [--subnetwork=my-network-subnet1 --preserve_instance_external_ip=False]
        
### Managed instance group:
#### 1. Migrate a zonal (single-zone) managed instance group
     python3 instance_group_migration.py  --project_id=my-project \
        --zone=us-central1-a  --target_resource_name=my-instance-group  \
        --network=my-network  
        [--subnetwork=my-network-subnet1]
#### 2. Migrate a regional (multi-zone) managed instance group
     python3 instance_group_migration.py  --project_id=my-project \
        --region=us-central1  --target_resource_name=my-instance-group  \
         [--subnetwork=my-network-subnet1]
## Special cases:
### Unmanaged instance group:
#### 1. The instance group is serving one or more target pool
Supported, but it is not recommended. \
The unmanaged instance group serves a target pool, which means the
instances in this instance group serve the target pool. The migration can
still succeed. But the VM instances might be removed from the target pool
after the migration. Therefore, it is not a recommended use case. \
Recommended action: [remove the instances of this instance group from the target pool.](https://cloud.google.com/compute/docs/reference/rest/v1/targetPools/removeInstance)
#### 2. The instance group is serving one or more backend service
Not supported. \
The migration will fail and rollback to the legacy network. \
*Recommendation*: [migrate the backend service directly](./BACKEND_SERVICE_README.md), 
or [remove the instance group from the backend service](https://cloud.google.com/compute/docs/reference/rest/v1/backendServices/update).
### Managed instance group
#### 1. The instance group is serving one or more target pool
Not supported. The migration will not start. \
*Recommendation*: [migrate the target pool](./TARGET_POOL_README.md) directly, or [remove the instance
group from the target pool](https://cloud.google.com/compute/docs/reference/rest/v1/instanceGroupManagers/setTargetPools).
#### 2. The instance group is serving one or more backend service
Not supported. \
The migration will fail and rollback to the legacy network. \
*Recommendation*: [migrate the backend service directly](./BACKEND_SERVICE_README.md), 
or [remove the instance group from the backend service](https://cloud.google.com/compute/docs/reference/rest/v1/backendServices/update).
