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

import time
import unittest
import warnings
import google.auth
from vm_network_migration_end_to_end_tests.build_test_resource import TestResourceCreator
from vm_network_migration_end_to_end_tests.check_result import *
from vm_network_migration_end_to_end_tests.google_api_interface import GoogleApiInterface
from googleapiclient import discovery
from vm_network_migration_end_to_end_tests.utils import *
from vm_network_migration.errors import *
from vm_network_migration.handler_helper.selfLink_executor import SelfLinkExecutor


class TestTargetPoolMigration(unittest.TestCase):
    project = os.environ["PROJECT_ID"]
    credentials, default_project = google.auth.default()
    compute = discovery.build('compute', 'v1', credentials=credentials)
    google_api_interface = GoogleApiInterface(compute,
                                              project,
                                              'us-central1',
                                              'us-central1-a')
    test_resource_creator = TestResourceCreator(
        google_api_interface)

    def testOnlyInstancesAsBackend(self):
        ### create test resources
        instance_name_1 = 'end-to-end-test-instance-1'
        operation = self.test_resource_creator.create_instance_using_template(
            instance_name_1,
            self.test_resource_creator.legacy_instance_template_selfLink)
        instance_selfLink_1 = operation['targetLink']
        instance_name_2 = 'end-to-end-test-instance-2'
        operation = self.test_resource_creator.create_instance_using_template(
            instance_name_2,
            self.test_resource_creator.legacy_instance_template_selfLink)
        instance_selfLink_2 = operation['targetLink']
        target_pool_name = 'end-to-end-test-target-pool'
        operation = self.test_resource_creator.create_target_pool_with_health_check(
            'sample_target_pool_with_no_instance.json',
            target_pool_name,
            [],
            [instance_selfLink_1, instance_selfLink_2],
            health_check_selfLink=None)
        target_pool_selfLink = operation['targetLink']
        original_target_pool_instance_list = \
            self.google_api_interface.get_target_pool_config(target_pool_name)[
                'instances']

        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute, target_pool_selfLink,
                                             self.test_resource_creator.network_name,
                                             self.test_resource_creator.subnetwork_name,
                                             )
        migration_handler = selfLink_executor.build_migration_handler()
        migration_handler.network_migration()
        ### check migration result
        new_target_pool_instance_list = \
            self.google_api_interface.get_target_pool_config(target_pool_name)[
                'instances']
        # target pool's instances unchanged
        self.assertTrue(compare_two_list(new_target_pool_instance_list,
                                         original_target_pool_instance_list))
        # instances' network changed
        new_instance_1_config = self.google_api_interface.get_instance_configs(
            instance_name_1)
        self.assertTrue(check_instance_network(new_instance_1_config,
                                               self.test_resource_creator.network_selfLink,
                                               self.test_resource_creator.subnetwork_selfLink))
        new_instance_2_config = self.google_api_interface.get_instance_configs(
            instance_name_2)
        self.assertTrue(check_instance_network(new_instance_2_config,
                                               self.test_resource_creator.network_selfLink,
                                               self.test_resource_creator.subnetwork_selfLink))
        print('Pass the current test')

    def testOnlyManagedInstanceGroupsAsBackend(self):
        ### create resources
        group_name_1 = 'end-to-end-test-managed-instance-group-1'
        self.test_resource_creator.create_regional_managed_instance_group(
            self.test_resource_creator.legacy_instance_template_selfLink,
            group_name_1,
            'sample_multi_zone_managed_instance_group.json',
        )
        original_instance_template_1_configs = self.google_api_interface.get_multi_zone_instance_template_configs(
            group_name_1)
        group_name_2 = 'end-to-end-test-managed-instance-group-2'
        self.test_resource_creator.create_regional_managed_instance_group(
            self.test_resource_creator.legacy_instance_template_selfLink,
            group_name_2,
            'sample_multi_zone_managed_instance_group.json',
        )
        original_instance_template_2_configs = self.google_api_interface.get_multi_zone_instance_template_configs(
            group_name_2)

        target_pool_name = 'end-to-end-test-target-pool'
        operation = self.test_resource_creator.create_target_pool_with_health_check(
            'sample_target_pool_with_no_instance.json',
            target_pool_name,
            [group_name_1, group_name_2],
            [],
            health_check_selfLink=None)
        target_pool_selfLink = operation['targetLink']
        # time allowance to let the instance groups create instances
        time.sleep(20)
        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute, target_pool_selfLink,
                                             self.test_resource_creator.network_name,
                                             self.test_resource_creator.subnetwork_name,
                                             )
        migration_handler = selfLink_executor.build_migration_handler()
        migration_handler.network_migration()
        ### check migration result
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

    def testInstancesAndManagedInstanceGroupsMixedBackends(
            self):
        ### create test resources
        group_name_1 = 'end-to-end-test-managed-instance-group-1'
        self.test_resource_creator.create_regional_managed_instance_group(
            self.test_resource_creator.legacy_instance_template_selfLink,
            group_name_1,
            'sample_multi_zone_managed_instance_group.json',
        )
        original_instance_template_1_configs = self.google_api_interface.get_multi_zone_instance_template_configs(
            group_name_1)
        instance_name_1 = 'end-to-end-test-instance-1'
        operation = self.test_resource_creator.create_instance_using_template(
            instance_name_1,
            self.test_resource_creator.legacy_instance_template_selfLink)
        instance_1_selfLink = operation['targetLink']
        original_instance_1_config = self.google_api_interface.get_instance_configs(
            instance_name_1)
        target_pool_name = 'end-to-end-test-target-pool'
        operation = self.test_resource_creator.create_target_pool_with_health_check(
            'sample_target_pool_with_no_instance.json',
            target_pool_name,
            [group_name_1],
            [instance_1_selfLink],
            health_check_selfLink=None)
        target_pool_selfLink = operation['targetLink']
        # time allowance to let the instance groups create instances
        time.sleep(10)
        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute,
                                             target_pool_selfLink,
                                             self.test_resource_creator.network_name,
                                             self.test_resource_creator.subnetwork_name,
                                             )
        migration_handler = selfLink_executor.build_migration_handler()
        migration_handler.network_migration()
        ### check migration result
        new_instance_template_1_configs = self.google_api_interface.get_multi_zone_instance_template_configs(
            group_name_1)
        self.assertTrue(
            instance_template_config_is_unchanged_except_for_network_and_name(
                original_instance_template_1_configs,
                new_instance_template_1_configs)
        )

        new_instance_1_config = self.google_api_interface.get_instance_configs(
            instance_name_1)
        self.assertTrue(resource_config_is_unchanged_except_for_network(
            original_instance_1_config,
            new_instance_1_config
        ))
        # network changed
        self.assertTrue(
            check_instance_template_network(new_instance_template_1_configs,
                                            self.test_resource_creator.network_selfLink,
                                            self.test_resource_creator.subnetwork_selfLink))
        self.assertTrue(check_instance_network(new_instance_1_config,
                                               self.test_resource_creator.network_selfLink,
                                               self.test_resource_creator.subnetwork_selfLink))
        print('Pass the current test')

    def testWithInstancesFromAnUnmanagedInstanceGroup(
            self):
        ### create resources
        instance_name_1 = 'end-to-end-test-instance-1'
        operation = self.test_resource_creator.create_instance_using_template(
            instance_name_1,
            self.test_resource_creator.legacy_instance_template_selfLink)
        instance_selfLink_1 = operation['targetLink']

        instance_name_2 = 'end-to-end-test-instance-2'
        operation = self.test_resource_creator.create_instance_using_template(
            instance_name_2,
            self.test_resource_creator.legacy_instance_template_selfLink)
        instance_selfLink_2 = operation['targetLink']

        unmanaged_instance_group_name = 'end-to-end-test-unmanaged-instance-group-1'
        original_instances_in_group = [instance_name_1, instance_name_2]
        self.test_resource_creator.create_unmanaged_instance_group(
            unmanaged_instance_group_name,
            original_instances_in_group)
        original_group_config = self.google_api_interface.get_unmanaged_instance_group_configs(
            unmanaged_instance_group_name)

        target_pool_name = 'end-to-end-test-target-pool'
        operation = self.test_resource_creator.create_target_pool_with_health_check(
            'sample_target_pool_with_no_instance.json',
            target_pool_name,
            [],
            [instance_selfLink_1, instance_selfLink_2],
            health_check_selfLink=None)

        target_pool_selfLink = operation['targetLink']
        original_target_pool_config = self.google_api_interface.get_target_pool_config(
            target_pool_name)

        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute,
                                             target_pool_selfLink,
                                             self.test_resource_creator.network_name,
                                             self.test_resource_creator.subnetwork_name,
                                             )

        try:
            migration_handler = selfLink_executor.build_migration_handler()
            migration_handler.network_migration()
        except Exception as e:
            # the migration will not start, and raise an error
            self.assertTrue(isinstance(e, AmbiguousTargetResource))
        ### check migration result
        # unmanaged instance group doesn't change
        new_group_config = self.google_api_interface.get_unmanaged_instance_group_configs(
            unmanaged_instance_group_name)
        self.assertEqual(original_group_config, new_group_config)
        # target pool is unchanged
        new_target_pool_config = self.google_api_interface.get_target_pool_config(
            target_pool_name)
        self.assertEqual(original_target_pool_config, new_target_pool_config)

        print('Pass the current test')

    def tearDown(self) -> None:
        pass

    def doCleanups(self) -> None:
        self.google_api_interface.clean_all_resources()


if __name__ == '__main__':
    warnings.filterwarnings(action="ignore", message="unclosed",
                            category=ResourceWarning)
    unittest.main(failfast=True)
