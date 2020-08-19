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

import google.auth
from googleapiclient import discovery
from vm_network_migration.handler_helper.selfLink_executor import SelfLinkExecutor
from vm_network_migration_end_to_end_tests.build_test_resource import TestResourceCreator
from vm_network_migration_end_to_end_tests.check_result import *
from vm_network_migration_end_to_end_tests.google_api_interface import GoogleApiInterface
from vm_network_migration_end_to_end_tests.utils import *


class TestInternalForwardingRuleMigration(unittest.TestCase):
    project = os.environ["PROJECT_ID"]
    credentials, default_project = google.auth.default()
    compute = discovery.build('compute', 'v1', credentials=credentials)
    google_api_interface = GoogleApiInterface(compute,
                                              project,
                                              'us-central1',
                                              'us-central1-a')
    test_resource_creator = TestResourceCreator(
        google_api_interface)

    def testWithBackendServiceAttached(self):
        ### create test resources
        forwarding_rule_name = 'end-to-end-test-forwarding-rule'
        backend_service_name = 'end-to-end-test-backend-service'
        group_name_1 = 'end-to-end-test-managed-instance-group-1'
        operation = self.test_resource_creator.create_regional_managed_instance_group(
            self.test_resource_creator.legacy_instance_template_selfLink,
            group_name_1,
            'sample_multi_zone_managed_instance_group.json',
        )
        instance_group_1_selfLink = operation['targetLink'].replace(
            '/instanceGroupManagers/', '/instanceGroups/')
        original_instance_template_1_configs = self.google_api_interface.get_multi_zone_instance_template_configs(
            group_name_1)

        backend_service_selfLink = \
            self.test_resource_creator.create_regional_backend_service(
                'sample_internal_backend_service.json',
                backend_service_name, [instance_group_1_selfLink])['targetLink']
        original_backend_service_configs = self.google_api_interface.get_regional_backend_service_configs(
            backend_service_name)
        forwarding_rule_selfLink = \
            self.test_resource_creator.create_regional_forwarding_rule_with_backend_service(
                'sample_tcp_regional_forwarding_rule_internal.json',
                forwarding_rule_name,
                backend_service_selfLink)['targetLink']
        original_forwarding_rule_config = self.google_api_interface.get_regional_forwarding_rule_config(
            forwarding_rule_name)
        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute,
                                             forwarding_rule_selfLink,
                                             self.test_resource_creator.network_name,
                                             self.test_resource_creator.subnetwork_name,
                                             )

        migration_handler = selfLink_executor.build_migration_handler()
        migration_handler.network_migration()

        ### check migration result
        # check internal forwarding rule
        new_forwarding_rule_config = self.google_api_interface.get_regional_forwarding_rule_config(
            forwarding_rule_name)
        self.assertTrue(resource_config_is_unchanged_except_for_network(
            original_forwarding_rule_config,
            new_forwarding_rule_config))
        self.assertTrue(
            check_selfLink_equal(new_forwarding_rule_config['network'],
                                 self.test_resource_creator.network_selfLink))

        # check backend service config
        new_backend_service_configs = self.google_api_interface.get_regional_backend_service_configs(
            backend_service_name)
        self.assertTrue(resource_config_is_unchanged_except_for_network(
            original_backend_service_configs,
            new_backend_service_configs))
        self.assertEqual(new_backend_service_configs['network'],
                         self.test_resource_creator.network_selfLink)
        # check its backends
        new_instance_template_1_configs = self.google_api_interface.get_multi_zone_instance_template_configs \
                (
                group_name_1)
        self.assertTrue(
            instance_template_config_is_unchanged_except_for_network_and_name(
                original_instance_template_1_configs,
                new_instance_template_1_configs)
        )
        self.assertTrue(
            check_instance_template_network(new_instance_template_1_configs,
                                            self.test_resource_creator.network_selfLink,
                                            self.test_resource_creator.subnetwork_selfLink))

        print('Pass the current test')

    def testWithTargetInstanceAttached(self):
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
                                             forwarding_rule_selfLink,
                                             self.test_resource_creator.network_name,
                                             self.test_resource_creator.subnetwork_name,
                                             )

        migration_handler = selfLink_executor.build_migration_handler()
        migration_handler.network_migration()

        ### check migration result
        # check internal forwarding rule network
        new_forwarding_rule_config = self.google_api_interface.get_regional_forwarding_rule_config(
            forwarding_rule_name)
        self.assertTrue(
            resource_config_is_unchanged_except_for_network(
                original_forwarding_rule_config,
                new_forwarding_rule_config))
        self.assertEqual(new_forwarding_rule_config['network'],
                         self.test_resource_creator.network_selfLink)

        self.assertTrue(
            check_selfLink_equal(new_forwarding_rule_config['network'],
                                 self.test_resource_creator.network_selfLink))

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
    unittest.main(failfast=True)
