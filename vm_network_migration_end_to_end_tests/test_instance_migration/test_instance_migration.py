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


class TestInstanceMigration(unittest.TestCase):
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

    def testInvalidNetworkInfo(self):
        """ Invalid target network information

        Expectation: http error. The migration will not start.

        """
        ### create test resources
        instance_name = "end-to-end-test-instance-1"
        instance_selfLink = \
            self.test_resource_creator.create_instance_using_template(
                instance_name,
                self.test_resource_creator.legacy_instance_template_selfLink)[
                'targetLink']
        original_config = self.google_api_interface.get_instance_configs(
            instance_name)
        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute, instance_selfLink,
                                             'an-invalid-network-for-testing',
                                             self.test_resource_creator.subnetwork_name,
                                             True)
        with self.assertRaises(Exception):
            migration_handler = selfLink_executor.build_migration_handler()
            migration_handler.network_migration()

        ### check result
        # Terminate before migration starts
        new_config = self.google_api_interface.get_instance_configs(
            instance_name)
        self.assertEqual(original_config, new_config)
        print('Pass the current test')

    def testAutomodeNetwork(self):
        """ Target network is an auto-mode subnet
        Without providing the subnetwork name, the migration will still success

        """
        ### create test resources
        instance_name = "end-to-end-test-instance-1"
        instance_selfLink = \
            self.test_resource_creator.create_instance_using_template(
                instance_name,
                self.test_resource_creator.legacy_instance_template_selfLink)[
                'targetLink']
        original_config = self.google_api_interface.get_instance_configs(
            instance_name)
        auto_subnetwork_name = 'end-to-end-test-auto-subnetwork'
        try:
            network_selfLink = self.google_api_interface.get_network(auto_subnetwork_name)['selfLink']
        except:
            network_selfLink = self.google_api_interface.create_auto_subnetwork(auto_subnetwork_name)['targetLink']

        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute, instance_selfLink,
                                             auto_subnetwork_name,
                                             None,
                                             True)

        migration_handler = selfLink_executor.build_migration_handler()
        migration_handler.network_migration()

        ### check result
        new_config = self.google_api_interface.get_instance_configs(
            instance_name)
        self.assertTrue(
            resource_config_is_unchanged_except_for_network(new_config,
                                                            original_config))
        self.assertTrue(
            compare_instance_external_ip(new_config, original_config))
        # network changed
        self.assertTrue(check_instance_network(new_config,
                                               network_selfLink,
                                               ))
        print('Pass the current test')

    def testIpPreservation(self):
        # create test resources
        instance_name = "end-to-end-test-instance-1"
        instance_selfLink = \
            self.test_resource_creator.create_instance_using_template(
                instance_name,
                self.test_resource_creator.legacy_instance_template_selfLink)[
                'targetLink']
        original_config = self.google_api_interface.get_instance_configs(
            instance_name)
        # start migration
        selfLink_executor = SelfLinkExecutor(self.compute, instance_selfLink,
                                             self.test_resource_creator.network_name,
                                             self.test_resource_creator.subnetwork_name,
                                             True)
        migration_handler = selfLink_executor.build_migration_handler()
        migration_handler.network_migration()
        # check migration result
        new_config = self.google_api_interface.get_instance_configs(
            instance_name)
        self.assertTrue(
            resource_config_is_unchanged_except_for_network(new_config,
                                                            original_config))
        self.assertTrue(
            compare_instance_external_ip(new_config, original_config))
        # network changed
        self.assertTrue(check_instance_network(new_config,
                                               self.test_resource_creator.network_selfLink,
                                               self.test_resource_creator.subnetwork_selfLink))
        print('Pass the current test')

    def testWithoutIpPreservation(self):
        # create test resources
        instance_name = "end-to-end-test-instance-1"
        instance_selfLink = \
            self.test_resource_creator.create_instance_using_template(
                instance_name,
                self.test_resource_creator.legacy_instance_template_selfLink)[
                'targetLink']
        original_config = self.google_api_interface.get_instance_configs(
            instance_name)
        # start migration
        selfLink_executor = SelfLinkExecutor(self.compute,
                                             instance_selfLink,
                                             self.test_resource_creator.network_name,
                                             self.test_resource_creator.subnetwork_name,
                                             False)
        migration_handler = selfLink_executor.build_migration_handler()
        migration_handler.network_migration()
        # check migration result
        new_config = self.google_api_interface.get_instance_configs(
            instance_name)
        self.assertTrue(
            resource_config_is_unchanged_except_for_network(new_config,
                                                            original_config))
        self.assertFalse(
            compare_instance_external_ip(new_config, original_config))
        # network changed
        self.assertTrue(check_instance_network(new_config,
                                               self.test_resource_creator.network_selfLink,
                                               self.test_resource_creator.subnetwork_selfLink))
        print('Pass the current test')

    def testInstanceUsingMultiDisks(self):
        # create test resources
        instance_name = "end-to-end-test-instance-1"
        instance_selfLink = \
            self.test_resource_creator.create_instance_using_template(
                instance_name,
                self.test_resource_creator.legacy_instance_template_selfLink)[
                'targetLink']
        self.test_resource_creator.add_additional_disk_to_instance(
            instance_name, 'second-disk',
            'sample_disk.json')
        original_config = self.google_api_interface.get_instance_configs(
            instance_name)
        # start migration
        selfLink_executor = SelfLinkExecutor(self.compute,
                                             instance_selfLink,
                                             self.test_resource_creator.network_name,
                                             self.test_resource_creator.subnetwork_name,
                                             False)
        migration_handler = selfLink_executor.build_migration_handler()
        migration_handler.network_migration()
        # check migration result
        new_config = self.google_api_interface.get_instance_configs(
            instance_name)
        self.assertTrue(
            resource_config_is_unchanged_except_for_network(new_config,
                                                            original_config))
        # network changed
        self.assertTrue(check_instance_network(new_config,
                                               self.test_resource_creator.network_selfLink,
                                               self.test_resource_creator.subnetwork_selfLink))
        print('Pass the current test')

    def testMigrateAnInstanceInAnInstanceGroup(self):
        """ The instance is serving an instance group

        Expectation: the migration will not start

        """
        ### create test resources
        instance_name_1 = 'end-to-end-test-instance-1'
        instance_selfLink_1 = \
            self.test_resource_creator.create_instance_using_template(
                instance_name_1,
                self.test_resource_creator.legacy_instance_template_selfLink)[
                'targetLink']
        original_config = self.google_api_interface.get_instance_configs(
            instance_name_1)
        unmanaged_instance_group_name = 'end-to-end-test-unmanaged-instance-group-1'
        self.test_resource_creator.create_unmanaged_instance_group(
            unmanaged_instance_group_name,
            [instance_name_1])
        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute,
                                             instance_selfLink_1,
                                             self.test_resource_creator.network_name,
                                             self.test_resource_creator.subnetwork_name,
                                             False)

        with self.assertRaises(AmbiguousTargetResource):
            migration_handler = selfLink_executor.build_migration_handler()
            migration_handler.network_migration()
        ### check migration result
        # the migration never starts, so the config didn't change
        new_config = self.google_api_interface.get_instance_configs(
            instance_name_1)
        self.assertEqual(new_config, original_config)
        print('Pass the current test')

    def testAsBackendOfTargetPool(self):
        """ An instance is serving a target pool.
        Expectation: the instance migration will still finish.
        But the instance will be detached from the target pool.
        So the target pool will be affected. This is not a recommended use case.
        """
        ### create test resources
        instance_name_1 = 'end-to-end-test-instance-1'
        instance_selfLink_1 = \
            self.test_resource_creator.create_instance_using_template(
                instance_name_1,
                self.test_resource_creator.legacy_instance_template_selfLink)[
                'targetLink']
        original_instance_config = self.google_api_interface.get_instance_configs(
            instance_name_1)
        target_pool_name = 'end-to-end-test-target-pool'
        self.test_resource_creator.create_target_pool_with_health_check(
            'sample_target_pool_with_no_instance.json',
            target_pool_name,
            [],
            [instance_selfLink_1],
            health_check_selfLink=None)

        ### start migration
        selfLink_executor = SelfLinkExecutor(self.compute, instance_selfLink_1,
                                             self.test_resource_creator.network_name,
                                             self.test_resource_creator.subnetwork_name,
                                             )
        migration_handler = selfLink_executor.build_migration_handler()
        migration_handler.network_migration()
        ### check migration result
        # the migration is successful
        new_instance_config = self.google_api_interface.get_instance_configs(
            instance_name_1)
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
