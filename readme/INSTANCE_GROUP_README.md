# Instance Group Network Migration
## Limitations:
1. For a managed instance group, after the migration, the VM instances of this group will be recreated with new disks and new IP addresses. A new instance template will be inserted without deleting the original instance template.
2. IP preservation feature is only valid for an unmanaged instance group. 
3. If the instance group is the backends of other services, the migration will not start or will rollback.
4. The original instance group will be deleted and recreated using modified network configuration

## Examples:
### Unmanaged Instance Group:
#### 1. Migrate an unmanaged instance group without preserving the external IP address:
     python3 instance_group_migration.py  --project=my-project \
        --zone=us-central1-a  --instance_group_name=my-instance-group  \
        --network=my-network  --subnetwork=my-network-subnet1 \
        --preserve_external_ip=False
         
#### 2. Migrate an an unmanaged instance group with preserving the external IP address:
Note: No matter whether its external IP address is a static one or a ephemeral one, 
it will be reserved as a static IP after the migration. The preserving action is not reversible. 

     python3 instance_group_migration.py  --project_id=my-project \
        --zone=us-central1-a  --instance_group_name=my-instance-group  \
        --network=my-network  --subnetwork=my-network-subnet1 \
        --preserve_external_ip=True
        
### Managed Instance Group:
#### 1. Migrate a zonal(single-zone) managed instance group
     python3 instance_group_migration.py  --project_id=my-project \
        --zone=us-central1-a  --instance_group_name=my-instance-group  \
        --network=my-network  --subnetwork=my-network-subnet1
#### 2. Migrate a regional(multi-zone) managed instance group
     python3 instance_group_migration.py  --project_id=my-project \
        --region=us-central1  --instance_group_name=my-instance-group  \
        --network=my-network  --subnetwork=my-network-subnet1
        
## Special Cases:
### Unmanaged Instance Group:
#### 1. The instance group is serving >= 1 target pool
     The unmanaged instance group serves a target pool, which means the
     instances in this instance group serve the target pool. The migration can
     still succeed. But the instances might be detached from the target pool
     after the migration. Therefore, it is not a recommended user case.
#### 2. The instance group is serving >= 1 backend service
     Not supported. The migration will fail and rollback to the legacy network.
     The user should migrate the backend service directly, or detach the instance
     group from the backend service.
### Managed Instance Group
#### 1. The instance group is serving >= 1 target pool
    Not supported. The migration will fail and rollback to the legacy network.
    The user should migrate the backend service directly, or detach the instance
    group from the target pool.
#### 2. The instance group is serving >= 1 backend service
     Not supported. The migration will fail and rollback to the legacy network.
     The user should migrate the backend service directly, or detach the instance
     group from the backend service.