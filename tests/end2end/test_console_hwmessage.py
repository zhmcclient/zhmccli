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
End2end tests for the 'zhmc console hw-message' command group.
"""

import re
import random
import urllib3
import pytest
import zhmcclient
# pylint: disable=unused-import
from zhmcclient.testutils import hmc_definition  # noqa: F401
from .utils import zhmc_session  # noqa: F401
# pylint: enable=unused-import

from .utils import run_zhmc, parse_output, fixup

urllib3.disable_warnings()


# pylint: disable=inconsistent-return-statements
def pick_console_with_hwmessages(console):
    """
    Pick the console if it has at least one hardware message.
    """
    messages = console.hw_messages.list()
    if messages:
        return console, messages

    pytest.skip("Did not find a CPC with hardware messages")


def assert_messages(
        rc, stdout, stderr, out_format, command, exp_rc, exp_stderr, exp_props,
        exp_messages):
    """
    Check exit code, stdout, stderr of the zhmc command against
    expected values.

    This function can be used for two cases:
    * command='list': Check a list of hardware messages in stdout, against the
      same set of messages in exp_messages.
    * command='show': Check a single hardware message in stdout against a
      single message in exp_messages (it is a list with one item).
    """
    assert rc == exp_rc, (
        f"Unexpected exit code {rc} (expected was {exp_rc})\n"
        f"Stdout: {stdout}\n"
        f"Stderr: {stderr}\n"
    )

    if command == 'list':
        out_type = list
    else:
        assert command == 'show'
        out_type = dict

    if exp_rc == 0:
        assert stderr == ""

        out_obj = parse_output(stdout, out_format, out_type)

        if command == 'list':
            assert len(out_obj) == len(exp_messages)
            # Check only one message from the result
            index = random.randrange(len(out_obj))  # nosec
            out_item = out_obj[index]
            exp_message = exp_messages[index]
        else:
            out_item = out_obj
            exp_message = exp_messages[0]

        # Check the message
        message_id = exp_message.prop('element-id')
        for pname in exp_props:
            if pname not in CPC_HWMSG_PROPS_ARTIFICIAL:
                assert pname in out_item
                exp_value = exp_message.prop(pname, 'undefined')
                if out_format == 'csv':
                    value = fixup(out_item[pname])
                else:
                    value = out_item[pname]
                assert value == exp_value, (
                    f"Unexpected value for property {pname} of hardware "
                    f"message {message_id} of a CPC:\n"
                    f"Expected: {exp_value!r}\n"
                    f"Actual: {value!r}"
                )
    else:
        assert re.search(exp_stderr, stderr, re.MULTILINE)


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
    # Testcases for test_console_hwmsg_list()
    # Each list item is a testcase, which is a tuple with items:
    # - options (list of str): Options for 'zhmc console hw-message list' cmd
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
def test_console_hwmsg_list(
        zhmc_session, out_format, options, exp_props):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test 'console hw-message list' command for output formats json and csv.
    """
    client = zhmcclient.Client(zhmc_session)
    console = client.consoles.console
    console, messages = pick_console_with_hwmessages(console)

    # Reduce messages to be listed since --all takes a long time for many
    # messages
    num_messages = min(5, len(messages))
    messages = messages[-num_messages:]
    first_ts_dt = zhmcclient.datetime_from_timestamp(
        messages[0].prop('timestamp'))
    first_ts_str = first_ts_dt.strftime('%Y-%m-%d %H:%M:%S.%f')

    args = ['-o', out_format, 'console', 'hw-message', 'list', '--begin',
            first_ts_str] + options
    rc, stdout, stderr = run_zhmc(args)

    assert_messages(rc, stdout, stderr, out_format, 'list', 0, "",
                    exp_props, messages)


@pytest.mark.parametrize(
    "out_format",
    ['json', 'csv']
)
def test_console_hwmsg_show(zhmc_session, out_format):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test 'console hw-message show' command.
    """
    client = zhmcclient.Client(zhmc_session)
    console = client.consoles.console
    console, messages = pick_console_with_hwmessages(console)

    test_message = random.choice(messages)  # nosec
    test_message_id = test_message.prop('element-id')

    rc, stdout, stderr = run_zhmc(
        ['-o', out_format, 'console', 'hw-message', 'show', test_message_id])

    assert_messages(rc, stdout, stderr, out_format, 'show', 0, "",
                    CPC_HWMSG_PROPS_DEFAULT, [test_message])


# Note: We do not have end2end tests for modifying commands:
# 'console hw-message delete'
# 'console hw-message get-service-info'
# 'console hw-message request-service'
# 'console hw-message decline-service'
