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
""" Errors for the library

All exceptions defined by the library
should be defined in this file.
"""

class UnchangedInstanceNameError(IOError):
    """The new instance name is the same as the original one's"""
    pass


class InvalidTargetNetworkError(IOError):
    """Migrate to a non-VPC network"""
    pass


class ZoneOperationsError(Exception):
    """Zone operation's error"""
    pass

class RegionOperationsError(Exception):
    """Region operation's error"""
    pass

class AttributeNotExistError(KeyError):
    """An attribute doesn't exist in the googleapi's response"""
    pass


class InvalidTypeError(TypeError):
    """Type error"""
    pass


class MissingSubnetworkError(IOError):
    """The subnetwork is not defined"""
    pass
