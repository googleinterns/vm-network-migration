# Target Pool Network Migration
## Characteristics
1. The target pool itself will not be modified during the migration, because it doesn't live in a network. Only its backends will be migrated one by one.
2. If more than one backends are serving this target pool, it may have no downtime during the migration.
 After the first backend finishes the migration, the tool will be paused and wait until the first backend becomes healthy (or partially healthy if the backend is a managed instance group).
 After the first backend passes the health check, the tool will continue migrating other backends without further health checks. 
 This health check waiting feature allows the tool to minimize or even eliminate the downtime if the target pool has multiple backends.
## Limitations:
1. If the target pool is serving by a VM instance, a member of an unmanaged instance group, the migration will not start. You should [remove these instances from the target pool](https://cloud.google.com/compute/docs/reference/rest/v1/targetPools/removeInstance) first, and then migrate this target pool. 

## Examples:
### 1. A target pool only has single instances and managed instance groups as backends:
     python3 target_pool_migration.py  --project=my-project \
        --region=us-central1-a  --target_resource_name=my-target-pool  \
        --network=my-network  
        [--subnetwork=my-network-subnet1 --preserve_instance_external_ip=False]
        
## Special cases:
### 1. The target pool has one or more instances from an unmanaged instance group as backends:
Not supported. \
Reason: see **Limitations**
  
### 2. The target pool is served by a same instance group with another target pool or backend service:
Not supported. \
The tool will rollback. \
*Recommendation*: [remove this instance group from the target pool](https://cloud.google.com/compute/docs/reference/rest/v1/instanceGroupManagers/setTargetPools) and try the target pool migration again. 

### 3. The target pool is served by a same VM instance with another target pool:
Supported, but not recommended. \
The migration will succeed, but the shared VM instance may be removed from another target pool.
*Recommendation*: after the migration, double-check if the VM instance has been removed from another target pool.
### 4. A target pool is serving a forwarding rule:
Supported. \
After the migration, this target pool will still serve its original forwarding rule.
### 5. A target pool has a backup pool:
Supported with limitation. \
The backup pool will not be migrated. 
The user can migrate the backup pool separately.
    