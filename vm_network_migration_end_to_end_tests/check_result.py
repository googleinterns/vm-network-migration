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
""" Helper functions for comparing the test results

"""
def compare_instance_external_ip(config1, config2):
    return config1['networkInterfaces'][0]['accessConfigs'][0]['natIP'] == \
           config2['networkInterfaces'][0]['accessConfigs'][0]['natIP']


def compare_two_list(l1, l2):
    for value in l1:
        if value not in l2:
            return False

    for value in l2:
        if value not in l1:
            return False
    return True


def resource_config_is_unchanged_except_for_network(original_config,
                                                    new_config):
    except_tags = ['id', 'creationTimestamp', 'fingerprint', 'network',
                   'subnetwork', 'networkIP', 'natIP']
    return resource_config_is_unchanged_except_for_tags(original_config,
                                                        new_config, except_tags)


def resource_config_is_unchanged_including_network(original_config, new_config):
    except_tags = ['id', 'creationTimestamp', 'fingerprint', 'networkIP',
                   'natIP']
    return resource_config_is_unchanged_except_for_tags(original_config,
                                                        new_config, except_tags)


def instance_template_config_is_unchanged_except_for_network_and_name(
        original_config, new_config):
    return resource_config_is_unchanged_except_for_tags(
        original_config,
        new_config,
        ['id', 'creationTimestamp', 'fingerprint', 'name', 'network',
         'subnetwork', 'selfLink'])


def instance_template_config_is_unchanged(original_config, new_config):
    return resource_config_is_unchanged_except_for_tags(
        original_config,
        new_config,
        ['id', 'creationTimestamp', 'fingerprint', 'selfLink'])


def resource_config_is_unchanged_except_for_tags(original_config, new_config,
                                                 except_tags=[]):
    """ Recursively compare if original_config is the same as new_config except
    for the except_tags

    """
    if type(original_config) is str:
        if original_config != new_config:
            print(original_config)
            return False
    elif type(original_config) is list:
        for i in range(len(original_config)):
            if not resource_config_is_unchanged_except_for_tags(
                    original_config[i], new_config[i], except_tags):
                print(i, original_config[i])
                return False

    elif type(original_config) is dict:
        for i in original_config:
            if i not in new_config:
                continue
            if i not in except_tags:
                if not resource_config_is_unchanged_except_for_tags(
                        original_config[i],
                        new_config[i],
                        except_tags):
                    print(i, original_config[i])

                    return False
    return True


def check_instance_template_network(instance_template_config, network_selfLink,
                                    subnetwork_selfLink=None):
    if instance_template_config['properties']['networkInterfaces'][
        0]['network'] != network_selfLink:
        return False
    if subnetwork_selfLink != None and \
            instance_template_config['properties']['networkInterfaces'][
                0]['subnetwork'] != subnetwork_selfLink:
        return False
    return True


def check_instance_network(instance_config, network_selfLink,
                           subnetwork_selfLink=None):
    if instance_config['networkInterfaces'][0]['network'] != network_selfLink:
        return False
    if subnetwork_selfLink != None and instance_config['networkInterfaces'][0][
        'subnetwork'] != subnetwork_selfLink:
        return False
    return True
