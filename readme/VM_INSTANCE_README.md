# VM Network Migration
## Limitations:
1. The VM should not be a part of any instance group. Otherwise, the migration will ealy terminate and won’t start.
2. The user can choose to preserve the external IP. If the original VM uses a Ephemeral external IP, and the user chooses to preserve it, it will become a static external IP after the migration. If the user is running out of quota of the static IP, the tool will pick up an Ephemeral IP and continue the migration.
3. The original VM will be deleted and recreated using modified network configuration (tags: network, subnetwork, natIP, networkIP). If the user chooses to preserve the external IP, the ‘natIP’ tag won’t change.

## Examples:
### 1. Migrate an instance without preserving the external IP address:
     python3 instance_network_migration.py  --project=my-project \
        --zone=us-central1-a  --original_instance=my-original-instance  \
        --network=my-network  --subnetwork=my-network-subnet1 \
        --preserve_external_ip=False 
### 2. Migrate an instance with preserving the external IP address:
Note: No matter whether its external IP address is a static one or a ephemeral one, 
it will be reserved as a static IP after the migration. The preserving action is not reversible. 

     python3 instance_network_migration.py  --project=my-project \
         --zone=us-central1-a  --original_instance=my-original-instance  \
         --network=my-network  --subnetwork=my-network-subnet1 \
         --preserve_external_ip=True
          
