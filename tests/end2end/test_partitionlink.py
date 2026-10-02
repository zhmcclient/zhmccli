# Copyright 2026 IBM Corp. All Rights Reserved.
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
End2end tests for the 'zhmc partitionlink' command group.
"""


import urllib3
import pytest
import zhmcclient
# pylint: disable=unused-import
from zhmcclient.testutils import hmc_definition  # noqa: F401
from .utils import zhmc_session  # noqa: F401
# pylint: enable=unused-import

from .utils import run_zhmc, parse_output, pick_test_resources

urllib3.disable_warnings()


# Expected output properties for 'partitionlink list' when --names-only is used
PROPNAMES_LIST_NAMES_ONLY = [
    "cpc",
    "name",
]

# Expected output properties for 'partitionlink list' with no extra options
PROPNAMES_LIST_DEFAULT = PROPNAMES_LIST_NAMES_ONLY + [
    "type",
    "state",
    "description",
]

# Expected output properties for 'partitionlink list' when --uri is used
PROPNAMES_LIST_URI = PROPNAMES_LIST_DEFAULT + [
    "object-uri",
]

# Expected output properties for 'partitionlink show'
PARTITIONLINK_SHOW_PROPNAMES = [
    "name",
    "type",
    "state",
    "description",
    "object-uri",
]


TESTCASES_PARTITIONLINK_LIST = [
    # Each item: (options, exp_props, exact)
    (
        ['--names-only'],
        PROPNAMES_LIST_NAMES_ONLY,
        True,
    ),
    (
        [],
        PROPNAMES_LIST_DEFAULT,
        True,
    ),
    (
        ['--uri'],
        PROPNAMES_LIST_URI,
        True,
    ),
    (
        ['--all'],
        PROPNAMES_LIST_DEFAULT,
        False,
    ),
]


@pytest.mark.parametrize(
    "options, exp_props, exact",
    TESTCASES_PARTITIONLINK_LIST
)
@pytest.mark.parametrize(
    "out_format",
    ['json', 'csv']
)
def test_partitionlink_list(
        zhmc_session, out_format, options, exp_props, exact):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test 'partitionlink list' command, including with --all which exercises
    the CTC partition link fix (issue #1046).
    """
    client = zhmcclient.Client(zhmc_session)
    console = client.consoles.console

    try:
        partitionlinks = console.partition_links.list()
    except zhmcclient.HTTPError as exc:
        if exc.http_status == 404:
            pytest.skip("HMC does not support partition links")
        raise

    if not partitionlinks:
        pytest.skip("HMC has no partition links defined")

    args = ['-o', out_format, 'partitionlink', 'list'] + options
    rc, stdout, stderr = run_zhmc(args)

    assert rc == 0, (
        f"Unexpected rc={rc} (expected 0),\n"
        f"stdout:\n{stdout}\n"
        f"stderr:\n{stderr}\n"
    )
    assert stderr == ""

    out_list = parse_output(stdout, out_format, list)

    assert len(out_list) == len(partitionlinks)
    exp_pl_dict = {pl.name: pl for pl in partitionlinks}
    for out_item in out_list:
        assert 'name' in out_item
        pl_name = out_item['name']
        assert pl_name in exp_pl_dict
        for pname in exp_props:
            assert pname in out_item, (
                f"Property {pname!r} missing in output item for "
                f"partition link {pl_name!r}"
            )
        if exact:
            assert len(out_item) == len(exp_props)


@pytest.mark.parametrize(
    "out_format",
    ['json', 'csv']
)
def test_partitionlink_show(zhmc_session, out_format):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test 'partitionlink show' command in the most simple way.
    """
    client = zhmcclient.Client(zhmc_session)
    console = client.consoles.console

    try:
        partitionlinks = console.partition_links.list()
    except zhmcclient.HTTPError as exc:
        if exc.http_status == 404:
            pytest.skip("HMC does not support partition links")
        raise

    if not partitionlinks:
        pytest.skip("HMC has no partition links defined")

    for pl in pick_test_resources(partitionlinks):
        rc, stdout, stderr = run_zhmc(
            ['-o', out_format, 'partitionlink', 'show', pl.name])

        assert rc == 0, (
            f"Unexpected rc={rc} (expected 0),\n"
            f"stdout:\n{stdout}\n"
            f"stderr:\n{stderr}\n"
        )
        assert stderr == ""

        out_dict = parse_output(stdout, out_format, dict)

        assert out_dict['name'] == pl.name
