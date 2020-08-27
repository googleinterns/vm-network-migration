# Backend Service Network Migration
## Characteristics:
The backend service can have one or more instance groups as its backends. The tool will migrate the backend service and all its backends to the target subnet.
### Global backend service:
* Supported global backend service: EXTERNAL or INTERNAL_SELF_MANAGED.
* During the migration, the tool won't modify the backend service itself, because a global backend service doesn't live within a network. If there are other services using the backend service, they will still connect with this backend service after the migration. The tool will only migrate the instance group backends serving this backend service.
* If it is serving a forwarding rule, the migration will still succeed.
* If more than one backends serve this backend service, it may have no downtime during the migration. After the first backend finishes the migration, the tool will be paused and wait until the first backend becomes partially healthy.
After the first backend passes the health check, the tool will continue migrating other backends without further health checks.
With this feature, the tool minimizes or eliminates the downtime for the backend service migration if it has multiple backends.
### Regional backend service:
* Supported regional backend service: INTERNAL.
* During the migration, the backend service itself will be deleted and recreated using the new network configuration. All its backends will be migrated as well.
* If it is serving a forwarding rule, the migration will not start. The user should detach this backend service from the forwarding rule, or try to [migrate its forwarding rule](./FORWARDING_RULE_README.md) instead.
## Limitations:
* If the backend service shares a backend with another backend service or target pool, the migration will fail and roll back.
## Examples:
### 1. A regional backend service (INTERNAL):
    python3 backend_service_migration.py  --project_id=my-project \
       --target_resource_name=my-backend-service  \
       --region=us-central1-a \
       --network=my-network  \
       [--subnetwork=my-network-subnet1 --preserve-instance-external-ip=True]
      
### 2. A global backend service (EXTERNAL or INTERNAL_SELF_MANAGED):
   python3 backend_service_migration.py  --project_id=my-project \
       --target_resource_name=my-backend-service  \
       --network=my-network  \
       [--subnetwork=my-network-subnet1 --preserve-instance-external-ip=True]
   
## Special cases
### 1. A backend service has NEGs as its backends
Supported. \
There is no need to migrate the NEGs, see [Unsupported GCE Resources](../README.md).
The tool will ignore those NEGs backends and only migrate instance group backends.
### 2. A backend service has backends from different regions:
Supported, as long as the target subnet exists in all those regions. \
For example, both an instance group from region A and another instance group from region B serve the backend service.
If the target subnet with a name 'a-target-subnet' exists in both region A and region B, the backend service migration will succeed.
Otherwise, the tool will roll back.
 

