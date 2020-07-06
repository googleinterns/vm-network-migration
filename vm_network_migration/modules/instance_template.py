from vm_network_migration.modules.operations import Operations
from vm_network_migration.utils import generate_timestamp_string

class InstanceTemplate:
    def __init__(self, compute, project, instance_template_name,
                 instance_template_body=None):
        self.compute = compute
        self.project = project
        self.instance_template_name = instance_template_name
        self.operation = Operations(self.compute, self.project, "", "")
        self.instance_template_body = instance_template_body
        if self.instance_template_body == None:
            self.instance_template_body = self.get_instance_template_body()

    def get_instance_template_body(self):
        return self.compute.instanceTemplates().get(project=self.project,
                                                    instanceTemplate=self.instance_template_name).execute()

    def insert(self):
        insert_operation = self.compute.instanceTemplates().insert(
            project=self.project,
            body=self.instance_template_body).execute()
        self.operation.wait_for_global_operation(insert_operation['name'])
        return insert_operation

    def delete(self):
        delete_operation = self.compute.instanceTemplates().delete(
            project=self.project, instanceTemplate=self.instance_template_name)

        self.operation.wait_for_global_operation(delete_operation['name'])
        return delete_operation

    def modify_instance_template_with_new_network(self, new_network_link,
                                                  new_subnetwork_link):
        """ Modify the instance template with the new network links

            Args:
                new_network_link: the selflink of the network
                new_subnetwork_link: the selflink of the subnetwork

        """
        self.instance_template_body['properties']['networkInterfaces'][0][
            'network'] = new_network_link
        self.instance_template_body['properties']['networkInterfaces'][0][
            'subnetwork'] = new_subnetwork_link

    def get_selfLink(self):
        instance_template_body = self.get_instance_template_body()
        return instance_template_body['selfLink']

    def random_change_name(self):
        self.instance_template_name = self.instance_template_name + '-' + generate_timestamp_string()
        self.instance_template_body['name'] = self.instance_template_name
