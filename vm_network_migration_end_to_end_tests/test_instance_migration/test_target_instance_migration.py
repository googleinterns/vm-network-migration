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

import unittest
import warnings

import google.auth
from googleapiclient import discovery
from vm_network_migration.handler_helper.selfLink_executor import SelfLinkExecutor
from vm_network_migration_end_to_end_tests.build_test_resource import TestResourceCreator
from vm_network_migration_end_to_end_tests.check_result import *
from vm_network_migration_end_to_end_tests.google_api_interface import GoogleApiInterface
from vm_network_migration_end_to_end_tests.utils import *


class TestTargetInstanceMigration(unittest.TestCase):
    def setUp(self):
        print('Initialize test environment.')
        project = os.environ["PROJECT_ID"]
        credentials, default_project = google.auth.default()
        self.compute = discovery.build('compute', 'v1', credentials=credentials)
        self.google_api_interface = GoogleApiInterface(self.compute,
                                                  project,
                                                  'us-central1',
                                                  'us-central1-a')
        self.test_resource_creator = TestResourceCreator(
            self.google_api_interface)

    def testAttachingAnInternalForwardingRule(self):
        """ A targetInstance is in use by the forwarding rule

        Expectation: both the targetInstance and the forwarding rule will be migrated

        """
        ### create test resources
        forwarding_rule_name = 'end-to-end-test-forwarding-rule'
        target_instance_name = 'end-to-end-test-instance'

        operation = self.test_resource_creator.create_instance_using_template(
            target_instance_name,
            self.test_resource_creator.legacy_instance_template_selfLink)
        instance_selfLink = operation['targetLink']

        target_instance_selfLink = \
            self.test_resource_creator.create_a_target_instance(
                target_instance_name, instance_selfLink)['targetLink']
        original_instance_config = self.google_api_interface.get_instance_configs(
            target_instance_name)
        forwarding_rule_selfLink = \
            self.test_resource_creator.create_regional_forwarding_rule_with_target(
                'sample_tcp_regional_forwarding_rule_internal.json',
                forwarding_rule_name,
                target_instance_selfLink)['targetLink']
        original_forwarding_rule_config = self.google_api_interface.get_regional_forwarding_rule_config(
            forwarding_rule_name)
        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute,
                                             target_instance_selfLink,
                                             self.test_resource_creator.network_name,
                                             self.test_resource_creator.subnetwork_name,
                                             )

        migration_handler = selfLink_executor.build_migration_handler()
        migration_handler.network_migration()

        ### check migration result

        new_forwarding_rule_config = self.google_api_interface.get_regional_forwarding_rule_config(
            forwarding_rule_name)
        self.assertTrue(resource_config_is_unchanged_including_network(
            original_forwarding_rule_config,
            new_forwarding_rule_config))
        # check instance network
        new_instance_config = self.google_api_interface.get_instance_configs(
            target_instance_name)
        self.assertTrue(
            resource_config_is_unchanged_except_for_network(new_instance_config,
                                                            original_instance_config))
        # network changed
        self.assertTrue(check_instance_network(new_instance_config,
                                               self.test_resource_creator.network_selfLink,
                                               self.test_resource_creator.subnetwork_selfLink))

        print('Pass the current test')
    def tearDown(self) -> None:
        pass

    def doCleanups(self) -> None:
        self.google_api_interface.clean_all_resources()


if __name__ == '__main__':
    warnings.filterwarnings(action="ignore", message="unclosed",
                            category=ResourceWarning)
    unittest.main(failfast=True)
