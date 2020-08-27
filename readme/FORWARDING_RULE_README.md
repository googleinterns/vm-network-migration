# Forwarding Rule Network Migration
## Characteristics:
*  The forwarding rule itself and the backend services, target pools, or target instances used by this forwarding rule will be migrated to the target subnet.
### EXTERNAL forwarding rule:
* The external IP of the forwarding rule will not change.
* The forwarding rule itself will not be modified, because it doesn't live in a network. 
* The downtime can be minimized or eliminated. For further explanation: see **Characteristic** in [Target pool migration](./TARGET_POOL_README.md) and [Backend service migration](./BACKEND_SERVICE_README.md)
* An EXTERNAL forwarding rule can have a target proxy as its target. A target proxy routes the requests to a URL map. All the backend services referred by this URL map will be migrated to the target subnet.
### INTERNAL or INTERNAL_SELF_MANAGED forwarding rule:
* The forwarding rule itself will be deleted and recreated using the new network configuration. 
## Limitations:
* If the forwarding rule is using a backend service (or using a target proxy routing to multiple backend services), see **Limitations** in [Backend service migration](./BACKEND_SERVICE_README.md)
* If the forwarding rule is using a target pool (or using a target pool which has a backup pool), see **Limitations** in [Target pool migration](./TARGET_POOL_README.md)
* If the forwarding rule is using a target instance, see **Limitations** in [VM instance migration](./VM_INSTANCE_README.md)
## Examples:
### 1. A regional forwarding rule (it can be EXTERNAL or INTERNAL):
     python3 forwarding_rule_migration.py  --project_id=my-project \
        --forwarding_rule_name=my-forwarding-rule \
        --region=us-central1-a \
        --network=my-network \
        [--subnetwork=my-network-subnet1 --preserve_instance_external_ip=False]
     
### 2. A global forwarding rule (it can be EXTERNAL or INTERNAL_SELF_MANAGED):
     python3 forwarding_rule_migration.py  --project_id=my-project \
        --forwarding_rule_name=my-forwarding-rule \
        --network=my-network \
        [--subnetwork=my-network-subnet1 --preserve_instance_external_ip=False]
        
## Special cases:
### 1. An INTERNAL forwarding rule shares a backend service with another forwarding rule:
Not supported. \
The migration of the INTERNAL forwarding rule will fail. The tool will rollback. \
*Recommendation*: Remove this backend service from another forwarding rule and try again.
### 2. An EXTERNAL or INTERNAL-SELF-MANAGED forwarding rule A shares a backend service with another forwarding rule B:
Supported. \
The tool will still migrate the forwarding rule A and all its backend services. 
After the migration, B will also be served by the migrated backend services. 
### 3. Any kind of forwarding rule shares the same target pool or target instance with another forwarding rule:
Supported. \
Further explanation: see case 2.
 