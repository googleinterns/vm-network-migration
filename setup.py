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
""" Setup script for vm_network_migration Python package.

Also installs third party libraries, if those libraries are not
already installed.
"""
import unittest2

from setuptools import (
    setup,
    find_packages,
)

install_requires = [
    # NOTE: Apache Beam tests depend on this library and cannot
    # currently upgrade their httplib2 version.
    # Please see https://github.com/googleapis/google-api-python-client/pull/84
    "httplib2>=0.9.2,<1dev",
    "google-auth>=1.16.0",
    "google-auth-httplib2>=0.0.3",
    "google-api-core>=1.18.0,<2dev",
    "google-api-python-client",
    "google",
    "timeout_decorator",
    "unittest2"
]

def my_test_suite():
    test_loader = unittest2.TestLoader()
    test_suite = test_loader.discover('vm_network_migration_end_to_end_tests',
                                      pattern='test_*.py')
    return test_suite


setup(
    name='vm_network_migration',
    version='1.0',
    description='',
    author='',
    author_email='',
    test_suite='setup.my_test_suite',
    packages=find_packages(),
    package_data={
        'vm_network_migration_end_to_end_tests': ['data/*.json']
    },
    install_requires=install_requires,  # external packages as dependencies
)
