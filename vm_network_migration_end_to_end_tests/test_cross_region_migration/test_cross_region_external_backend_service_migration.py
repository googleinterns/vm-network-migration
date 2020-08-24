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


class TestCrossRegionExternalBackendServiceMigration(unittest.TestCase):
    def setUp(self):
        print('Initialize test environment.')
        project = os.environ["PROJECT_ID"]
        credentials, default_project = google.auth.default()
        self.compute = discovery.build('compute', 'v1', credentials=credentials)
        self.google_api_interface_region_1 = GoogleApiInterface(self.compute,
                                                                project,
                                                                'us-central1',
                                                                'us-central1-a')
        self.test_resource_creator_region_1 = TestResourceCreator(
            self.google_api_interface_region_1)
        self.google_api_interface_region_2 = GoogleApiInterface(self.compute,
                                                                project,
                                                                'us-east1',
                                                                'us-east1-b')
        self.test_resource_creator_region_2 = TestResourceCreator(
            self.google_api_interface_region_2
        )

    def testAutomodeSubnetworkExistsInBothRegions(self):
        """ A backend service has two instance groups from two regions as backends.
        The network is an auto-mode network, and it has subnet with the same name
        in all regions.

        Expectation: all the backends will be migrated

        """
        ### create test resources
        auto_subnetwork_name = 'end-to-end-test-auto-subnetwork'
        try:
            target_network_selfLink = \
                self.google_api_interface_region_1.get_network(
                    auto_subnetwork_name)['selfLink']
        except:
            target_network_selfLink = \
                self.google_api_interface_region_1.create_auto_subnetwork(
                    auto_subnetwork_name)[
                    'targetLink']

        group_name_1 = 'end-to-end-test-managed-instance-group-1'
        operation = self.test_resource_creator_region_1.create_regional_managed_instance_group(
            self.test_resource_creator_region_1.legacy_instance_template_selfLink,
            group_name_1,
            'sample_multi_zone_managed_instance_group.json',
        )
        instance_group_1_selfLink = operation['targetLink'].replace(
            '/instanceGroupManagers/', '/instanceGroups/')
        original_instance_template_1_configs = self.google_api_interface_region_1.get_multi_zone_instance_template_configs(
            group_name_1)
        group_name_2 = 'end-to-end-test-managed-instance-group-2'
        operation = self.test_resource_creator_region_2.create_regional_managed_instance_group(
            self.test_resource_creator_region_2.legacy_instance_template_selfLink,
            group_name_2,
            'sample_multi_zone_managed_instance_group.json',
        )
        instance_group_2_selfLink = operation['targetLink'].replace(
            '/instanceGroupManagers/', '/instanceGroups/')
        original_instance_template_2_configs = self.google_api_interface_region_2.get_multi_zone_instance_template_configs(
            group_name_2)

        backend_service_name = 'end-to-end-test-backend-service'
        operation = self.test_resource_creator_region_1.create_global_backend_service(
            'sample_external_backend_service.json',
            backend_service_name, [instance_group_2_selfLink,
                                   instance_group_1_selfLink])
        original_backend_service_configs = self.google_api_interface_region_1.get_global_backend_service_configs(
            backend_service_name)
        backend_service_selfLink = operation['targetLink']
        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute,
                                             backend_service_selfLink,
                                             auto_subnetwork_name,
                                             auto_subnetwork_name
                                             )
        migration_handler = selfLink_executor.build_migration_handler()
        migration_handler.network_migration()
        ### check migration result
        new_backend_service_configs = self.google_api_interface_region_1.get_global_backend_service_configs(
            backend_service_name)

        # check backend service config
        self.assertTrue(
            resource_config_is_unchanged_including_network(
                original_backend_service_configs, new_backend_service_configs))
        # check its backends
        new_instance_template_1_configs = self.google_api_interface_region_1.get_multi_zone_instance_template_configs(
            group_name_1)
        new_instance_template_2_configs = self.google_api_interface_region_2.get_multi_zone_instance_template_configs(
            group_name_2)
        self.assertTrue(
            instance_template_config_is_unchanged_except_for_network_and_name(
                original_instance_template_1_configs,
                new_instance_template_1_configs))
        self.assertTrue(
            instance_template_config_is_unchanged_except_for_network_and_name(
                original_instance_template_2_configs,
                new_instance_template_2_configs))

        # network changed
        self.assertTrue(
            check_instance_template_network(new_instance_template_1_configs,
                                            target_network_selfLink))

        self.assertTrue(
            check_instance_template_network(new_instance_template_2_configs,
                                            target_network_selfLink))

        print('Pass the current test')

    def testCustomSubnetworkExistsInBothRegions(self):
        """ A backend service has two instance groups from two regions as backends.

         Expectation: all the backends will be migrated

         """
        ### create test resources

        group_name_1 = 'end-to-end-test-managed-instance-group-1'
        operation = self.test_resource_creator_region_1.create_regional_managed_instance_group(
            self.test_resource_creator_region_1.legacy_instance_template_selfLink,
            group_name_1,
            'sample_multi_zone_managed_instance_group.json',
        )
        instance_group_1_selfLink = operation['targetLink'].replace(
            '/instanceGroupManagers/', '/instanceGroups/')
        original_instance_template_1_configs = self.google_api_interface_region_1.get_multi_zone_instance_template_configs(
            group_name_1)
        group_name_2 = 'end-to-end-test-managed-instance-group-2'
        operation = self.test_resource_creator_region_2.create_regional_managed_instance_group(
            self.test_resource_creator_region_2.legacy_instance_template_selfLink,
            group_name_2,
            'sample_multi_zone_managed_instance_group.json',
        )
        instance_group_2_selfLink = operation['targetLink'].replace(
            '/instanceGroupManagers/', '/instanceGroups/')
        original_instance_template_2_configs = self.google_api_interface_region_2.get_multi_zone_instance_template_configs(
            group_name_2)

        backend_service_name = 'end-to-end-test-backend-service'
        operation = self.test_resource_creator_region_1.create_global_backend_service(
            'sample_external_backend_service.json',
            backend_service_name, [instance_group_2_selfLink,
                                   instance_group_1_selfLink])
        original_backend_service_configs = self.google_api_interface_region_1.get_global_backend_service_configs(
            backend_service_name)
        backend_service_selfLink = operation['targetLink']
        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute,
                                             backend_service_selfLink,
                                             self.test_resource_creator_region_1.network_name,
                                             self.test_resource_creator_region_1.subnetwork_name
                                             )
        migration_handler = selfLink_executor.build_migration_handler()
        migration_handler.network_migration()
        ### check migration result
        new_backend_service_configs = self.google_api_interface_region_1.get_global_backend_service_configs(
            backend_service_name)

        # check backend service config
        self.assertTrue(
            resource_config_is_unchanged_including_network(
                original_backend_service_configs, new_backend_service_configs))
        # check its backends
        new_instance_template_1_configs = self.google_api_interface_region_1.get_multi_zone_instance_template_configs(
            group_name_1)
        new_instance_template_2_configs = self.google_api_interface_region_2.get_multi_zone_instance_template_configs(
            group_name_2)
        self.assertTrue(
            instance_template_config_is_unchanged_except_for_network_and_name(
                original_instance_template_1_configs,
                new_instance_template_1_configs))
        self.assertTrue(
            instance_template_config_is_unchanged_except_for_network_and_name(
                original_instance_template_2_configs,
                new_instance_template_2_configs))

        # network changed
        self.assertTrue(
            check_instance_template_network(new_instance_template_1_configs,
                                            self.test_resource_creator_region_1.network_selfLink,
                                            self.test_resource_creator_region_1.subnetwork_selfLink))

        self.assertTrue(
            check_instance_template_network(new_instance_template_2_configs,
                                            self.test_resource_creator_region_2.network_selfLink,
                                            self.test_resource_creator_region_2.subnetwork_selfLink))

        print('Pass the current test')

    def testCustomSubnetworkExistsInOnlyOneRegion(self):
        """ A backend service has two instance groups from two regions as backends.

         Expectation: rollback will happen

        """
        ### create test resources
        target_subnetwork_name = 'subnetwork-only-in-region-1'
        target_subnetwork_selfLink = \
            self.google_api_interface_region_1.create_subnetwork_using_random_ip_range(
                target_subnetwork_name,
                self.test_resource_creator_region_1.network_selfLink
            )['targetLink']
        group_name_1 = 'end-to-end-test-managed-instance-group-1'
        operation = self.test_resource_creator_region_1.create_regional_managed_instance_group(
            self.test_resource_creator_region_1.legacy_instance_template_selfLink,
            group_name_1,
            'sample_multi_zone_managed_instance_group.json',
        )
        instance_group_1_selfLink = operation['targetLink'].replace(
            '/instanceGroupManagers/', '/instanceGroups/')
        original_instance_template_1_configs = self.google_api_interface_region_1.get_multi_zone_instance_template_configs(
            group_name_1)
        group_name_2 = 'end-to-end-test-managed-instance-group-2'
        operation = self.test_resource_creator_region_2.create_regional_managed_instance_group(
            self.test_resource_creator_region_2.legacy_instance_template_selfLink,
            group_name_2,
            'sample_multi_zone_managed_instance_group.json',
        )
        instance_group_2_selfLink = operation['targetLink'].replace(
            '/instanceGroupManagers/', '/instanceGroups/')
        original_instance_template_2_configs = self.google_api_interface_region_2.get_multi_zone_instance_template_configs(
            group_name_2)

        backend_service_name = 'end-to-end-test-backend-service'
        operation = self.test_resource_creator_region_1.create_global_backend_service(
            'sample_external_backend_service.json',
            backend_service_name, [instance_group_2_selfLink,
                                   instance_group_1_selfLink])
        original_backend_service_configs = self.google_api_interface_region_1.get_global_backend_service_configs(
            backend_service_name)
        backend_service_selfLink = operation['targetLink']
        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute,
                                             backend_service_selfLink,
                                             self.test_resource_creator_region_1.network_name,
                                             target_subnetwork_name
                                             )
        with self.assertRaises(MigrationFailed):
            migration_handler = selfLink_executor.build_migration_handler()
            migration_handler.network_migration()
        ### check migration result
        new_backend_service_configs = self.google_api_interface_region_1.get_global_backend_service_configs(
            backend_service_name)

        # check backend service config
        self.assertTrue(
            resource_config_is_unchanged_including_network(
                original_backend_service_configs, new_backend_service_configs))
        # check its backends
        new_instance_template_1_configs = self.google_api_interface_region_1.get_multi_zone_instance_template_configs(
            group_name_1)
        new_instance_template_2_configs = self.google_api_interface_region_2.get_multi_zone_instance_template_configs(
            group_name_2)
        # configs are unchanged including network
        self.assertTrue(
            instance_template_config_is_unchanged(
                original_instance_template_1_configs,
                new_instance_template_1_configs))
        self.assertTrue(
            instance_template_config_is_unchanged(
                original_instance_template_2_configs,
                new_instance_template_2_configs))

        print('Pass the current test')

    def tearDown(self) -> None:
        pass

    def doCleanups(self) -> None:
        self.google_api_interface_region_1.clean_all_resources()
        self.google_api_interface_region_2.clean_all_resources()


if __name__ == '__main__':
    warnings.filterwarnings(action="ignore", message="unclosed",
                            category=ResourceWarning)
    unittest.main(failfast=True)
