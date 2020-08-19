# Target Pool Network Migration
## Limitations:
1. The target pool can have single VMs or managed instance groups in it.
2. If there is an VM instance which is a member of an unmanaged instance group, it is not allowed. It is an ambiguous situation. Because this unmanaged instance group may have other instances which are not serving this instance group, it is not proper to infer the user wants to migrate the whole group. In this scenario, the migration will not start. The user should detach these instances first, and then migrate this target pool. 
3. If the target pool shares the same backends with another backend service or another target pool, the migration will fail and rollback to the original network.
4. The target pool will not be deleted during the migration. Only its backends will be migrated one by one.
5. If there are more than one backends serving this target pool, after the first backend finishes the migration, the tool will be paused and wait until the first backend become healthy (or partially healthy if the backend is a managed instance group). After the first backend passes the health check, the tool will continue migrating other backends without further health checks. The tool minimizes or even eliminates the downtime for the target pool migration if it has mutliple backends.
## Examples:
### 1. A target pool only has single instances and managed instance groups as backends:
     python3 target_pool_migration.py  --project=my-project \
        --region=us-central1-a  --target_pool_name=my-target-pool  \
        --network=my-network  --subnetwork=my-network-subnet1 \
     (Note: you can add --preserve-instance-external-ip=True if
      you want to preserve the single instances' IP) 
## Special cases
### 1. A target pool has one or more instances from an unmanaged instance group as backends:
    Not supported. 
    The user should manually detach these instances, 
    then try to migrate this target pool again.
### 2. A target pool shares one or more backends with another target pool or backend service:
    Not supported.
    The tool will rollback.
