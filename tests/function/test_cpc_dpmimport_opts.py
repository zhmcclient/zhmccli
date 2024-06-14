# Copyright 2023 IBM Corp. All Rights Reserved.
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
Function tests for options of 'zhmc cpc dpm-import' command.
"""


from .utils import call_zhmc_child, assert_rc


def test_cpc_dpmimport_help():
    """Test 'zhmc cpc dpm-import --help'"""

    rc, stdout, stderr = call_zhmc_child(
        ['cpc', 'dpm-import', '--help'])

    assert_rc(0, rc, stdout, stderr)
    assert stdout.startswith(
        "Usage: zhmc cpc dpm-import [COMMAND-OPTIONS] CPC\n"), \
        f"stdout={stdout!r}"
    assert stderr == ""


def test_cpc_dpmimport_helpdpmfile():
    """Test 'zhmc cpc dpm-import --help-dpm-file'"""

    rc, stdout, stderr = call_zhmc_child(
        ['cpc', 'dpm-import', '--help-dpm-file'])

    assert_rc(0, rc, stdout, stderr)
    assert stdout.startswith(
        "\nFormat of DPM configuration file:\n"), \
        f"stdout={stdout!r}"
    assert stderr == ""


def test_cpc_dpmimport_helpmappingfile():
    """Test 'zhmc cpc dpm-import --help-mapping-file'"""

    rc, stdout, stderr = call_zhmc_child(
        ['cpc', 'dpm-import', '--help-mapping-file'])

    assert_rc(0, rc, stdout, stderr)
    assert stdout.startswith(
        "\nFormat of adapter mapping file:\n"), \
        f"stdout={stdout!r}"
    assert stderr == ""
