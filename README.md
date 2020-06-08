# VM Network Migration
**This is not an officially supported Google product.**
## Description

This project aims to migrate a VM instance from its legacy network to a
subnetwork with downtime. After the migration, a new VM instance in the new
subnetwork will be created and the old VM instance will be deleted.
## Before Running
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
## Run
     python3 vm_network_migration.py --project_id=dakeying-devconsole
     --zone=us-central1-a --original_instance_name=instance-legacy
     --new_instance_name=vm-new --network=test-network --subnetwork=test-network
## Source Code Headers

Every file containing source code must include copyright and license
information. This includes any JS/CSS files that you might be serving out to
browsers. (This is to help well-intentioned people avoid accidental copying that
doesn't comply with the license.)

Apache header:

    Copyright 2020 Google LLC

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        https://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
