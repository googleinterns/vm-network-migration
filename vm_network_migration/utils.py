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
""" Utility functions for the library

"""
import inspect
import time
from functools import wraps


def initializer(fun):
    """ Automatically initialize instance variables

    Args:
        fun: an init function

    Returns: a wrapper function

    """
    names, varargs, keywords, defaults, kwonlyargs, kwonlydefaults, annotations = inspect.getfullargspec(fun)

    @wraps(fun)
    def wrapper(self, *args, **kwargs):
        for name, arg in list(zip(names[1:], args)) + list(kwargs.items()):
            setattr(self, name, arg)
        if defaults !=None:
            for i in range(len(defaults)):
                index = -(i + 1)
                if not hasattr(self, names[index]):
                    setattr(self, names[index], defaults[index])
        fun(self, *args, **kwargs)

    return wrapper


def generate_timestamp_string() -> str:
    """Generate the current timestamp.

    Returns: current timestamp string

    """
    return str(time.strftime('%s', time.gmtime()))

def find_all_matching_strings_from_a_dict(dict_object, matching_string, result_set):
    """ Recursively find all matching strings if it appears in the dictionary

    Args:
        dict_object: a dictionary
        matching_string: string to be matched
        result_set: strings which are matched with the matching_string

    Returns:

    """
    if type(dict_object) is str:
        if matching_string in dict_object:
            result_set.add(dict_object)
            return
    elif type(dict_object) is dict:
        for key in dict_object:
            find_all_matching_strings_from_a_dict(dict_object[key], matching_string, result_set)

    elif type(dict_object) is list:
        for i in range(len(dict_object)):
            find_all_matching_strings_from_a_dict(dict_object[i], matching_string, result_set)

def is_equal_or_contians(url1, url2):
    """ Check if two url is the same or contains each other

    Args:
        url1:
        url2:

    Returns: true or false

    """
    return url1 == url2 or url1 in url2 or url2 in url1

def instance_group_links_is_equal(url1, url2) -> bool:
    """ Compare two instance group selfLinks

    Args:
        url1: selfLink of group1
        url2: selfLink of group2

    Returns:

    """
    url1 = url1.replace('/instanceGroupManagers/','/instanceGroups/' )
    url2 = url2.replace('/instanceGroupManagers/','/instanceGroups/' )
    return is_equal_or_contians(url1, url2)