# Forwarding Rule Network Migration
## Limitations:
1. Supported type: ‘EXTERNAL’, ‘INTERNAL’ and ‘INTERAL_SELF_MANAGED’.
2. All the backend services, target pool, or target instance serving the forwarding rule will be migrated to the VPC subnet.
3. If any of its backends is serving multiple resources, the migration will fail and rollback to the original network.
4. For an INTERNAL or INTERNAL_SELF_MANAGED forwarding rule, it will be deleted and recreated using the new network configuration. If the forwarding rule is using a static internal IP, the IP address will remain the same after the migration. 
5. For an external forwarding rule, it will not be deleted and its external IP will not change.
