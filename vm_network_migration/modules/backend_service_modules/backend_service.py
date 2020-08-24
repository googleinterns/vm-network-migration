# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" BackendService class: describe a backend service.
"""
import logging
from datetime import datetime
import time
from vm_network_migration.utils import initializer


class BackendService(object):

    @initializer
    def __init__(self, compute, project, backend_service_name, network,
                 subnetwork, preserve_instance_external_ip):
        """ Initialization

        Args:
            compute: Google Compute Engine
            project: Project ID
            backend_service_name: name of the backend service
        """

        self.backend_service_configs = None
        self.operations = None

    def log(self):
        logging.basicConfig(filename='backup.log', level=logging.INFO)
        logging.info(
            '-------Backend Service: %s-----' % (self.backend_service_name))
        logging.info(self.backend_service_configs)
        logging.info('--------------------------')

    def get_backend_service_configs(self):
        """ Get the config of the backend service
        """
        pass

    def get_connecting_forwarding_rule_list(self):
        """ Get a list of the forwarding rule which serves this backend service
        """
        pass

    def count_forwarding_rules(self) -> int:
        """ Count the number of forwarding rules connecting this backend service
        to check whether it is only serving a single forwarding rule

        Returns: the number of forwarding rules

        """
        return len(self.get_connecting_forwarding_rule_list())

    def compare_original_network_and_target_network(self) -> bool:
        """ Compare whether the original network and the target network is the same

        Returns: True for same
        """
        return False

    def check_backend_health(self, backend_selfLink):
        """ Check if the backends is healthy

        Args:
            backends_selfLink: url selfLink of the backends (just an instance group)

        Returns: True for healthy

        """
        return True

    def wait_for_backend_become_healthy(self, backend_selfLink, TIME_OUT = 300):
        """ Wait for backend being healthy

        Args:
            backend_selfLink: url selfLink of the backends (just an instance group)
            TIME_OUT: maximum waiting time
        Returns:

        """
        start = datetime.now()
        print('Waiting for %s being healthy with timeout %s seconds.' %(backend_selfLink, TIME_OUT))
        while not self.check_backend_health(backend_selfLink):
            time.sleep(3)
            current_time = datetime.now()
            if (current_time-start).seconds > TIME_OUT:
                print('Health waiting operation is timed out.')
                return
        print('At least one of the instances in %s is healthy.' %(backend_selfLink))