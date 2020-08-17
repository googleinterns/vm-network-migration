# Target Pool Network Migration
## Limitations:
1. The target pool can have single VMs or managed instance groups in it.
2. If there is an VM instance which is a member of an unmanaged instance group, it is not allowed. It is an ambiguous situation. Because this unmanaged instance group may have other instances which are not serving this instance group, it is not proper to infer the user wants to migrate the whole group. In this scenario, the migration will not start. The user should detach these instances first, and then migrate this target pool. 
3. If the target pool shares the same backends with another backend service or another target pool, the migration will fail and rollback to the original network.
4. The target pool will not be deleted during the migration. Only its backends will be migrated one by one.
5. If there are more than one backends serving this target pool, after the first backend finishes the migration, the tool will be paused and wait until the first backend become healthy (or partially healthy if the backend is a managed instance group). After the first backend passes the health check, the tool will continue migrating other backends without further health checks. The tool minimizes or even eliminates the downtime for the target pool migration if it has mutliple backends. 


