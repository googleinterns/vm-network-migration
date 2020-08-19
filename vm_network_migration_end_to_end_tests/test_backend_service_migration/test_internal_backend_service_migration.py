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
from vm_network_migration_end_to_end_tests.build_test_resource import TestResourceCreator
from vm_network_migration_end_to_end_tests.check_result import *
from vm_network_migration_end_to_end_tests.google_api_interface import GoogleApiInterface
from googleapiclient import discovery
from vm_network_migration_end_to_end_tests.utils import *
from vm_network_migration.handler_helper.selfLink_executor import SelfLinkExecutor


class TestInternalBackendServiceMigration(unittest.TestCase):
    project = os.environ["PROJECT_ID"]
    credentials, default_project = google.auth.default()
    compute = discovery.build('compute', 'v1', credentials=credentials)
    google_api_interface = GoogleApiInterface(compute,
                                              project,
                                              'us-central1',
                                              'us-central1-a')
    test_resource_creator = TestResourceCreator(
        google_api_interface)

    def testWithMultipleBackends(self):
        ### create test resources
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
        group_name_2 = 'end-to-end-test-managed-instance-group-2'
        operation = self.test_resource_creator.create_regional_managed_instance_group(
            self.test_resource_creator.legacy_instance_template_selfLink,
            group_name_2,
            'sample_multi_zone_managed_instance_group.json',
        )
        instance_group_2_selfLink = operation['targetLink'].replace(
            '/instanceGroupManagers/', '/instanceGroups/')
        original_instance_template_2_configs = self.google_api_interface.get_multi_zone_instance_template_configs(
            group_name_2)

        original_backend_selfLinks = [instance_group_2_selfLink,
                                      instance_group_1_selfLink]
        operation = self.test_resource_creator.create_regional_backend_service(
            'sample_internal_backend_service.json',
            backend_service_name, original_backend_selfLinks)

        backend_service_selfLink = operation['targetLink']
        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute,
                                             backend_service_selfLink,
                                             self.test_resource_creator.network_name,
                                             self.test_resource_creator.subnetwork_name,
                                             )
        migration_handler = selfLink_executor.build_migration_handler()
        migration_handler.network_migration()
        ### check migration result
        new_backend_service_configs = self.google_api_interface.get_regional_backend_service_configs(
            backend_service_name)
        new_backend_selfLinks = self.google_api_interface.get_backends_links_from_backend_service_configs(
            new_backend_service_configs)
        # check backend service config
        self.assertTrue(
            check_selfLink_equal(new_backend_service_configs['network'],
                                 self.test_resource_creator.network_selfLink))
        self.assertTrue(
            compare_two_list(original_backend_selfLinks, new_backend_selfLinks))
        # check its backends
        new_instance_template_1_configs = self.google_api_interface.get_multi_zone_instance_template_configs(
            group_name_1)
        new_instance_template_2_configs = self.google_api_interface.get_multi_zone_instance_template_configs(
            group_name_2)
        self.assertTrue(
            instance_template_config_is_unchanged_except_for_network_and_name(
                original_instance_template_1_configs,
                new_instance_template_1_configs)
        )
        self.assertTrue(
            instance_template_config_is_unchanged_except_for_network_and_name(
                original_instance_template_2_configs,
                new_instance_template_2_configs)
        )
        # network changed
        self.assertTrue(
            check_instance_template_network(new_instance_template_1_configs,
                                            self.test_resource_creator.network_selfLink,
                                            self.test_resource_creator.subnetwork_selfLink))

        self.assertTrue(
            check_instance_template_network(new_instance_template_2_configs,
                                            self.test_resource_creator.network_selfLink,
                                            self.test_resource_creator.subnetwork_selfLink))
        print('Pass the current test')

    def testWithNoBackends(self):
        ### create test resources
        backend_service_name = 'end-to-end-test-backend-service'
        operation = self.test_resource_creator.create_regional_backend_service(
            'sample_internal_backend_service.json',
            backend_service_name, [])
        original_backend_service_configs = self.google_api_interface.get_regional_backend_service_configs(
            backend_service_name)
        backend_service_selfLink = operation['targetLink']
        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute,
                                             backend_service_selfLink,
                                             self.test_resource_creator.network_name,
                                             self.test_resource_creator.subnetwork_name,
                                             )
        migration_handler = selfLink_executor.build_migration_handler()
        migration_handler.network_migration()
        ### check migration result
        new_backend_service_configs = self.google_api_interface.get_regional_backend_service_configs(
            backend_service_name)

        # check backend service config
        self.assertTrue(
            check_selfLink_equal(new_backend_service_configs['network'],
                                 self.test_resource_creator.network_selfLink))
        self.assertTrue(resource_config_is_unchanged_except_for_network(
            original_backend_service_configs,
            new_backend_service_configs))
        print('Pass the current test')

    def testWithForwardingRuleAttached(self):
        ### create test resources
        backend_service_name = 'end-to-end-test-backend-service'
        original_backend_selfLinks = []
        operation = self.test_resource_creator.create_regional_backend_service(
            'sample_internal_backend_service.json',
            backend_service_name, original_backend_selfLinks)
        original_backend_service_configs = self.google_api_interface.get_regional_backend_service_configs(
            backend_service_name)
        backend_service_selfLink = operation['targetLink']
        self.test_resource_creator.create_regional_forwarding_rule_with_backend_service(
            'sample_tcp_regional_forwarding_rule_internal.json',
            backend_service_name,
            backend_service_selfLink)
        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute,
                                             backend_service_selfLink,
                                             self.test_resource_creator.network_name,
                                             self.test_resource_creator.subnetwork_name,
                                             )

        migration_handler = selfLink_executor.build_migration_handler()
        migration_handler.network_migration()

        ### check migration result
        # migration didn't start
        new_backend_service_configs = self.google_api_interface.get_regional_backend_service_configs(
            backend_service_name)
        self.assertTrue(resource_config_is_unchanged_including_network(
            original_backend_service_configs, new_backend_service_configs))
        print('Pass the current test')

    def tearDown(self) -> None:
        pass

    def doCleanups(self) -> None:
        self.google_api_interface.clean_all_resources()


if __name__ == '__main__':
    warnings.filterwarnings(action="ignore", message="unclosed",
                            category=ResourceWarning)
    unittest.main(failfast=True)
