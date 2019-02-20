# Copyright 2017-2019 IBM Corp. All Rights Reserved.
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
Function tests for 'zhmc' command with global options that can be tested
without a subcommand.

Global options that can be tested only with a subcommand are tested with the
'info' subcommand (in test_info.py).
"""

from __future__ import absolute_import, print_function

import re

from .utils import call_zhmc_child, assert_rc


class TestGlobalOptions(object):
    """
    All tests for the 'zhmc' command with global options that can be tested
    without a subcommand.
    """

    def test_global_help(self):
        """Test 'zhmc --help'"""

        rc, stdout, stderr = call_zhmc_child(['--help'])

        assert_rc(0, rc, stdout, stderr)
        assert stdout.startswith(
            "Usage: zhmc [GENERAL-OPTIONS] COMMAND [ARGS]...\n"), \
            "stdout={!r}".format(stdout)
        assert stderr == ""

    def test_global_version(self):
        """Test 'zhmc --version'"""

        rc, stdout, stderr = call_zhmc_child(['--version'])

        assert_rc(0, rc, stdout, stderr)
        assert re.match(r'^zhmc, version [0-9]+\.[0-9]+\.[0-9]+', stdout)
        assert stderr == ""
