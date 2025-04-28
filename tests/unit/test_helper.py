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


import os
import re
from datetime import datetime, timezone, timedelta, date
import pytest
import click

from zhmcclient_mock import FakedSession

from zhmccli._helper import CmdContext, parse_yaml_flow_style, \
    parse_ec_levels, parse_adapter_names, parse_crypto_domains, \
    domains_to_domain_config, domain_config_to_props_list, \
    required_option, forbidden_option, required_envvar, bool_envvar, \
    parse_timestamp


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
        params=None, host='host', userid='host', password='password',
        no_verify=True, ca_certs=None, logon_source='options',
        session_name=None, output_format='table', transpose=False,
        error_format='msg', timestats=False, session_id=None, get_password=None,
        pdb=False)  # nosec: B106

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


# Test cases for test_parse_ec_levels()
TESTCASES_PARSE_EC_LEVELS = [
    # value, exp_obj, exp_exc_msg
    (
        '',
        None,
        "Error parsing value of option '--option': Value must be a list of "
        "strings: ''"
    ),
    (
        '[]',
        [],
        None
    ),
    (
        '[P12345.001]',
        [('P12345', '001')],
        None
    ),
    (
        '[P12345.001, P12346.002]',
        [('P12345', '001'), ('P12346', '002')],
        None
    ),
    (
        '[',
        None,
        "Error parsing value of option '--option' in YAML FLow Collection Style"
    ),
    (
        '{P12345: 001}',
        None,
        "Error parsing value of option '--option': Value must be a list of "
        "strings: '{P12345: 001}'"
    ),
    (
        'P12345.001',
        None,
        "Error parsing value of option '--option': Value must be a list of "
        "strings: 'P12345.001'"
    ),
    (
        '[P12345]',
        None,
        "Error parsing value of option '--option': Invalid EC level format "
        "'P12345'"
    ),
    (
        '[P12345.001.002]',
        None,
        "Error parsing value of option '--option': Invalid EC level format "
        "'P12345.001.002'"
    ),
]


@pytest.mark.parametrize(
    "value, exp_obj, exp_exc_msg",
    TESTCASES_PARSE_EC_LEVELS)
def test_parse_ec_levels(value, exp_obj, exp_exc_msg):
    """
    Test function for parse_ec_levels().
    """

    cmd_ctx = CmdContext(
        params=None, host='host', userid='host', password='password',
        no_verify=True, ca_certs=None, logon_source='options',
        session_name=None, output_format='table', transpose=False,
        error_format='msg', timestats=False, session_id=None, get_password=None,
        pdb=False)  # nosec: B106

    if exp_exc_msg:
        with pytest.raises(click.exceptions.ClickException) as exc_info:

            # The function to be tested
            parse_ec_levels(cmd_ctx, '--option', value)

        exc = exc_info.value
        msg = str(exc)
        m = re.match(exp_exc_msg, msg)
        assert m, \
            "Unexpected exception message:\n" \
            "  expected pattern: {!r}\n" \
            "  actual message: {!r}".format(exp_exc_msg, msg)
    else:

        # The function to be tested
        obj = parse_ec_levels(cmd_ctx, '--option', value)

        assert obj == exp_obj


# Test cases for test_parse_adapter_names()
TESTCASES_PARSE_ADAPTER_NAMES = [
    # value, exp_obj, exp_exc_msg
    (
        '',
        None,
        r"Error parsing value of option '--option': Value must be a list of "
        r"adapter names: "
    ),
    (
        '[]',
        [],
        None
    ),
    (
        '[HSM1]',
        ['HSM1'],
        None
    ),
    (
        '[HSM 1]',
        ['HSM 1'],
        None
    ),
    (
        '["HSM 1"]',
        ['HSM 1'],
        None
    ),
    (
        '[\'HSM 1\']',
        ['HSM 1'],
        None
    ),
    (
        '[HSM1, HSM2]',
        ['HSM1', 'HSM2'],
        None
    ),
    (
        '[',
        None,
        r"Error parsing value of option '--option' in YAML FLow Collection "
        r"Style"
    ),
    (
        '{HSM1: 1}',
        None,
        r"Error parsing value of option '--option': Value must be a list of "
        r"adapter names: '\{HSM1: 1\}'"
    ),
    (
        'HSM1',
        None,
        r"Error parsing value of option '--option': Value must be a list of "
        r"adapter names: 'HSM1'"
    ),
]


@pytest.mark.parametrize(
    "value, exp_obj, exp_exc_msg",
    TESTCASES_PARSE_ADAPTER_NAMES)
def test_parse_adapter_names(value, exp_obj, exp_exc_msg):
    """
    Test function for parse_adapter_names().
    """

    cmd_ctx = CmdContext(
        params=None, host='host', userid='host', password='password',
        no_verify=True, ca_certs=None, logon_source='options',
        session_name=None, output_format='table', transpose=False,
        error_format='msg', timestats=False, session_id=None, get_password=None,
        pdb=False)  # nosec: B106

    if exp_exc_msg:
        with pytest.raises(click.exceptions.ClickException) as exc_info:

            # The function to be tested
            parse_adapter_names(cmd_ctx, '--option', value)

        exc = exc_info.value
        msg = str(exc)
        m = re.match(exp_exc_msg, msg)
        assert m, \
            "Unexpected exception message:\n" \
            "  expected pattern: {!r}\n" \
            "  actual message: {!r}".format(exp_exc_msg, msg)
    else:

        # The function to be tested
        obj = parse_adapter_names(cmd_ctx, '--option', value)

        assert obj == exp_obj


# Test cases for test_parse_crypto_domains()
TESTCASES_PARSE_CRYPTO_DOMAINS = [
    # value, exp_obj, exp_exc_msg
    (
        '',
        None,
        r"Error parsing value of option '--option': Value must be a list of "
        r"domain index numbers or ranges thereof: "
    ),
    (
        '[]',
        [],
        None
    ),
    (
        '[12]',
        [12],
        None
    ),
    (
        '["12"]',
        [12],
        None
    ),
    (
        '[\'12\']',
        [12],
        None
    ),
    (
        '[xx]',
        None,
        r"Error parsing value of option '--option': Invalid integer value for "
        r"list item 'xx'"
    ),
    (
        '[0, 1]',
        [0, 1],
        None
    ),
    (
        '[12-14]',
        [12, 13, 14],
        None
    ),
    (
        '["12-14"]',
        [12, 13, 14],
        None
    ),
    (
        '[\'12-14\']',
        [12, 13, 14],
        None
    ),
    (
        '[12-12]',
        [12],
        None
    ),
    (
        '[11-12-13]',
        None,
        r"Error parsing value of option '--option': Invalid range format for "
        r"list item '11-12-13' - must be N-M"
    ),
    (
        '[12-11]',
        None,
        r"Error parsing value of option '--option': Invalid range values for "
        r"list item '12-11' - left value must not be larger than right value"
    ),
    (
        '[xx-12]',
        None,
        r"Error parsing value of option '--option': Invalid integer values for "
        r"range list item 'xx-12'"
    ),
    (
        '[[0]]',
        None,
        r"Error parsing value of option '--option': Invalid type for list item "
        r"\[0\] - must be string or int"
    ),
    (
        '[true]',
        None,
        r"Error parsing value of option '--option': Invalid type for list item "
        r"True - must be string or int"
    ),
    (
        '[false]',
        None,
        r"Error parsing value of option '--option': Invalid type for list item "
        r"False - must be string or int"
    ),
    (
        '[',
        None,
        r"Error parsing value of option '--option' in YAML FLow Collection "
        r"Style"
    ),
    (
        '{12: 13}',
        None,
        r"Error parsing value of option '--option': Value must be a list of "
        r"domain index numbers or ranges thereof: '\{12: 13\}'"
    ),
    (
        '12',
        None,
        r"Error parsing value of option '--option': Value must be a list of "
        r"domain index numbers or ranges thereof: '12'"
    ),
]


@pytest.mark.parametrize(
    "value, exp_obj, exp_exc_msg",
    TESTCASES_PARSE_CRYPTO_DOMAINS)
def test_parse_crypto_domains(value, exp_obj, exp_exc_msg):
    """
    Test function for parse_crypto_domains().
    """

    cmd_ctx = CmdContext(
        params=None, host='host', userid='host', password='password',
        no_verify=True, ca_certs=None, logon_source='options',
        session_name=None, output_format='table', transpose=False,
        error_format='msg', timestats=False, session_id=None, get_password=None,
        pdb=False)  # nosec: B106

    if exp_exc_msg:
        with pytest.raises(click.exceptions.ClickException) as exc_info:

            # The function to be tested
            parse_crypto_domains(cmd_ctx, '--option', value)

        exc = exc_info.value
        msg = str(exc)
        m = re.match(exp_exc_msg, msg)
        assert m, \
            "Unexpected exception message:\n" \
            "  expected pattern: {!r}\n" \
            "  actual message: {!r}".format(exp_exc_msg, msg)
    else:

        # The function to be tested
        obj = parse_crypto_domains(cmd_ctx, '--option', value)

        assert obj == exp_obj


# Test cases for test_domains_to_domain_config()
TESTCASES_DOMAINS_TO_DOMAIN_CONFIG = [
    # usage_domains, control_domains, exp_obj, exp_exc_msg
    (
        [],
        [],
        [],
        None,
    ),
    (
        [12],
        [],
        [
            {
                'domain-index': 12,
                'access-mode': 'control-usage',
            },
        ],
        None
    ),
    (
        [],
        [12],
        [
            {
                'domain-index': 12,
                'access-mode': 'control',
            },
        ],
        None
    ),
    (
        [12, 13],
        [14, 15],
        [
            {
                'domain-index': 12,
                'access-mode': 'control-usage',
            },
            {
                'domain-index': 13,
                'access-mode': 'control-usage',
            },
            {
                'domain-index': 14,
                'access-mode': 'control',
            },
            {
                'domain-index': 15,
                'access-mode': 'control',
            },
        ],
        None
    ),
]


@pytest.mark.parametrize(
    "usage_domains, control_domains, exp_obj, exp_exc_msg",
    TESTCASES_DOMAINS_TO_DOMAIN_CONFIG)
def test_domains_to_domain_config(
        usage_domains, control_domains, exp_obj, exp_exc_msg):
    """
    Test function for domains_to_domain_config().
    """

    if exp_exc_msg:
        with pytest.raises(click.exceptions.ClickException) as exc_info:

            # The function to be tested
            domains_to_domain_config(usage_domains, control_domains)

        exc = exc_info.value
        msg = str(exc)
        m = re.match(exp_exc_msg, msg)
        assert m, \
            "Unexpected exception message:\n" \
            "  expected pattern: {!r}\n" \
            "  actual message: {!r}".format(exp_exc_msg, msg)
    else:

        # The function to be tested
        obj = domains_to_domain_config(usage_domains, control_domains)

        assert obj == exp_obj


# Test cases for test_domain_config_to_props_list()
TESTCASES_DOMAIN_CONFIG_TO_PROPS_LIST = [
    # adapter_names, domain_configs, exp_props_list, exp_exc_msg
    (
        [],
        [],
        [],
        None,
    ),
    (
        ['A1'],
        [
            {
                'domain-index': 12,
                'access-mode': 'control-usage',
            },
        ],
        [
            {'adapter': 'A1', 'domains': '12', 'access-mode': 'control-usage'},
        ],
        None
    ),
    (
        ['A1'],
        [
            {
                'domain-index': 0,
                'access-mode': 'control-usage',
            },
        ],
        [
            {'adapter': 'A1', 'domains': '0', 'access-mode': 'control-usage'},
        ],
        None
    ),
    (
        ['A1'],
        [
            {
                'domain-index': 12,
                'access-mode': 'control',
            },
            {
                'domain-index': 13,
                'access-mode': 'control',
            },
        ],
        [
            {'adapter': 'A1', 'domains': '12-13', 'access-mode': 'control'},
        ],
        None
    ),
    (
        ['A1'],
        [
            {
                'domain-index': 0,
                'access-mode': 'control',
            },
            {
                'domain-index': 1,
                'access-mode': 'control',
            },
            {
                'domain-index': 2,
                'access-mode': 'control',
            },
        ],
        [
            {'adapter': 'A1', 'domains': '0-2', 'access-mode': 'control'},
        ],
        None
    ),
    (
        ['A1'],
        [
            {
                'domain-index': 12,
                'access-mode': 'control',
            },
            {
                'domain-index': 13,
                'access-mode': 'control',
            },
            {
                'domain-index': 14,
                'access-mode': 'control-usage',
            },
        ],
        [
            {'adapter': 'A1', 'domains': '12-13', 'access-mode': 'control'},
            {'adapter': 'A1', 'domains': '14', 'access-mode': 'control-usage'},
        ],
        None
    ),
    (
        ['A1'],
        [
            {
                'domain-index': 12,
                'access-mode': 'control',
            },
            {
                'domain-index': 14,
                'access-mode': 'control',
            },
            {
                'domain-index': 15,
                'access-mode': 'control',
            },
        ],
        [
            {'adapter': 'A1', 'domains': '12', 'access-mode': 'control'},
            {'adapter': 'A1', 'domains': '14-15', 'access-mode': 'control'},
        ],
        None
    ),
    (
        ['A1', 'A2'],
        [
            {
                'domain-index': 14,
                'access-mode': 'control',
            },
            {
                'domain-index': 15,
                'access-mode': 'control',
            },
        ],
        [
            {'adapter': 'A1', 'domains': '14-15', 'access-mode': 'control'},
            {'adapter': 'A2', 'domains': '14-15', 'access-mode': 'control'},
        ],
        None
    ),
    (
        ['A2', 'A1'],
        [
            {
                'domain-index': 15,
                'access-mode': 'control',
            },
            {
                'domain-index': 14,
                'access-mode': 'control',
            },
        ],
        [
            {'adapter': 'A1', 'domains': '14-15', 'access-mode': 'control'},
            {'adapter': 'A2', 'domains': '14-15', 'access-mode': 'control'},
        ],
        None
    ),
]


@pytest.mark.parametrize(
    "adapter_names, domain_configs, exp_props_list, exp_exc_msg",
    TESTCASES_DOMAIN_CONFIG_TO_PROPS_LIST)
def test_domain_config_to_props_list(
        adapter_names, domain_configs, exp_props_list, exp_exc_msg):
    """
    Test function for domain_config_to_props_list().
    """

    session = FakedSession('fake-host', 'fake-hmc', '2.16.0', '4.10')
    cpc = session.hmc.cpcs.add({'name': 'cpc1'})

    adapters = []
    for adapter_name in adapter_names:
        adapter = cpc.adapters.add({'name': adapter_name, 'type': 'crypto'})
        adapters.append(adapter)

    if exp_exc_msg:
        with pytest.raises(click.exceptions.ClickException) as exc_info:

            # The function to be tested
            domain_config_to_props_list(adapters, 'adapter', domain_configs)

        exc = exc_info.value
        msg = str(exc)
        m = re.match(exp_exc_msg, msg)
        assert m, \
            "Unexpected exception message:\n" \
            "  expected pattern: {!r}\n" \
            "  actual message: {!r}".format(exp_exc_msg, msg)
    else:

        # The function to be tested
        props_list = domain_config_to_props_list(
            adapters, 'adapter', domain_configs)

        assert props_list == exp_props_list


# Test cases for required_option()
TESTCASES_REQUIRED_OPTION = [
    # value, name, exp_value, exp_exc_msg
    (
        'v1',
        'o1',
        'v1',
        None
    ),
    (
        '',
        'o1',
        '',
        None
    ),
    (
        None,
        'o1',
        None,
        "Required option not specified: o1"
    ),
]


@pytest.mark.parametrize(
    "value, name, exp_value, exp_exc_msg",
    TESTCASES_REQUIRED_OPTION)
def test_required_option(value, name, exp_value, exp_exc_msg):
    """
    Test function for required_option().
    """

    if exp_exc_msg:
        with pytest.raises(click.exceptions.ClickException) as exc_info:

            # The function to be tested
            required_option(value, name)

        exc = exc_info.value
        msg = str(exc)
        m = re.match(exp_exc_msg, msg)
        assert m, \
            "Unexpected exception message:\n" \
            "  expected pattern: {!r}\n" \
            "  actual message: {!r}".format(exp_exc_msg, msg)
    else:

        # The function to be tested
        act_value = required_option(value, name)

        assert act_value == exp_value


# Test cases for forbidden_option()
TESTCASES_FORBIDDEN_OPTION = [
    # value, name, reason, exp_exc_msg
    (
        None,
        'o1',
        'of some reason',
        None
    ),
    (
        '',
        'o1',
        'of some reason',
        "Option is not allowed because of some reason: o1"
    ),
    (
        'v1',
        'o1',
        'of some reason',
        "Option is not allowed because of some reason: o1"
    ),
]


@pytest.mark.parametrize(
    "value, name, reason, exp_exc_msg",
    TESTCASES_FORBIDDEN_OPTION)
def test_forbidden_option(value, name, reason, exp_exc_msg):
    """
    Test function for forbidden_option().
    """

    if exp_exc_msg:
        with pytest.raises(click.exceptions.ClickException) as exc_info:

            # The function to be tested
            forbidden_option(value, name, reason)

        exc = exc_info.value
        msg = str(exc)
        m = re.match(exp_exc_msg, msg)
        assert m, \
            "Unexpected exception message:\n" \
            "  expected pattern: {!r}\n" \
            "  actual message: {!r}".format(exp_exc_msg, msg)
    else:

        # The function to be tested
        forbidden_option(value, name, reason)


# Test cases for required_envvar()
TESTCASES_REQUIRED_ENVVAR = [
    # initial_value, name, exp_exc_msg
    (
        None,
        'e1',
        "Required environment variable not set: e1"
    ),
    (
        '',
        'e1',
        None
    ),
    (
        'v1',
        'e1',
        None
    ),
]


@pytest.mark.parametrize(
    "initial_value, name, exp_exc_msg",
    TESTCASES_REQUIRED_ENVVAR)
def test_required_envvar(initial_value, name, exp_exc_msg):
    """
    Test function for required_envvar().
    """

    if initial_value is not None:
        os.environ[name] = initial_value
    else:
        if name in os.environ:
            del os.environ[name]

    if exp_exc_msg:
        with pytest.raises(click.exceptions.ClickException) as exc_info:

            # The function to be tested
            required_envvar(name)

        exc = exc_info.value
        msg = str(exc)
        m = re.match(exp_exc_msg, msg)
        assert m, \
            "Unexpected exception message:\n" \
            "  expected pattern: {!r}\n" \
            "  actual message: {!r}".format(exp_exc_msg, msg)
    else:

        # The function to be tested
        value = required_envvar(name)

        assert value == initial_value


# Test cases for bool_envvar()
TESTCASES_BOOL_ENVVAR = [
    # initial_value, name, default, exp_value, exp_exc_msg
    (
        None,
        'e1',
        'd1',
        'd1',
        None,
    ),
    (
        None,
        'e1',
        None,
        None,
        None,
    ),
    (
        '0',
        'e1',
        'd1',
        False,
        None
    ),
    (
        'no',
        'e1',
        'd1',
        False,
        None
    ),
    (
        'No',
        'e1',
        'd1',
        False,
        None
    ),
    (
        'NO',
        'e1',
        'd1',
        False,
        None
    ),
    (
        'false',
        'e1',
        'd1',
        False,
        None
    ),
    (
        'False',
        'e1',
        'd1',
        False,
        None
    ),
    (
        'FALSE',
        'e1',
        'd1',
        False,
        None
    ),
    (
        '1',
        'e1',
        'd1',
        True,
        None
    ),
    (
        'yes',
        'e1',
        'd1',
        True,
        None
    ),
    (
        'Yes',
        'e1',
        'd1',
        True,
        None
    ),
    (
        'YES',
        'e1',
        'd1',
        True,
        None
    ),
    (
        'true',
        'e1',
        'd1',
        True,
        None
    ),
    (
        'True',
        'e1',
        'd1',
        True,
        None
    ),
    (
        'TRUE',
        'e1',
        'd1',
        True,
        None
    ),
    (
        '',
        'e1',
        'd1',
        None,
        "Invalid value for e1 environment variable: '' is not a valid boolean."
    ),
    (
        '2',
        'e1',
        'd1',
        None,
        "Invalid value for e1 environment variable: '2' is not a "
        "valid boolean."
    ),
    (
        'yesssir',
        'e1',
        'd1',
        None,
        "Invalid value for e1 environment variable: 'yesssir' is not a "
        "valid boolean."
    ),
]


@pytest.mark.parametrize(
    "initial_value, name, default, exp_value, exp_exc_msg",
    TESTCASES_BOOL_ENVVAR)
def test_bool_envvar(initial_value, name, default, exp_value, exp_exc_msg):
    """
    Test function for bool_envvar().
    """

    if initial_value is not None:
        os.environ[name] = initial_value
    else:
        if name in os.environ:
            del os.environ[name]

    if exp_exc_msg:
        with pytest.raises(click.exceptions.ClickException) as exc_info:

            # The function to be tested
            bool_envvar(name, default)

        exc = exc_info.value
        msg = str(exc)
        m = re.match(exp_exc_msg, msg)
        assert m, \
            "Unexpected exception message:\n" \
            "  expected pattern: {!r}\n" \
            "  actual message: {!r}".format(exp_exc_msg, msg)
    else:

        # The function to be tested
        value = bool_envvar(name, default)

        assert value == exp_value


TESTCASES_PARSE_TIMESTAMP = [
    # Test cases for parse_timestamp(). Each item is a testcase with the
    # following tuple items:
    # * value (str): Timestamp value to be parsed
    # * exp_dt (datetime): Expected parsed datetime value, if success.
    # * exp_exc_type (Exception): Expected excaption class, if error.
    # * exp_exc_msg (str): Expected exception message pattern, if error.
    (
        None,
        None,
        TypeError,
        ".*"
    ),
    (
        1,
        None,
        TypeError,
        ".*"
    ),
    (
        '',
        None,
        ValueError,
        "String does not contain a date"
    ),
    (
        '-1',
        None,
        ValueError,
        "Negative HMC timestamp value .* cannot be represented"
    ),
    (
        '2025-04-20 08:13:38+-!0000',
        None,
        ValueError,
        "Unknown string format"
    ),
    (
        '2025000-04-20',
        None,
        ValueError,
        "year .* is out of range"
    ),
    (
        '2025000000000000-04-20',
        None,
        OverflowError,
        "Python int too large|signed integer is greater than maximum"
    ),
    (
        '2025000000000000000000000000000000-04-20',
        None,
        OverflowError,
        "Python int too large|signed integer is greater than maximum"
    ),
    (
        '0',
        datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc),
        None,
        None
    ),
    (
        '1',
        datetime(1970, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc),
        None,
        None
    ),
    (
        '1745136818344',
        datetime(2025, 4, 20, 8, 13, 38, 344000, tzinfo=timezone.utc),
        None,
        None
    ),
    (
        '2025-04-20 08:13:38.344+0000',
        datetime(2025, 4, 20, 8, 13, 38, 344000, tzinfo=timezone.utc),
        None,
        None
    ),
    (
        '2025-04-20 08:13:38.344+0200',
        datetime(2025, 4, 20, 8, 13, 38, 344000,
                 tzinfo=timezone(timedelta(seconds=7200))),
        None,
        None
    ),
    (
        '2025-04-20 08:13:38.344',
        datetime(2025, 4, 20, 8, 13, 38, 344000, tzinfo=timezone.utc),
        None,
        None
    ),
    (
        '2025-04-20 08:13:38',
        datetime(2025, 4, 20, 8, 13, 38, 0, tzinfo=timezone.utc),
        None,
        None
    ),
    (
        '2025-04-20 08:13',
        datetime(2025, 4, 20, 8, 13, 0, 0, tzinfo=timezone.utc),
        None,
        None
    ),
    (
        '2025-04-20 08',
        datetime(2025, 4, 20, 8, 0, 0, 0, tzinfo=timezone.utc),
        None,
        None
    ),
    (
        '2025-04-20',
        datetime(2025, 4, 20, 0, 0, 0, 0, tzinfo=timezone.utc),
        None,
        None
    ),
    (
        '05-04-06',
        datetime(2006, 5, 4, 0, 0, 0, 0, tzinfo=timezone.utc),
        None,
        None
    ),
    (
        '5/4/06',
        datetime(2006, 5, 4, 0, 0, 0, 0, tzinfo=timezone.utc),
        None,
        None
    ),
    (
        '08:13:38',
        datetime(date.today().year, date.today().month, date.today().day,
                 8, 13, 38, 0, tzinfo=timezone.utc),
        None,
        None
    ),
    (
        '2025-04-20T08:13:38.344Z',
        datetime(2025, 4, 20, 8, 13, 38, 344000, tzinfo=timezone.utc),
        None,
        None
    ),
    (
        '2025-04-20T08:13:38.344+02:00',
        datetime(2025, 4, 20, 8, 13, 38, 344000,
                 tzinfo=timezone(timedelta(seconds=7200))),
        None,
        None
    ),
    (
        '2025-04-20T08:13:38.344',
        datetime(2025, 4, 20, 8, 13, 38, 344000, tzinfo=timezone.utc),
        None,
        None
    ),
]


@pytest.mark.parametrize(
    "value, exp_dt, exp_exc_type, exp_exc_msg",
    TESTCASES_PARSE_TIMESTAMP)
def test_parse_timestamp(value, exp_dt, exp_exc_type, exp_exc_msg):
    """
    Test function for parse_timestamp().
    """

    if exp_exc_type:
        with pytest.raises(exp_exc_type) as exc_info:

            # The function to be tested
            parse_timestamp(value)

        exc = exc_info.value
        msg = str(exc)
        m = re.match(exp_exc_msg, msg)
        assert m, \
            "Unexpected exception message:\n" \
            "  expected pattern: {!r}\n" \
            "  actual message: {!r}".format(exp_exc_msg, msg)
    else:

        # The function to be tested
        dt = parse_timestamp(value)

        assert dt == exp_dt
