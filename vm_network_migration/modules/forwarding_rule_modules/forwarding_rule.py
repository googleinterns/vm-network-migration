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
"""  ForwardingRule class: describes a forwarding rule

"""
from vm_network_migration.utils import initializer
import logging

class ForwardingRule(object):
    @initializer
    def __init__(self, compute, project, forwarding_rule_name, network,
                 subnetwork):
        """ Initialization

        Args:
            compute: Google Compute Engine
            project: Project ID
            forwarding_rule_name: name of the forwarding rule
            network: target network
            subnetwork: target subnet

        """
        self.forwarding_rule_configs = None
        self.operations = None

        self.migrated = False

    def log(self):
        """ Log the configuration

        Returns:

        """
        logging.basicConfig(filename='backup.log', level=logging.INFO)
        logging.info('-------Forwarding Rule: %s-----' % (self.forwarding_rule_name))
        logging.info(self.forwarding_rule_configs)
        logging.info('--------------------------')

    def get_forwarding_rule_configs(self):
        """ Get the configs of a forwarding rule

        Returns:

        """
        pass

    def check_forwarding_rule_exists(self):
        """ Check if the forwarding rule exists

        Returns:

        """
        pass
