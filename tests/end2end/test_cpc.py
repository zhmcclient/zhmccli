# Copyright 2025 IBM Corp. All Rights Reserved.
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
End2end tests for the 'zhmc cpc' command group.
"""


import json
import urllib3
import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition  # noqa: F401, E501
from .utils import zhmc_session  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import run_zhmc, pick_test_resources

urllib3.disable_warnings()


def test_cpc_list(zhmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test 'cpc list' command in the most simple way.
    """
    client = zhmcclient.Client(zhmc_session)
    cpcs = client.cpcs.list()

    rc, stdout, stderr = run_zhmc(
        ['-o', 'json', 'cpc', 'list', '--names-only'])

    assert rc == 0
    assert stderr == ""
    out_list = json.loads(stdout)
    assert isinstance(out_list, list)
    assert len(out_list) == len(cpcs)
    cpc_names = [cpc.name for cpc in cpcs]
    for out_item in out_list:
        assert 'name' in out_item
        assert out_item['name'] in cpc_names


def test_cpc_show(zhmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test 'cpc show' command in the most simple way.
    """
    client = zhmcclient.Client(zhmc_session)
    cpcs = client.cpcs.list()
    cpcs = pick_test_resources(cpcs)

    for cpc in cpcs:

        rc, stdout, stderr = run_zhmc(
            ['-o', 'json', 'cpc', 'show', cpc.name])

        assert rc == 0
        assert stderr == ""
        out_props = json.loads(stdout)
        assert isinstance(out_props, dict)
        assert out_props['name'] == cpc.name


# TODO: Add tests for 'cpc list-api-features' command
# TODO: Add tests for 'cpc dpm-export' command
# TODO: Add tests for 'cpc list-firmware' command
# TODO: Add tests for 'cpc get-em-data' command

# Note: We do not have end2end tests for modifying commands:
# 'cpc dpm-import'
# 'cpc update'
# 'cpc upgrade'
# 'cpc install-firmware'
# 'cpc delete-uninstalled-firmware'
# 'cpc set-power-capping'
