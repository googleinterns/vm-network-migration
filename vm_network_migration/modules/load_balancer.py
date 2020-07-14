class LoadBalancer(object):
    def __init__(self, compute, project, backend_service_name, network, subnetwork, preserve_instance_external_ip):
        """ Initialization

        Args:
            compute: Google Compute Engine
            project: Project ID
            backend_service_name: name of the backend service
        """
        self.compute = compute
        self.project = project
        self.backend_service_name = backend_service_name
        # all instance group backends
        self.backends = None
        self.operations = None
        self.network = network
        self.subnetwork = subnetwork
        self.preserve_instance_external_ip = preserve_instance_external_ip