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
End2end tests for the 'zhmc cpc hw-message' command group.
"""

import random
import urllib3
import pytest
import zhmcclient
# pylint: disable=unused-import
from zhmcclient.testutils import hmc_definition  # noqa: F401
from .utils import zhmc_session  # noqa: F401
# pylint: enable=unused-import

from .utils import run_zhmc
from .test_console_hwmessage import assert_messages

urllib3.disable_warnings()


# pylint: disable=inconsistent-return-statements
def pick_cpc_with_hwmessages(cpcs):
    """
    Pick a CPC that has at least one hardware message.
    """
    for cpc in cpcs:
        messages = cpc.hw_messages.list()
        if messages:
            return cpc, messages

    pytest.skip("Did not find a CPC with hardware messages")


# Expected output properties when no other options are specified
CPC_HWMSG_PROPS_DEFAULT = [
    "timestamp-utc",
    "message-id",
    "text",
]

# Expected output properties when --all option is specified
# Note: These are the z16 properties. Additional properties are allowed.
CPC_HWMSG_PROPS_ALL = [
    "timestamp-utc",
    "message-id",
    "text",
    "class",
    "details",
    "element-id",
    "element-uri",
    "parent",
    "service-supported",
    "text",
    "timestamp",
]

# Artificial output properties (that are not properties on the HardwareMessage
# object).
CPC_HWMSG_PROPS_ARTIFICIAL = [
    "timestamp-utc",
    "message-id",
]


TESTCASES_CPC_HWMSG_LIST = [
    # Testcases for test_cpc_hwmsg_list()
    # Each list item is a testcase, which is a tuple with items:
    # - options (list of str): Options for 'zhmc cpc list' command
    # - exp_props (list of str): Expected property names in output
    (
        [],
        CPC_HWMSG_PROPS_DEFAULT,
    ),
    (
        ['--all'],
        CPC_HWMSG_PROPS_ALL,
    ),
]


@pytest.mark.parametrize(
    "options, exp_props",
    TESTCASES_CPC_HWMSG_LIST
)
@pytest.mark.parametrize(
    "out_format",
    ['json', 'csv']
)
def test_cpc_hwmsg_list(
        zhmc_session, out_format, options, exp_props):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test 'cpc hw-message list' command for output formats json and csv.
    """
    client = zhmcclient.Client(zhmc_session)
    cpcs = client.cpcs.list()
    cpc, messages = pick_cpc_with_hwmessages(cpcs)

    # Reduce messages to be listed since --all takes a long time for many
    # messages
    num_messages = min(5, len(messages))
    messages = messages[-num_messages:]
    first_ts_dt = zhmcclient.datetime_from_timestamp(
        messages[0].prop('timestamp'))
    first_ts_str = first_ts_dt.strftime('%Y-%m-%d %H:%M:%S.%f')

    args = ['-o', out_format, 'cpc', 'hw-message', 'list', '--begin',
            first_ts_str, cpc.name] + options
    rc, stdout, stderr = run_zhmc(args)

    assert_messages(rc, stdout, stderr, out_format, 'list', 0, "",
                    exp_props, messages)


@pytest.mark.parametrize(
    "out_format",
    ['json', 'csv']
)
def test_cpc_hwmsg_show(zhmc_session, out_format):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test 'cpc hw-message show' command.
    """
    client = zhmcclient.Client(zhmc_session)
    cpcs = client.cpcs.list()
    cpc, messages = pick_cpc_with_hwmessages(cpcs)

    test_message = random.choice(messages)  # nosec
    test_message_id = test_message.prop('element-id')

    rc, stdout, stderr = run_zhmc(
        ['-o', out_format, 'cpc', 'hw-message', 'show', cpc.name,
         test_message_id])

    assert_messages(rc, stdout, stderr, out_format, 'show', 0, "",
                    CPC_HWMSG_PROPS_DEFAULT, [test_message])


# Note: We do not have end2end tests for modifying commands:
# 'cpc hw-message delete'
# 'cpc hw-message get-service-info'
# 'cpc hw-message request-service'
# 'cpc hw-message decline-service'
