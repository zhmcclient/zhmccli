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
Unit tests for _helper module.
"""

from __future__ import absolute_import, print_function

import re
import pytest
import click

from zhmccli._helper import CmdContext, parse_yaml_flow_style


# Test cases for parse_yaml_flow_style()
TESTCASES_PARSE_YAML_FLOW_STYLE = [
    # value, exp_obj, exp_exc_msg
    (
        '',
        None,
        None
    ),
    (
        'a',
        'a',
        None
    ),
    (
        '1',
        1,
        None
    ),
    (
        'null',
        None,
        None
    ),
    (
        '[]',
        [],
        None
    ),
    (
        '[a]',
        ['a'],
        None
    ),
    (
        '[a, b, 1, null]',
        ['a', 'b', 1, None],
        None
    ),
    (
        '{}',
        {},
        None
    ),
    (
        '{a: b}',
        {'a': 'b'},
        None
    ),
    (
        '{a: b, b: 1, c: null}',
        {'a': 'b', 'b': 1, 'c': None},
        None
    ),
    (
        '{',
        None,
        "Error parsing value of option '--option' in YAML FLow Collection Style"
    ),
]


@pytest.mark.parametrize(
    "value, exp_obj, exp_exc_msg",
    TESTCASES_PARSE_YAML_FLOW_STYLE)
def test_parse_yaml_flow_style(value, exp_obj, exp_exc_msg):
    """
    Test function for datetime_from_isoformat().
    """

    cmd_ctx = CmdContext(
        host='host', userid='host', password='password', no_verify=True,
        ca_certs=None, output_format='table', transpose=False,
        error_format='msg', timestats=False, session_id=None,
        get_password=None, pdb=False)

    if exp_exc_msg:
        with pytest.raises(click.exceptions.ClickException) as exc_info:

            # The function to be tested
            parse_yaml_flow_style(cmd_ctx, '--option', value)

        exc = exc_info.value
        msg = str(exc)
        m = re.match(exp_exc_msg, msg)
        assert m, \
            "Unexpected exception message:\n" \
            "  expected pattern: {!r}\n" \
            "  actual message: {!r}".format(exp_exc_msg, msg)
    else:

        # The function to be tested
        obj = parse_yaml_flow_style(cmd_ctx, '--option', value)

        assert obj == exp_obj
