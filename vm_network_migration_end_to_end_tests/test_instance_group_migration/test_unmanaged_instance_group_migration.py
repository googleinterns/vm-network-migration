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
from vm_network_migration_end_to_end_tests.build_test_resource import TestResourceCreator
from vm_network_migration_end_to_end_tests.check_result import *
from vm_network_migration_end_to_end_tests.google_api_interface import GoogleApiInterface
from googleapiclient import discovery
from vm_network_migration_end_to_end_tests.utils import *
from vm_network_migration.handler_helper.selfLink_executor import SelfLinkExecutor
from vm_network_migration.errors import *


class TestUnmanagedInstanceGroupMigration(unittest.TestCase):
    project = os.environ["PROJECT_ID"]
    credentials, default_project = google.auth.default()
    compute = discovery.build('compute', 'v1', credentials=credentials)
    google_api_interface = GoogleApiInterface(compute,
                                              project,
                                              'us-central1',
                                              'us-central1-a')
    test_resource_creator = TestResourceCreator(
        google_api_interface)

    def testWithMultipleInstancesInTheGroup(self):
        ### create test resources
        instance_name_1 = 'end-to-end-test-instance-1'
        self.test_resource_creator.create_instance_using_template(
            instance_name_1,
            self.test_resource_creator.legacy_instance_template_selfLink)

        instance_name_2 = 'end-to-end-test-instance-2'
        self.test_resource_creator.create_instance_using_template(
            instance_name_2,
            self.test_resource_creator.legacy_instance_template_selfLink)


        unmanaged_instance_group_name = 'end-to-end-test-unmanaged-instance-group-1'
        original_instances_in_group = [instance_name_1, instance_name_2]
        self.test_resource_creator.create_unmanaged_instance_group(
            unmanaged_instance_group_name,
            original_instances_in_group)
        original_config = self.google_api_interface.get_unmanaged_instance_group_configs(
            unmanaged_instance_group_name)

        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute,
                                             original_config['selfLink'],
                                             self.test_resource_creator.network_name,
                                             self.test_resource_creator.subnetwork_name,
                                             False)
        migration_handler = selfLink_executor.build_migration_handler()
        migration_handler.network_migration()
        ### check migration result
        new_config = self.google_api_interface.get_unmanaged_instance_group_configs(
            unmanaged_instance_group_name)
        self.assertTrue(resource_config_is_unchanged_except_for_network(
            original_config, new_config))

        # network changed
        self.assertTrue(
            check_selfLink_equal(new_config['network'],
                                 self.test_resource_creator.network_selfLink))
        self.assertTrue(
            check_selfLink_equal(new_config['subnetwork'],
                                 self.test_resource_creator.network_selfLink))
        print('Pass the current test')

    def testWithNoInstanceInTheGroup(self):
        ### create test resources
        unmanaged_instance_group_name = 'end-to-end-test-unmanaged-instance-group-1'
        self.test_resource_creator.create_unmanaged_instance_group(
            unmanaged_instance_group_name,
            [])
        original_config = self.google_api_interface.get_unmanaged_instance_group_configs(
            unmanaged_instance_group_name)

        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute,
                                             original_config['selfLink'],
                                             self.test_resource_creator.network_name,
                                             self.test_resource_creator.subnetwork_name,
                                             False)
        migration_handler = selfLink_executor.build_migration_handler()
        migration_handler.network_migration()
        ### check migration result
        new_config = self.google_api_interface.get_unmanaged_instance_group_configs(
            unmanaged_instance_group_name)

        self.assertTrue(
            resource_config_is_unchanged_except_for_network(original_config,
                                                            new_config))

        # network changed
        self.assertTrue(
            check_selfLink_equal(new_config['network'],
                                 self.test_resource_creator.network_selfLink))
        print('Pass the current test')

    def testAsBackendOfTargetPool(self):
        """ The unmanaged instance group serves a target pool, which means the
        instances in this instance group serve the target pool. The migration can
        still succeed. But the instances might be detached from the target pool
        after the migration.

        """
        ### create test resources
        instance_name_1 = 'end-to-end-test-instance-1'
        operation = self.test_resource_creator.create_instance_using_template(
            instance_name_1,
            self.test_resource_creator.legacy_instance_template_selfLink)
        instance_selfLink_1 = operation['targetLink']
        original_instance_config = self.google_api_interface.get_instance_configs(
            instance_name_1)
        unmanaged_instance_group_name = 'end-to-end-test-unmanaged-instance-group-1'
        original_instances_in_group = [instance_name_1]
        unmanaged_instance_group_selfLink = \
        self.test_resource_creator.create_unmanaged_instance_group(
            unmanaged_instance_group_name,
            original_instances_in_group)['targetLink']
        original_instance_group_config = self.google_api_interface.get_unmanaged_instance_group_configs(
            unmanaged_instance_group_name)
        target_pool_name = 'end-to-end-test-target-pool'
        self.test_resource_creator.create_target_pool_with_health_check(
            'sample_target_pool_with_no_instance.json',
            target_pool_name,
            [],
            [instance_selfLink_1],
            health_check_selfLink=None)
        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute,
                                             unmanaged_instance_group_selfLink,
                                             self.test_resource_creator.network_name,
                                             self.test_resource_creator.subnetwork_name,
                                             )
        migration_handler = selfLink_executor.build_migration_handler()
        migration_handler.network_migration()
        ### check migration result
        # the migration is successful
        new_instance_config = self.google_api_interface.get_instance_configs(
            instance_name_1)
        new_instance_group_config = self.google_api_interface.get_unmanaged_instance_group_configs(
            unmanaged_instance_group_name)
        self.assertTrue(resource_config_is_unchanged_except_for_network(
            original_instance_config, new_instance_config))
        self.assertTrue(resource_config_is_unchanged_except_for_network(
            original_instance_group_config, new_instance_group_config))

        # network changed
        self.assertTrue(check_instance_network(new_instance_config, self.test_resource_creator.network_selfLink,
                               self.test_resource_creator.subnetwork_selfLink))
        print('Pass the current test')

    def testAsBackendOfBackendService(self):
        """ The migration will fail and rollback to the legacy network.
        The user should migrate the backend service directly, or detach the instance
        group from the backend service.

        """
        ### create test resources
        instance_name_1 = 'end-to-end-test-instance-1'
        operation = self.test_resource_creator.create_instance_using_template(
            instance_name_1,
            self.test_resource_creator.legacy_instance_template_selfLink)

        original_instance_config = self.google_api_interface.get_instance_configs(
            instance_name_1)
        unmanaged_instance_group_name = 'end-to-end-test-unmanaged-instance-group-1'
        original_instances_in_group = [instance_name_1]
        unmanaged_instance_group_selfLink = \
        self.test_resource_creator.create_unmanaged_instance_group(
            unmanaged_instance_group_name,
            original_instances_in_group)['targetLink']
        original_instance_group_config = self.google_api_interface.get_unmanaged_instance_group_configs(
            unmanaged_instance_group_name)
        backend_service_name = 'end-to-end-test-backend-service'
        original_backend_selfLinks = [unmanaged_instance_group_selfLink]
        self.test_resource_creator.create_regional_backend_service(
            'sample_internal_backend_service.json',
            backend_service_name, original_backend_selfLinks)
        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute,
                                             unmanaged_instance_group_selfLink,
                                             self.test_resource_creator.network_name,
                                             self.test_resource_creator.subnetwork_name,
                                             )
        with self.assertRaises(MigrationFailed):
            migration_handler = selfLink_executor.build_migration_handler()
            migration_handler.network_migration()

        ### check migration result
        # the migration is failed and the resources are rolled back
        new_instance_config = self.google_api_interface.get_instance_configs(
            instance_name_1)
        new_instance_group_config = self.google_api_interface.get_unmanaged_instance_group_configs(
            unmanaged_instance_group_name)
        self.assertTrue(
            resource_config_is_unchanged_including_network(
                original_instance_config, new_instance_config))
        self.assertTrue(
            resource_config_is_unchanged_including_network(
                original_instance_group_config, new_instance_group_config))

        print('Pass the current test')

    def tearDown(self) -> None:
        pass

    def doCleanups(self) -> None:
        self.google_api_interface.clean_all_resources()


if __name__ == '__main__':
    unittest.main(failfast=True)
