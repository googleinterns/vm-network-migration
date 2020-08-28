# Target Instance Network Migration
## Characteristics:
1. The target instance network migration is the same as the VM instance migration. Therefore, please refer **Characteristics** in the [VM instance migration](./VM_INSTANCE_README.md) 
## Limitations:
please refer **Limitation** in the [VM instance migration](./VM_INSTANCE_README.md) 
## Special cases:
### 1. Migrate a target instance which is serving an INTERNAL forwarding rule:
Supported. \
After the migration, the target instance will be migrated and still serve its forwarding rule. However, the INTERNAL forwarding rule's network won't change.
    