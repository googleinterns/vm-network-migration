# Forwarding Rule Network Migration
## Limitations:
1. Supported type: ‘EXTERNAL’, ‘INTERNAL’ and ‘INTERAL_SELF_MANAGED’. The ‘INTERNAL_MANAGED’ is not supported, because it can not use a legacy network.
2. All the backend service, target pools, or target instances serving the forwarding rule will be migrated to the VPC subnet.
3. If any of its backends is serving multiple resources, the migration will fail and rollback to the original network.
4. For an INTERNAL or INTERNAL_SELF_MANAGED forwarding rule, it will be deleted and recreated using the new network configuration. For an external forwarding rule, it will not be deleted.
## Examples:
### 1. A regional forwarding rule (supported loadBalancingScheme: EXTERNAL, INTERNAL, INTERNAL_SELF_MANAGED):
     python3 forwarding_rule_migration.py  --project_id=my-project \
        --region=us-central1-a  --forwarding_rule_name=my-forwarding-rule  \
        --network=my-network  --subnetwork=my-network-subnet1 
        
     Note: 
     1. you can add --preserve-instance-external-ip=True if you want to preserve the single instances' IP.
     2. --region tag is only for a regional forwarding rule. 
        For a global forwarding rule, --region shouldn't be specified. 
### 2. A global forwarding rule (supported loadBalancingScheme: EXTERNAL, INTERNAL, INTERNAL_SELF_MANAGED):
     python3 forwarding_rule_migration.py  --project_id=my-project \
        --forwarding_rule_name=my-forwarding-rule  \
        --network=my-network  --subnetwork=my-network-subnet1 
    
     Note: 
     1. you can add --preserve-instance-external-ip=True if you want to preserve the single instances' IP.
     2. --region tag is only for a regional forwarding rule. 
        For a global forwarding rule, --region shouldn't be specified. 
## Special cases:
### 1. An INTERNAL forwarding rule is sharing the same backend service with another forwarding rule:
    Not supported.
    The tool will rollback. 
### 2. An EXTERNAL or INTERNAL-SELF-MANAGED forwarding rule A is sharing the same backend service with another forwarding rule B:
    Supported, but it is not recommended. 
    The tool will still migrate A and all its backend services. After the migration, B will also be served by the migrated backend services. 
### 3. Any kind of forwarding rule is sharing the same target pool or target instance with another forwarding rule:
    Supported, but it is not recommended. 
    Reason: see case2.
 