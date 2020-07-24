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

""" Given the selfLink of a compute engine resource, and
network information arguments, the script can recognize the resource type
and run the resource migration.

Before running:
    1. If not already done, enable the Compute Engine API
       and check the quota for your project at
       https://console.developers.google.com/apis/api/compute
    2. This sample uses Application Default Credentials for authentication.
       If not already done, install the gcloud CLI from
       https://cloud.google.com/sdk and run
       `gcloud beta auth application-default login`.
       For more information, see
       https://developers.google.com/identity/protocols/application-default-credentials
    3. Install the Python client library for Google APIs by running
       `pip install --upgrade google-api-python-client`

Run the script by terminal, for example:
     python3 migrate_by_selfLink.py --selfLink=projects/sample-project/global/forwardingRules/sample-rule
     --network=test-network
     --subnetwork=test-network --preserve_external_ip=False
     --region=us-central1

"""
import warnings

import argparse
import google.auth
from googleapiclient import discovery
from vm_network_migration.handler_helper.selfLink_executor import SelfLinkExecutor

if __name__ == '__main__':
    # google credential setup
    credentials, default_project = google.auth.default()
    compute = discovery.build('compute', 'v1', credentials=credentials)

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--selfLink',
                        help='The selfLink of the target resource.')

    parser.add_argument('--network', help='The name of the target network.')
    parser.add_argument(
        '--subnetwork',
        default=None,
        help='The name of target subnetwork. For auto mode networks,'
             ' this field is optional')
    parser.add_argument(
        '--preserve_instance_external_ip',
        default=False,
        help='Preserve the external IP addresses of the instances serving this forwarding rule')

    args = parser.parse_args()

    if args.preserve_instance_external_ip == 'True':
        args.preserve_instance_external_ip = True
    else:
        args.preserve_instance_external_ip = False

    if args.preserve_instance_external_ip:

        warnings.warn(
            'You choose to preserve the external IP. If the original instance '
            'has an ephemeral IP, it will be reserved as a static external IP after the '
            'execution.',
            Warning)
        continue_execution = input(
            'Do you still want to preserve the external IP? y/n: ')
        if continue_execution == 'n':
            args.preserve_instance_external_ip = False
    selfLink_executor = SelfLinkExecutor(compute, args.selfLink, args.network,
                                         args.subnetwork,
                                         args.preserve_instance_external_ip)
    migration_handler = selfLink_executor.build_migration_handler()
    migration_handler.network_migration()
