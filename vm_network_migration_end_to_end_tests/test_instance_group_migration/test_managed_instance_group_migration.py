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
from vm_network_migration.errors import *
from vm_network_migration.handler_helper.selfLink_executor import SelfLinkExecutor
from vm_network_migration_end_to_end_tests.build_test_resource import TestResourceCreator
from vm_network_migration_end_to_end_tests.check_result import *
from vm_network_migration_end_to_end_tests.google_api_interface import GoogleApiInterface
from vm_network_migration_end_to_end_tests.utils import *


class TestManagedInstanceGroupMigration(unittest.TestCase):
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

    def testWithAutoscalerAttached(self):
        # create test resources
        group_name = 'end-to-end-test-managed-instance-group-1'
        operation = self.test_resource_creator.create_regional_managed_instance_group(
            self.test_resource_creator.legacy_instance_template_selfLink,
            group_name,
            'sample_multi_zone_managed_instance_group.json',
            autoscaler_file_name='sample_autoscaler.json')
        instance_group_selfLink = operation['targetLink']
        original_instance_template_configs = self.google_api_interface.get_multi_zone_instance_template_configs(
            group_name)
        original_autoscaler_configs = self.google_api_interface.get_region_autoscaler(
            group_name)

        # start migration
        selfLink_executor = SelfLinkExecutor(self.compute,
                                             instance_group_selfLink,
                                             self.test_resource_creator.network_name,
                                             self.test_resource_creator.subnetwork_name,
                                             )
        migration_handler = selfLink_executor.build_migration_handler()
        migration_handler.network_migration()
        ### check migration result
        new_instance_template_configs = self.google_api_interface.get_multi_zone_instance_template_configs(
            group_name)
        self.assertTrue(
            instance_template_config_is_unchanged_except_for_network_and_name(
                original_instance_template_configs,
                new_instance_template_configs)
        )
        # network changed
        self.assertTrue(
            check_instance_template_network(new_instance_template_configs,
                                            self.test_resource_creator.network_selfLink,
                                            self.test_resource_creator.subnetwork_selfLink))
        # autoscaler doesn't change
        current_autoscaler_configs = self.google_api_interface.get_region_autoscaler(
            group_name)
        self.assertTrue(
            resource_config_is_unchanged_including_network(
                original_autoscaler_configs,
                current_autoscaler_configs))

        print('Pass the current test')

    def testWithoutAutoscalerAttached(self):
        ### create test resources
        group_name = 'end-to-end-test-managed-instance-group-1'
        operation = self.test_resource_creator.create_regional_managed_instance_group(
            self.test_resource_creator.legacy_instance_template_selfLink,
            group_name,
            'sample_multi_zone_managed_instance_group.json')
        instance_group_selfLink = operation['targetLink']
        original_instance_template_configs = self.google_api_interface.get_multi_zone_instance_template_configs(
            group_name)

        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute,
                                             instance_group_selfLink,
                                             self.test_resource_creator.network_name,
                                             self.test_resource_creator.subnetwork_name,
                                             )
        migration_handler = selfLink_executor.build_migration_handler()
        migration_handler.network_migration()
        ### check migration result
        new_instance_template_configs = self.google_api_interface.get_multi_zone_instance_template_configs(
            group_name)
        self.assertTrue(
            instance_template_config_is_unchanged_except_for_network_and_name(
                original_instance_template_configs,
                new_instance_template_configs)
        )
        # network changed
        self.assertTrue(
            check_instance_template_network(new_instance_template_configs,
                                            self.test_resource_creator.network_selfLink,
                                            self.test_resource_creator.subnetwork_selfLink))

        print('Pass the current test')

    def testAsBackendOfTargetPool(self):
        """ The managed instance group serves a target pool.

        Expectation: The migration will not start.

        """
        ### create test resources
        group_name = 'end-to-end-test-managed-instance-group-1'
        instance_group_selfLink = \
            self.test_resource_creator.create_regional_managed_instance_group(
                self.test_resource_creator.legacy_instance_template_selfLink,
                group_name,
                'sample_multi_zone_managed_instance_group.json')[
                'targetLink']
        original_instance_template_configs = self.google_api_interface.get_multi_zone_instance_template_configs(
            group_name)

        target_pool_name = 'end-to-end-test-target-pool'
        self.test_resource_creator.create_target_pool_with_health_check(
            'sample_target_pool_with_no_instance.json',
            target_pool_name,
            [group_name],
            [],
            health_check_selfLink=None)
        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute,
                                             instance_group_selfLink,
                                             self.test_resource_creator.network_name,
                                             self.test_resource_creator.subnetwork_name,
                                             )
        with self.assertRaises(MigrationFailed):
            migration_handler = selfLink_executor.build_migration_handler()
            migration_handler.network_migration()
        ### check migration result
        # the migration didn't start
        new_instance_template_configs = self.google_api_interface.get_multi_zone_instance_template_configs(
            group_name)
        self.assertTrue(resource_config_is_unchanged_including_network(
            new_instance_template_configs, new_instance_template_configs))
        print('Pass the current test')

    def testAsBackendOfBackendService(self):
        """ The managed instance group serves a backend service.

        Expectation: The migration will fail and rollback.

        """
        ### create test resources
        group_name = 'end-to-end-test-managed-instance-group-1'
        instance_group_selfLink = \
            self.test_resource_creator.create_regional_managed_instance_group(
                self.test_resource_creator.legacy_instance_template_selfLink,
                group_name,
                'sample_multi_zone_managed_instance_group.json')[
                'targetLink'].replace('/instanceGroupManagers/',
                                      '/instanceGroups/')
        original_instance_group_config = self.google_api_interface.get_multi_zone_managed_instance_group_configs(
            group_name)
        backend_service_name = 'end-to-end-test-backend-service'
        self.test_resource_creator.create_regional_backend_service(
            'sample_internal_backend_service.json',
            backend_service_name, [instance_group_selfLink])
        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute,
                                             instance_group_selfLink,
                                             self.test_resource_creator.network_name,
                                             self.test_resource_creator.subnetwork_name,
                                             )
        with self.assertRaises(MigrationFailed):
            migration_handler = selfLink_executor.build_migration_handler()
            migration_handler.network_migration()

        ### check migration result
        # the migration is failed and the resources are rolled back
        new_instance_group_config = self.google_api_interface.get_multi_zone_managed_instance_group_configs(
            group_name)
        self.assertTrue(resource_config_is_unchanged_including_network(
            original_instance_group_config, new_instance_group_config))
        print('Pass the current test')

    def tearDown(self) -> None:
        pass

    def doCleanups(self) -> None:
        self.google_api_interface.clean_all_resources()


if __name__ == '__main__':
    warnings.filterwarnings(action="ignore", message="unclosed",
                            category=ResourceWarning)
    unittest.main(failfast=True)
