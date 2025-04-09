# Copyright 2017,2019 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Function tests for 'zhmc info' command, using faked HMCs (zhmcclient mock).
"""

from .utils import call_zhmc_child, assert_rc


def test_info_help():
    """
    Test 'zhmc info --help'
    """

    # Invoke the command to be tested
    rc, stdout, stderr = call_zhmc_child(['info', '--help'])

    assert_rc(0, rc, stdout, stderr)
    assert stdout.startswith(
        "Usage: zhmc info [OPTIONS]\n"), \
        f"stdout={stdout!r}"
    assert stderr == ""
