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


class TestCrossTwoRegionTargetPoolMigration(unittest.TestCase):
    project = os.environ["PROJECT_ID"]
    credentials, default_project = google.auth.default()
    compute = discovery.build('compute', 'v1', credentials=credentials)
    google_api_interface_region_1 = GoogleApiInterface(compute,
                                              project,
                                              'us-central1',
                                              'us-central1-a')
    test_resource_creator_region_1 = TestResourceCreator(
        google_api_interface_region_1)
    google_api_interface_region_2 = GoogleApiInterface(compute,
                                              project,
                                              'us-east1',
                                              'us-east1-a')
    test_resource_creator_region_2 = TestResourceCreator(
        google_api_interface_region_2
    )


    def testSubnetworkExistsInBothRegions(self):
        """ The target pool has single instances as its backends, no instance groups
        """
        ### create test resources
        auto_subnetwork_name = 'end-to-end-test-auto-subnetwork'
        target_network_selfLink = \
            self.google_api_interface_region_1.create_auto_subnetwork(auto_subnetwork_name)[
                'targetLink']

        instance_in_region_1 = 'end-to-end-test-instance-region-1'
        instance_in_region_1_selfLink = self.test_resource_creator_region_1.create_instance_using_template(
            instance_in_region_1,
            self.test_resource_creator_region_1.legacy_instance_template_selfLink)['targetLink']
        original_instance_in_region_1_config = self.google_api_interface_region_1.get_instance_configs(instance_in_region_1)
        instance_in_region_2 = 'end-to-end-test-instance-region-1'
        instance_in_region_2_selfLink = self.test_resource_creator_region_2.create_instance_using_template(
            instance_in_region_2,
            self.test_resource_creator_region_2.legacy_instance_template_selfLink)['targetLink']
        original_instance_in_region_2_config = self.google_api_interface_region_2.get_instance_configs(instance_in_region_2)

        target_pool_name = 'end-to-end-test-target-pool'
        target_pool_selfLink = self.test_resource_creator_region_1.create_target_pool_with_health_check(
            'sample_target_pool_with_no_instance.json',
            target_pool_name,
            [],
            [instance_in_region_1_selfLink, instance_in_region_2_selfLink],
            health_check_selfLink=None)['targetLink']
        original_target_pool_config = self.google_api_interface_region_1.get_target_pool_config(target_pool_name)
        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute,
                                             target_pool_selfLink,
                                             auto_subnetwork_name,
                                             auto_subnetwork_name
                                             )
        migration_handler = selfLink_executor.build_migration_handler()
        migration_handler.network_migration()
        ### check migration result
        new_target_pool_config = self.google_api_interface_region_1.get_target_pool_config(target_pool_name)
        new_instance_in_region_1_config = self.google_api_interface_region_1.get_instance_configs(instance_in_region_1)
        new_instance_in_region_2_config = self.google_api_interface_region_2.get_instance_configs(instance_in_region_2)


        # target pool configuration is unchanged
        self.assertTrue(resource_config_is_unchanged_including_network(original_target_pool_config, new_target_pool_config))
        # instances' network changed
        self.assertTrue(resource_config_is_unchanged_except_for_network(original_instance_in_region_1_config, new_instance_in_region_1_config))
        self.assertTrue(resource_config_is_unchanged_except_for_network(original_instance_in_region_2_config, new_instance_in_region_2_config))

        self.assertTrue(check_instance_network(new_instance_in_region_1_config,
                                               target_network_selfLink))
        self.assertTrue(check_instance_network(new_instance_in_region_2_config,
                                               target_network_selfLink))
        print('Pass the current test')

    def testSubnetworkNotExistsInBothRegions(self):
        """ The target pool has single instances as its backends, no instance groups
        """
        ### create test resources
        instance_in_region_1 = 'end-to-end-test-instance-region-1'
        instance_in_region_1_selfLink = \
        self.test_resource_creator_region_1.create_instance_using_template(
            instance_in_region_1,
            self.test_resource_creator_region_1.legacy_instance_template_selfLink)[
            'targetLink']
        original_instance_in_region_1_config = self.google_api_interface_region_1.get_instance_configs(
            instance_in_region_1)
        instance_in_region_2 = 'end-to-end-test-instance-region-1'
        instance_in_region_2_selfLink = \
        self.test_resource_creator_region_2.create_instance_using_template(
            instance_in_region_2,
            self.test_resource_creator_region_2.legacy_instance_template_selfLink)[
            'targetLink']
        original_instance_in_region_2_config = self.google_api_interface_region_2.get_instance_configs(
            instance_in_region_2)

        target_pool_name = 'end-to-end-test-target-pool'
        target_pool_selfLink = \
        self.test_resource_creator_region_1.create_target_pool_with_health_check(
            'sample_target_pool_with_no_instance.json',
            target_pool_name,
            [],
            [instance_in_region_1_selfLink, instance_in_region_2_selfLink],
            health_check_selfLink=None)['targetLink']
        original_target_pool_config = self.google_api_interface_region_1.get_target_pool_config(
            target_pool_name)
        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute,
                                             target_pool_selfLink,
                                             self.test_resource_creator_region_1.network_name,
                                             self.test_resource_creator_region_1.subnetwork_name,
                                             )

        migration_handler = selfLink_executor.build_migration_handler()
        migration_handler.network_migration()

        ### check migration result
        new_target_pool_config = self.google_api_interface_region_1.get_target_pool_config(
            target_pool_name)
        new_instance_in_region_1_config = self.google_api_interface_region_1.get_instance_configs(
            instance_in_region_1)
        new_instance_in_region_2_config = self.google_api_interface_region_2.get_instance_configs(
            instance_in_region_2)

        # target pool configuration is unchanged
        self.assertTrue(resource_config_is_unchanged_including_network(
            original_target_pool_config, new_target_pool_config))
        # instances' network changed
        self.assertTrue(resource_config_is_unchanged_except_for_network(
            original_instance_in_region_1_config,
            new_instance_in_region_1_config))
        self.assertTrue(resource_config_is_unchanged_except_for_network(
            original_instance_in_region_2_config,
            new_instance_in_region_2_config))

        self.assertTrue(check_instance_network(new_instance_in_region_1_config,
                                               target_network_selfLink))
        self.assertTrue(check_instance_network(new_instance_in_region_2_config,
                                               target_network_selfLink))
        print('Pass the current test')

    def tearDown(self) -> None:
        pass

    def doCleanups(self) -> None:
        self.google_api_interface.clean_all_resources()


if __name__ == '__main__':
    warnings.filterwarnings(action="ignore", message="unclosed",
                            category=ResourceWarning)
    unittest.main(failfast=True)
