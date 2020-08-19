# Backend Service Network Migration
## Limitations:
1. Supported type: ‘EXTERNAL’, ‘INTERNAL’ and ‘INTERAL_SELF_MANAGED’. The ‘INTERNAL_MANAGED’ is not supported, because it can not use a legacy network.
2. For an EXTERNAL or an INTERAL_SELF_MANAGED backend service, it will not be deleted. For an INTERNAL backend service, it will be deleted and recreated using the new network configuration.
3. If an INTERNAL backend service is serving a forwarding rule , the migration will not start. The user should detach this backend service from the frontend, or directly migrate its frontend instead. 
4. If an EXTERNAL or INTERNAL_SELF_MANAGED backend service is serving a frontend, the migration is legal. The backend service will not be deleted or recreated, only its backends will be migrated to the target subnet one by one.
5. If an EXTERNAL or INTERNAL_SELF_MANAGED backend service is serving multiple frontends at the same time, the migration can still succeed, but it is not recommended.
6. If multiple backend services are sharing the same backends, the migration will fail and rollback.
7. If there are more than one backends serving this backend service, after the first backend finishes the migration, the tool will be paused and wait until the first backend become partially healthy. After the first backend passes the health check, the tool will continue migrating other backends without further health checks. The tool minimizes or even eliminates the downtime for the backend service migration if it has mutliple backends. 
## Examples:
### 1. A regional backend service (supported loadBalancingScheme: EXTERNAL, INTERNAL, INTERNAL_SELF_MANAGED):
     python3 backend_service_migration.py  --project_id=my-project \
        --region=us-central1-a  --backend_service_name=my-backend-service  \
        --network=my-network  --subnetwork=my-network-subnet1 \

     (Note: you can add --preserve-instance-external-ip=True if you want to preserve the single instances' IP) 
 
### 2. A global backend service (supported loadBalancingScheme: EXTERNAL, INTERNAL, INTERNAL_SELF_MANAGED):
    python3 backend_service_migration.py  --project_id=my-project \
        --backend_service_name=my-backend-service  \
        --network=my-network  --subnetwork=my-network-subnet1 \
    
    (Note: you can add --preserve-instance-external-ip=True if you want to preserve the single instances' IP) 
 
## Special Cases
### 1. A backend service is serving a forwarding rule:
    Not supported. 
    The tool will terminate and will not start the migration. The user should migrate the forwarding rule directly.
### 2. A backend service share the same backends with another backend service or target pool:
    Not supported.
    The tool will rollback.
