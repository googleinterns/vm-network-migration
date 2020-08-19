# VM Network Migration
## Limitations:
1. The VM should not be a part of any instance group. Otherwise, the migration will ealy terminate and won’t start.
2. The user can choose to preserve the external IP. If the original VM uses a Ephemeral external IP, and the user chooses to preserve it, it will become a static external IP after the migration. If the user is running out of quota of the static IP, the tool will pick up an Ephemeral IP and continue the migration.
3. The IP preservation action is not reversible, even though rollback happens.
4. The original VM will be deleted and recreated using modified network configuration (tags: network, subnetwork, natIP, networkIP). If the user chooses to preserve the external IP, the ‘natIP’ tag won’t change.
## Examples:
### 1. Migrate an instance without preserving the external IP address:
     python3 instance_migration.py  --project_id=my-project \
        --zone=us-central1-a  --original_instance=my-original-instance  \
        --network=my-network  --subnetwork=my-network-subnet1 \
        --preserve_external_ip=False 
### 2. Migrate an instance with preserving the external IP address:
     (Note: No matter whether its external IP address is a static one or a ephemeral one, 
           it will be reserved as a static IP after the migration. 
           The preserving action is not reversible.)
     python3 instance_migration.py  --project_id=my-project \
         --zone=us-central1-a  --original_instance=my-original-instance  \
         --network=my-network  --subnetwork=my-network-subnet1 \
         --preserve_external_ip=True
## Special cases:
### 1. Migrate an instance which is a member of an instance group:
    Not supported. 
    The tool will terminate and the migration will not start.
    The user should migrate that instance group directly.
### 2. Migrate an instance which is a backend serving one or more target pool:
    Supported, but it is not recommended. 
    The user can still migrate this instance normally. During the migration, 
    this instance will be deleted and recreated. It will affact the target pool.
    After the migration, this instance may still be attached on the target pool. 
    But it is also possible that it has been detached from the target pool. 
    In general, the target pool will be affected. It is not a recommended use case.
### 3. Migrate an instance which serves a target instance:
    Supported.
    The user can still migrate this instance. 
    The target instance will still use this instance.
    