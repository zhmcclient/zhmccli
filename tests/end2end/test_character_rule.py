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
End2end tests for the 'zhmc passwordrule characterrule' command group.
"""

import re
import uuid
import urllib3
import pytest
import zhmcclient
# pylint: disable=unused-import
from zhmcclient.testutils import hmc_definition  # noqa: F401
from .utils import zhmc_session  # noqa: F401
# pylint: enable=unused-import

from .utils import run_zhmc, pick_test_resources, TEST_PREFIX, parse_output, \
    fixup

urllib3.disable_warnings()


# pylint: disable=inconsistent-return-statements
def pick_with_charrules(pwrules):
    """
    Pick a password rule that has at least one character rule.
    """
    for pwrule in pwrules:
        charrules = pwrule.get_property('character-rules')
        if charrules:
            return pwrule

    pytest.skip("Did not find a password rule that has at least one char rule")


def assert_pwrule(
        rc, stdout, stderr, exp_rc, exp_stdout, exp_stderr, exp_charrules,
        pwrule):
    """
    Check exit code, stdout, stderr of the zhmc command against
    expected values.
    """
    assert rc == exp_rc, (
        f"Unexpected exit code {rc} (expected was {exp_rc})\n"
        f"Stdout: {stdout}\n"
        f"Stderr: {stderr}\n"
    )
    assert re.search(exp_stdout, stdout, re.MULTILINE)
    assert re.search(exp_stderr, stderr, re.MULTILINE)

    if exp_rc == 0:
        pwrule.pull_properties(['character-rules'])
        act_charrules = pwrule.properties['character-rules']
        assert len(act_charrules) == len(exp_charrules)
        for i, exp_charrule in enumerate(exp_charrules):
            act_charrule = act_charrules[i]
            for name, exp_value in exp_charrule.items():
                assert name in act_charrule
                act_value = act_charrule[name]
                assert act_value == exp_value, (
                    f"Unexpected value in property {name} of character "
                    f"rule {i} in password rule {pwrule.name}:\n"
                    f"Actual: {act_value!r}\n"
                    f"Expected: {exp_value!r}")


# Expected output properties when no other options are specified
CHARRULE_PROPS_DEFAULT = [
    "min-characters",
    "max-characters",
    "alphabetic",
    "numeric",
    "special",
    "custom-character-sets",
]


TESTCASES_CHARRULE_LIST = [
    # Testcases for test_charrule_list()
    # Each list item is a testcase, which is a tuple with items:
    # - options (list of str): Options for 'zhmc cpc list' command
    # - exp_props (list of str): Expected property names in output
    # - exact (bool): If True, the output property names must be exactly the
    #   expected properties. If False, additional properties are allowed.
    (
        [],
        CHARRULE_PROPS_DEFAULT,
        True,
    ),
]


@pytest.mark.parametrize(
    "options, exp_props, exact",
    TESTCASES_CHARRULE_LIST
)
@pytest.mark.parametrize(
    "out_format",
    ['json', 'csv']
)
def test_charrule_list(
        zhmc_session, out_format, options, exp_props, exact):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test 'passwordrule characterrule list' command for output formats json and
    csv.
    """
    client = zhmcclient.Client(zhmc_session)
    console = client.consoles.console
    pwrules = console.password_rules.list()
    pwrule = pick_with_charrules(pwrules)

    charrules = pwrule.get_property('character-rules')

    args = ['-o', out_format, 'passwordrule', 'characterrule', 'list',
            pwrule.name] + options
    rc, stdout, stderr = run_zhmc(args)

    assert rc == 0
    assert stderr == ""
    out_list = parse_output(stdout, out_format, list)

    assert len(out_list) == len(charrules)
    for i, out_item in enumerate(out_list):
        assert 'index' in out_item
        assert out_item['index'] == i
        exp_charrule = charrules[i]
        for pname in exp_props:
            assert pname in out_item
            exp_value = exp_charrule.get(pname, 'undefined')
            if out_format == 'csv':
                value = fixup(out_item[pname])
            else:
                value = out_item[pname]
            assert value == exp_value, (
                f"Unexpected value for property {pname} of "
                f"character rule {i} in password rule {pwrule.name}:\n"
                f"Expected: {exp_value!r}\n"
                f"Actual: {value!r}"
            )
        if exact:
            assert len(out_item) == len(exp_props) + 1  # + 1 for index


@pytest.mark.parametrize(
    "out_format",
    ['json', 'csv']
)
def test_charrule_show(zhmc_session, out_format):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test 'passwordrule characterrule show' command.
    """
    client = zhmcclient.Client(zhmc_session)
    console = client.consoles.console
    pwrules = console.password_rules.list()
    pwrule = pick_with_charrules(pwrules)

    charrules = pwrule.get_property('character-rules')
    charrules = pick_test_resources(charrules)

    for i, charrule in enumerate(charrules):

        rc, stdout, stderr = run_zhmc(
            ['-o', out_format, 'passwordrule', 'characterrule', 'show',
             pwrule.name, str(i)])

        assert rc == 0
        assert stderr == ""

        out_dict = parse_output(stdout, out_format, dict)

        assert out_dict == charrule


# Some character rules for the testcases
CHARRULE_TEST_OPTIONS = [
    '--min', '4',
    '--max', '8',
    '--alphabetic', 'required',
    '--numeric', 'allowed',
    '--special', 'not-allowed',
    '--custom', '!', 'allowed',
]
CHARRULE_TEST_PROPS = {
    'min-characters': 4,
    'max-characters': 8,
    'alphabetic': 'required',
    'numeric': 'allowed',
    'special': 'not-allowed',
    'custom-character-sets': [{'character-set': '!', 'inclusion': 'allowed'}],
}
CHARRULE_0_PROPS = {
    'min-characters': 6,
    'max-characters': 8,
    'alphabetic': 'allowed',
    'numeric': 'required',
    'special': 'not-allowed',
    'custom-character-sets': [],
}
CHARRULE_1_PROPS = {
    'min-characters': 7,
    'max-characters': 8,
    'alphabetic': 'not-allowed',
    'numeric': 'allowed',
    'special': 'required',
    'custom-character-sets': [],
}

TESTCASES_CHARRULE_ADD = [
    # Testcases for test_charrule_add()
    # Each list item is a testcase, which is a tuple with items:
    # - desc (str): Testcase description
    # - initial_charrules (list of dict): Initial character rules before test
    # - options (list of str): Options for 'zhmc passwordrule characterrule
    #   add' command
    # - exp_rc (int): Expected exit code
    # - exp_stdout (str): Expected standard output
    # - exp_stderr (str): Expected standard error
    # - exp_charrules (list of dict): Expected character rules, if success
    (
        "Missing options",
        [],
        [
            '--min', '4', '--max', '8',
        ],
        2,
        r"",
        r"Error: Missing option",
        None,
    ),
    (
        "Add to empty password rule",
        [],
        CHARRULE_TEST_OPTIONS,
        0,
        r"Password rule .* has been updated",
        r"",
        [
            CHARRULE_TEST_PROPS,
        ],
    ),
    (
        "Add to password rule with one char rule",
        [
            CHARRULE_0_PROPS,
        ],
        CHARRULE_TEST_OPTIONS,
        0,
        r"Password rule .* has been updated",
        r"",
        [
            CHARRULE_0_PROPS,
            CHARRULE_TEST_PROPS,
        ],
    ),
    (
        "Add to password rule before rule 1",
        [
            CHARRULE_0_PROPS,
            CHARRULE_1_PROPS,
        ],
        CHARRULE_TEST_OPTIONS + ['--before', '1'],
        0,
        r"Password rule .* has been updated",
        r"",
        [
            CHARRULE_0_PROPS,
            CHARRULE_TEST_PROPS,
            CHARRULE_1_PROPS,
        ],
    ),
    (
        "Add to password rule after rule 0",
        [
            CHARRULE_0_PROPS,
            CHARRULE_1_PROPS,
        ],
        CHARRULE_TEST_OPTIONS + ['--after', '0'],
        0,
        r"Password rule .* has been updated",
        r"",
        [
            CHARRULE_0_PROPS,
            CHARRULE_TEST_PROPS,
            CHARRULE_1_PROPS,
        ],
    ),
    (
        "Add to password rule last",
        [
            CHARRULE_0_PROPS,
            CHARRULE_1_PROPS,
        ],
        CHARRULE_TEST_OPTIONS + ['--last'],
        0,
        r"Password rule .* has been updated",
        r"",
        [
            CHARRULE_0_PROPS,
            CHARRULE_1_PROPS,
            CHARRULE_TEST_PROPS,
        ],
    ),
]


@pytest.mark.parametrize(
    "desc, initial_charrules, options, exp_rc, exp_stdout, exp_stderr, "
    "exp_charrules",
    TESTCASES_CHARRULE_ADD
)
def test_charrule_add(
        zhmc_session,  # noqa: F811
        desc, initial_charrules, options, exp_rc, exp_stdout, exp_stderr,
        exp_charrules):
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Test 'passwordrule characterrule add' command.
    """
    client = zhmcclient.Client(zhmc_session)
    console = client.consoles.console
    pwrule_name = f"{TEST_PREFIX}_{uuid.uuid4().hex}"

    pwrule = console.password_rules.create({'name': pwrule_name})
    pwrule.update_properties({'character-rules': initial_charrules})

    try:
        rc, stdout, stderr = run_zhmc(
            ['-o', 'json', 'passwordrule', 'characterrule', 'add',
             pwrule_name] + options)

        assert_pwrule(
            rc, stdout, stderr, exp_rc, exp_stdout, exp_stderr, exp_charrules,
            pwrule)

    finally:
        pwrule.delete()


TESTCASES_CHARRULE_REMOVE = [
    # Testcases for test_charrule_remove()
    # Each list item is a testcase, which is a tuple with items:
    # - desc (str): Testcase description
    # - initial_charrules (list of dict): Initial character rules before test
    # - options (list of str): Options for 'zhmc passwordrule characterrule
    #   add' command
    # - exp_rc (int): Expected exit code
    # - exp_stdout (str): Expected standard output
    # - exp_stderr (str): Expected standard error
    # - exp_charrules (list of dict): Expected character rules, if success
    (
        "Missing argument",
        [],
        [],
        2,
        r"",
        r"Error: Missing argument",
        None,
    ),
    (
        "Remove non-existing char rule",
        [],
        ['0'],
        1,
        r"",
        r"Error: Invalid index 0",
        None,
    ),
    (
        "Remove an existing password rule",
        [
            CHARRULE_0_PROPS,
        ],
        ['0'],
        0,
        r"Password rule .* has been updated",
        r"",
        [],
    ),
]


@pytest.mark.parametrize(
    "desc, initial_charrules, options, exp_rc, exp_stdout, exp_stderr, "
    "exp_charrules",
    TESTCASES_CHARRULE_REMOVE
)
def test_charrule_remove(
        zhmc_session,  # noqa: F811
        desc, initial_charrules, options, exp_rc, exp_stdout, exp_stderr,
        exp_charrules):
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Test 'passwordrule characterrule remove' command.
    """
    client = zhmcclient.Client(zhmc_session)
    console = client.consoles.console
    pwrule_name = f"{TEST_PREFIX}_{uuid.uuid4().hex}"

    pwrule = console.password_rules.create({'name': pwrule_name})
    pwrule.update_properties({'character-rules': initial_charrules})

    try:
        rc, stdout, stderr = run_zhmc(
            ['-o', 'json', 'passwordrule', 'characterrule', 'remove',
             pwrule_name] + options)

        assert_pwrule(
            rc, stdout, stderr, exp_rc, exp_stdout, exp_stderr, exp_charrules,
            pwrule)

    finally:
        pwrule.delete()


TESTCASES_CHARRULE_REPLACE = [
    # Testcases for test_charrule_replace())
    # Each list item is a testcase, which is a tuple with items:
    # - desc (str): Testcase description
    # - initial_charrules (list of dict): Initial character rules before test
    # - options (list of str): Options for 'zhmc passwordrule characterrule
    #   add' command
    # - exp_rc (int): Expected exit code
    # - exp_stdout (str): Expected standard output
    # - exp_stderr (str): Expected standard error
    # - exp_charrules (list of dict): Expected character rules, if success
    (
        "Missing argument",
        [],
        [
            '--min', '4', '--max', '8',
        ],
        2,
        r"",
        r"Error: Missing argument",
        None,
    ),
    (
        "Missing options",
        [],
        [
            '0', '--min', '4', '--max', '8',
        ],
        2,
        r"",
        r"Error: Missing option",
        None,
    ),
    (
        "Replace non-existing char rule 0",
        [],
        ['0'] + CHARRULE_TEST_OPTIONS,
        1,
        r"",
        r"Error: Invalid index 0",
        None,
    ),
    (
        "Replace existing char rule 0",
        [CHARRULE_1_PROPS],
        ['0'] + CHARRULE_TEST_OPTIONS,
        0,
        r"Password rule .* has been updated",
        r"",
        [
            CHARRULE_TEST_PROPS,
        ],
    ),
]


@pytest.mark.parametrize(
    "desc, initial_charrules, options, exp_rc, exp_stdout, exp_stderr, "
    "exp_charrules",
    TESTCASES_CHARRULE_REPLACE
)
def test_charrule_replace(
        zhmc_session,  # noqa: F811
        desc, initial_charrules, options, exp_rc, exp_stdout, exp_stderr,
        exp_charrules):
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Test 'passwordrule characterrule add' command.
    """
    client = zhmcclient.Client(zhmc_session)
    console = client.consoles.console
    pwrule_name = f"{TEST_PREFIX}_{uuid.uuid4().hex}"

    pwrule = console.password_rules.create({'name': pwrule_name})
    pwrule.update_properties({'character-rules': initial_charrules})

    try:
        rc, stdout, stderr = run_zhmc(
            ['-o', 'json', 'passwordrule', 'characterrule', 'replace',
             pwrule_name] + options)

        assert_pwrule(
            rc, stdout, stderr, exp_rc, exp_stdout, exp_stderr, exp_charrules,
            pwrule)

    finally:
        pwrule.delete()
