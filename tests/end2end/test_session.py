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
End2end tests for the 'zhmc session' command group.
"""


import os
import re
import time
import urllib3
import pytest

# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import run_zhmc, create_hmc_session, delete_hmc_session, \
    is_valid_hmc_session, env2bool

urllib3.disable_warnings()

# Enable logging via environment
TESTLOG = env2bool('TESTLOG')


def assert_session_create(
        rc, stdout, stderr, hmc_definition,  # noqa: F811
        exp_rc, exp_err, pdb_):
    # pylint: disable=redefined-outer-name
    """
    Check the result of a 'session create' command.
    """
    assert rc == exp_rc, \
        "Unexpected exit code: got {}, expected {}\nstdout:\n{}\nstderr:\n{}". \
        format(rc, exp_rc, stdout, stderr)

    if pdb_:
        # The pdb interactions are also part of the stdout lines, so checking
        # stdout does not make sense.
        return

    if exp_err:
        assert re.search(exp_err, stderr), \
            "Unexpected stderr:\ngot: {}\nexpected pattern: {}". \
            format(stderr, exp_err)

    if rc == 0:
        export_vars = {}
        unset_vars = {}
        for line in stdout.splitlines():
            m = re.match(r'^unset (ZHMC_[A-Z_]+)$', line)
            if m:
                name = m.group(1)
                unset_vars[name] = True
                continue
            m = re.match(r'^export (ZHMC_[A-Z_]+)=(.*)$', line)
            if m:
                name = m.group(1)
                value = m.group(2)
                export_vars[name] = value
                continue
            raise AssertionError(f"Unexpected line on stdout: {line!r}")

        assert 'ZHMC_HOST' in export_vars
        zhmc_host = export_vars.pop('ZHMC_HOST')
        assert zhmc_host == hmc_definition.host

        assert 'ZHMC_USERID' in export_vars
        zhmc_userid = export_vars.pop('ZHMC_USERID')
        assert zhmc_userid == hmc_definition.userid

        assert 'ZHMC_SESSION_ID' in export_vars
        del export_vars['ZHMC_SESSION_ID']

        if hmc_definition.verify:
            assert 'ZHMC_NO_VERIFY' in unset_vars
            _ = unset_vars.pop('ZHMC_NO_VERIFY')
        else:
            assert 'ZHMC_NO_VERIFY' in export_vars
            zhmc_no_verify = export_vars.pop('ZHMC_NO_VERIFY')
            assert bool(zhmc_no_verify) is True

        if hmc_definition.ca_certs is None:
            assert 'ZHMC_CA_CERTS' in unset_vars
            _ = unset_vars.pop('ZHMC_CA_CERTS')
        else:
            assert 'ZHMC_CA_CERTS' in export_vars
            zhmc_ca_certs = export_vars.pop('ZHMC_CA_CERTS')
            assert zhmc_ca_certs == hmc_definition.ca_certs

        assert not export_vars
        assert not unset_vars


def assert_session_delete(
        rc, stdout, stderr, hmc_definition,  # noqa: F811
        exp_rc, exp_err, pdb_):
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Check the result of a 'session delete' command.
    """
    assert rc == exp_rc, \
        "Unexpected exit code: got {}, expected {}\nstdout:\n{}\nstderr:\n{}". \
        format(rc, exp_rc, stdout, stderr)

    if pdb_:
        # The pdb interactions are also part of the stdout lines, so checking
        # stdout does not make sense.
        return

    if exp_err:
        assert re.search(exp_err, stderr), \
            "Unexpected stderr:\ngot: {}\nexpected pattern: {}". \
            format(stderr, exp_err)

    if rc == 0:
        export_vars = {}
        unset_vars = {}
        for line in stdout.splitlines():
            m = re.match(r'^unset (ZHMC_[A-Z_]+)$', line)
            if m:
                name = m.group(1)
                unset_vars[name] = True
                continue
            m = re.match(r'^export (ZHMC_[A-Z_]+)=(.*)$', line)
            if m:
                name = m.group(1)
                value = m.group(2)
                export_vars[name] = value
                continue
            raise AssertionError(f"Unexpected line on stdout: {line!r}")

        assert 'ZHMC_SESSION_ID' in unset_vars
        del unset_vars['ZHMC_SESSION_ID']

        assert not export_vars
        assert not unset_vars


def assert_session_command(
        rc, stdout, stderr, hmc_definition,  # noqa: F811
        exp_rc, exp_err, pdb_):
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Check the result of a normal command.
    """
    assert rc == exp_rc, \
        "Unexpected exit code: got {}, expected {}\nstdout:\n{}\nstderr:\n{}". \
        format(rc, exp_rc, stdout, stderr)

    if pdb_:
        # The pdb interactions are also part of the stdout lines, so checking
        # stdout does not make sense.
        return

    if exp_err:
        assert re.search(exp_err, stderr), \
            "Unexpected stderr:\ngot: {}\nexpected pattern: {}". \
            format(stderr, exp_err)


def get_session_create_exports(stdout):
    """
    Get the export statements from stdout of the 'session create' command.
    """
    export_vars = {}
    for line in stdout.splitlines():
        m = re.match(r'^export (ZHMC_[A-Z_]+)=(.*)$', line)
        if m:
            name = m.group(1)
            value = m.group(2)
            export_vars[name] = value
    return export_vars


def prepare_environ(environ, envvars, hmc_definition):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Update the ZHMC_* variables in the environ dict from the envvars testcase
    parameter.
    """
    cleanup_session_ids = []

    # Clean the environment from ZHMC_* variables
    for name in list(environ.keys()):
        if name.startswith('ZHMC_'):
            del environ[name]

    # Set ZHMC_* variables according to the testcase
    for name, kind in envvars.items():
        if name == 'ZHMC_HOST':
            if kind == 'valid':
                environ[name] = hmc_definition.host
            elif kind == 'invalid':
                environ[name] = 'invalid-host'
        elif name == 'ZHMC_USERID':
            if kind == 'valid':
                environ[name] = hmc_definition.userid
            elif kind == 'invalid':
                environ[name] = 'invalid-userid'
        elif name == 'ZHMC_SESSION_ID':
            if kind == 'valid':
                session_id = create_hmc_session(hmc_definition)
                cleanup_session_ids.append(session_id)
                environ[name] = session_id
            elif kind == 'invalid':
                environ[name] = 'invalid-session-id'
        elif name == 'ZHMC_NO_VERIFY':
            if kind == 'valid':
                environ[name] = '0' if hmc_definition.verify else '1'
            elif kind == 'invalid':
                environ[name] = '1' if hmc_definition.verify else '0'
        elif name == 'ZHMC_CA_CERTS':
            if kind == 'valid':
                if hmc_definition.ca_certs:
                    environ[name] = hmc_definition.ca_certs
            elif kind == 'invalid':
                if not hmc_definition.ca_certs:
                    environ[name] = 'invalid-cert-path'
        else:
            raise AssertionError(
                "Invalid testcase: envvars specifies unknown "
                "variable: {!r}".format(name))

    return cleanup_session_ids


def prepare_logon_args(logon_opts, hmc_definition):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Prepare logon arguments from the test_ops testcase parameter.
    """
    logon_args = []
    for name, kind in logon_opts.items():
        if name == '-h':
            if kind == 'valid':
                logon_args.extend([name, hmc_definition.host])
            elif kind == 'invalid':
                logon_args.extend([name, 'invalid-host'])
        elif name == '-u':
            if kind == 'valid':
                logon_args.extend([name, hmc_definition.userid])
            elif kind == 'invalid':
                logon_args.extend([name, 'invalid-userid'])
        elif name == '-p':
            if kind == 'valid':
                logon_args.extend([name, hmc_definition.password])
            elif kind == 'invalid':
                logon_args.extend([name, 'invalid-password'])
        elif name == '-n':
            if kind == 'valid':
                if not hmc_definition.verify:
                    logon_args.append(name)
            elif kind == 'invalid':
                if hmc_definition.verify:
                    # Do it the opposite way -> invalid
                    logon_args.append(name)
        elif name == '-c':
            if kind == 'valid':
                if hmc_definition.ca_certs:
                    logon_args.extend([name, hmc_definition.ca_certs])
            elif kind == 'invalid':
                if not hmc_definition.ca_certs:
                    # Do it the opposite way -> invalid
                    logon_args.extend([name, 'invalid-cert-path'])
        else:
            raise AssertionError(
                "Invalid testcase: logon_opts specifies unknown "
                "option: {!r}".format(name))

    return logon_args


def test_utils_valid_session(hmc_definition):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test utils.is_valid_hmc_session() with a valid session.
    """
    valid_session_id = create_hmc_session(hmc_definition)

    is_valid = is_valid_hmc_session(hmc_definition, valid_session_id)

    assert is_valid is True

    # Cleanup
    delete_hmc_session(hmc_definition, valid_session_id)


def test_utils_invalid_session(hmc_definition):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test utils.is_valid_hmc_session() with an invalid session.
    """
    invalid_session_id = 'invalid-session-id'

    is_valid = is_valid_hmc_session(hmc_definition, invalid_session_id)

    assert is_valid is False


TESTCASE_SESSION_CREATE = [

    # Each item is a testcase for test_session_create(), with the following
    # items:
    #
    # * desc (str): Testcase description
    # * envvars (dict): ZHMC env vars to be set before running command. Key is
    #   the var name; value indicates how to provide the var value:
    #   - omitted - var is not provided
    #   - 'valid' - var is provided with valid value from HMC definition
    #   - 'invalid' - var is provided with some invalid value
    # * logon_opts (str): zhmc logon options to be provided in the command.
    #   Key is the option name; value indicates how to provide the option value:
    #   - omitted - option is not provided
    #   - 'valid' - option is provided with valid value from HMC definition
    #   - 'invalid' - option is provided with some invalid value
    # * exp_rc (int): Expected command exit code.
    # * exp_err (str): Pattern for expected error message, or None for success.
    # * run: Testcase run control, as follows:
    #   - True - run the testcase
    #   - False - skip the testcase
    #   - 'pdb' - debug the testcase (wake up in pdb before command function)
    #   - 'log' - enable HMC logging and display the log records
    #   - 'sleep' - sleep for 60 sec after the testcase (used to circumvent
    #     temporary disablemnt of logong due to too many logons).

    (
        "'session create' with no env vars and valid logon opts",
        # Since there is no session ID in the env vars, a new session is created
        # on the HMC, using the valid password.
        {},
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'valid',
            '-n': 'valid',
            '-c': 'valid',
        },
        0, None,
        True
    ),
    (
        "'session create' with no env vars and logon opts with invalid pw",
        # Since there is no session ID in the env vars, a new session is created
        # on the HMC, using the invalid password, which fails with 403,0.
        {},
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'invalid',
            '-n': 'valid',
            '-c': 'valid',
        },
        1, "ServerAuthError: HTTP authentication failed with 403,0",
        True
    ),
    (
        "'session create' with just session_id env var (valid session) "
        "and no logon opts",
        # A (valid) session ID is in the env vars, but for creating a Session
        # oject, an HMC host is also needed.
        {
            'ZHMC_SESSION_ID': 'valid',
        },
        {},
        1, 'No HMC host provided',
        True
    ),
    (
        "'session create' with all env vars (valid session) "
        "and no logon opts",
        # The valid session in the env var is successfully deleted on the HMC.
        # A new session is created on the HMC, but since no password is
        # provided, it is prompted for.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'valid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {},
        0, None,
        False  # TODO: Provide the password to the password prompt
    ),
    (
        "'session create' with all env vars (expired session) "
        "and no logon opts",
        # The invalid session in the env var is attempted to be deleted on the
        # HMC and the failure of that due to invalid session ID is ignored.
        # A new session is created on the HMC, but since no password is
        # provided, it is prompted for.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'invalid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {},
        0, None,
        False  # TODO: Provide the password to the password prompt
    ),
    (
        "'session create' with all env vars (valid session) "
        "and valid logon opts",
        # The valid session in the env var is successfully deleted on the HMC.
        # A new session is created on the HMC, using the valid password.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'valid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'valid',
            '-n': 'valid',
            '-c': 'valid',
        },
        0, None,
        True
    ),
    (
        "'session create' with all env vars (expired session) "
        "and valid logon opts",
        # The invalid session in the env var is attempted to be deleted on the
        # HMC, which fails due to being invalid, which is ignored.
        # A new session is created on the HMC, using the valid password.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'invalid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'valid',
            '-n': 'valid',
            '-c': 'valid',
        },
        0, None,
        True
    ),
    (
        "'session create' with all env vars (valid session) "
        "and logon opts with invalid pw",
        # The valid session in the env var is successfully deleted on the HMC.
        # A new session is attempted to be created on the HMC, wich fails due
        # to the invalid password.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'valid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'invalid',
            '-n': 'valid',
            '-c': 'valid',
        },
        1, "ServerAuthError: HTTP authentication failed with 403,0",
        True
    ),
    (
        "'session create' with all env vars (expired session) "
        "and logon opts with invalid pw",
        # The invalid session in the env var is attempted to be deleted on the
        # HMC, which fails due to being invalid, which is ignored.
        # A new session is attempted to be created on the HMC, wich fails due
        # to the invalid password.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'invalid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'invalid',
            '-n': 'valid',
            '-c': 'valid',
        },
        1, "ServerAuthError: HTTP authentication failed with 403,0",
        True
    ),
]


@pytest.mark.parametrize(
    "desc, envvars, logon_opts, exp_rc, exp_err, run",
    TESTCASE_SESSION_CREATE
)
def test_session_create(
        hmc_definition, desc, envvars, logon_opts, exp_rc,  # noqa: F811
        exp_err, run):
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Test 'session create' command.
    """
    if run is False:
        pytest.skip("Testcase disabled")

    cleanup_session_ids = []
    try:
        session_ids = prepare_environ(os.environ, envvars, hmc_definition)
        cleanup_session_ids += session_ids
        logon_args = prepare_logon_args(logon_opts, hmc_definition)

        pdb_ = run == 'pdb'
        log = (run == 'log' or TESTLOG)

        zhmc_args = logon_args + ['session', 'create']

        # The code to be tested
        rc, stdout, stderr = run_zhmc(zhmc_args, pdb_=pdb_, log=log)

        if log:
            print("Debug: test case log begin ------------------")
            print(stderr)
            print("Debug: test case log end --------------------")

        if not pdb_:
            export_vars = get_session_create_exports(stdout)
            session_id = export_vars.get('ZHMC_SESSION_ID', None)
            if session_id:
                cleanup_session_ids.append(session_id)

        assert_session_create(rc, stdout, stderr, hmc_definition,
                              exp_rc, exp_err, pdb_)

        # If a valid session ID was provided to the command in env vars,
        # verify that that session was deleted on the HMC
        if envvars.get('ZHMC_SESSION_ID', None) == 'valid' and rc == 0 \
                and session_ids:
            session_id = session_ids[0]
            assert not is_valid_hmc_session(hmc_definition, session_id)

    finally:
        for session_id in cleanup_session_ids:
            delete_hmc_session(hmc_definition, session_id)
        if run == 'sleep':
            time.sleep(60)


TESTCASE_SESSION_DELETE = [

    # Each item is a testcase for test_session_delete(), with the following
    # items:
    #
    # * desc (str): Testcase description
    # * envvars (dict): ZHMC env vars to be set before running command. Key is
    #   the var name; value indicates how to provide the var value:
    #   - omitted - var is not provided
    #   - 'valid' - var is provided with valid value from HMC definition
    #   - 'invalid' - var is provided with some invalid value
    # * logon_opts (str): zhmc logon options to be provided in the command.
    #   Key is the option name; value indicates how to provide the option value:
    #   - omitted - option is not provided
    #   - 'valid' - option is provided with valid value from HMC definition
    #   - 'invalid' - option is provided with some invalid value
    # * exp_rc (int): Expected command exit code.
    # * exp_err (str): Pattern for expected error message, or None for success.
    # * run: Testcase run control, as follows:
    #   - True - run the testcase
    #   - False - skip the testcase
    #   - 'pdb' - debug the testcase (wake up in pdb before command function)
    #   - 'log' - enable HMC logging and display the log records
    #   - 'sleep' - sleep for 60 sec after the testcase (used to circumvent
    #     temporary disablemnt of logong due to too many logons).

    (
        "'session delete' with no env vars and valid logon opts",
        # Since there is no session ID in the env vars, no session will be
        # deleted on the HMC. The credentials in the options are ignored.
        {},
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'valid',
            '-n': 'valid',
            '-c': 'valid',
        },
        0, None,
        True
    ),
    (
        "'session delete' with no env vars and logon opts with invalid pw",
        # Since there is no session ID in the env vars, no session will be
        # deleted on the HMC. The credentials in the options are ignored.
        {},
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'invalid',
            '-n': 'valid',
            '-c': 'valid',
        },
        0, None,
        True
    ),
    (
        "'session delete' with just session_id env var (valid session) "
        "and no logon opts",
        # A (valid) session ID is in the env vars, but for creating a Session
        # oject, an HMC host is also needed.
        {
            'ZHMC_SESSION_ID': 'valid',
        },
        {},
        1, 'No HMC host provided',
        True
    ),
    (
        "'session delete' with all env vars (valid session) "
        "and no logon opts",
        # The valid session ID in the env vars is used to successfully delete
        # the session on the HMC.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'valid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {},
        0, None,
        True
    ),
    (
        "'session delete' with all env vars (expired session) "
        "and no logon opts",
        # The invalid session in the env var is attempted to be deleted on the
        # HMC, which fails due to being invalid, which is ignored.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'invalid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {},
        0, None,
        True
    ),
    (
        "'session delete' with all env vars (valid session) "
        "and valid logon opts",
        # The valid session ID in the env vars is used to successfully delete
        # the session on the HMC. The credentials in the options are ignored.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'valid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'valid',
            '-n': 'valid',
            '-c': 'valid',
        },
        0, None,
        True
    ),
    (
        "'session delete' with all env vars (expired session) "
        "and valid logon opts",
        # The invalid session in the env var is attempted to be deleted on the
        # HMC, which fails due to being invalid, which is ignored. The
        # credentials in the options are ignored.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'invalid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'valid',
            '-n': 'valid',
            '-c': 'valid',
        },
        0, None,
        True
    ),
    (
        "'session delete' with all env vars (valid session) "
        "and logon opts with invalid pw",
        # The valid session ID in the env vars is used to successfully delete
        # the session on the HMC. The credentials in the options are ignored.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'valid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'invalid',
            '-n': 'valid',
            '-c': 'valid',
        },
        0, None,
        True
    ),
    (
        "'session delete' with all env vars (expired session) "
        "and logon opts with invalid pw",
        # The invalid session in the env var is attempted to be deleted on the
        # HMC, which fails due to being invalid, which is ignored. The
        # credentials in the options are ignored.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'invalid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'invalid',
            '-n': 'valid',
            '-c': 'valid',
        },
        0, None,
        True
    ),
]


@pytest.mark.parametrize(
    "desc, envvars, logon_opts, exp_rc, exp_err, run",
    TESTCASE_SESSION_DELETE
)
def test_session_delete(
        hmc_definition, desc, envvars, logon_opts, exp_rc,  # noqa: F811
        exp_err, run):
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Test 'session delete' command.
    """
    if run is False:
        pytest.skip("Testcase disabled")

    cleanup_session_ids = []
    try:
        session_ids = prepare_environ(os.environ, envvars, hmc_definition)
        cleanup_session_ids += session_ids
        logon_args = prepare_logon_args(logon_opts, hmc_definition)

        pdb_ = run == 'pdb'
        log = (run == 'log' or TESTLOG)

        zhmc_args = logon_args + ['session', 'delete']

        # The code to be tested
        rc, stdout, stderr = run_zhmc(zhmc_args, pdb_=pdb_, log=log)

        if log:
            print("Debug: test case log begin ------------------")
            print(stderr)
            print("Debug: test case log end --------------------")

        assert_session_delete(rc, stdout, stderr, hmc_definition,
                              exp_rc, exp_err, pdb_)

        # If a valid session ID was provided to the command in env vars,
        # verify that that session was deleted on the HMC
        if envvars.get('ZHMC_SESSION_ID', None) == 'valid' and rc == 0 \
                and session_ids:
            session_id = session_ids[0]
            assert not is_valid_hmc_session(hmc_definition, session_id)

    finally:
        for session_id in cleanup_session_ids:
            delete_hmc_session(hmc_definition, session_id)
        if run == 'sleep':
            time.sleep(60)


TESTCASE_SESSION_COMMAND = [

    # Each item is a testcase for test_session_command(), with the following
    # items:
    #
    # * desc (str): Testcase description
    # * envvars (dict): ZHMC env vars to be set before running command. Key is
    #   the var name; value indicates how to provide the var value:
    #   - omitted - var is not provided
    #   - 'valid' - var is provided with valid value from HMC definition
    #   - 'invalid' - var is provided with some invalid value
    # * logon_opts (str): zhmc logon options to be provided in the command.
    #   Key is the option name; value indicates how to provide the option value:
    #   - omitted - option is not provided
    #   - 'valid' - option is provided with valid value from HMC definition
    #   - 'invalid' - option is provided with some invalid value
    # * exp_rc (int): Expected command exit code.
    # * exp_err (str): Pattern for expected error message, or None for success.
    # * run: Testcase run control, as follows:
    #   - True - run the testcase
    #   - False - skip the testcase
    #   - 'pdb' - debug the testcase (wake up in pdb before command function)
    #   - 'log' - enable HMC logging and display the log records
    #   - 'sleep' - sleep for 60 sec after the testcase (used to circumvent
    #     temporary disablemnt of logong due to too many logons).

    (
        "Simple command with no env vars and valid logon opts",
        # Since there is no session ID in the env vars, a new session is created
        # on the HMC, using the valid password, and again deleted on the HMC
        # after the command.
        {},
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'valid',
            '-n': 'valid',
            '-c': 'valid',
        },
        0, None,
        True
    ),
    (
        "Simple command with no env vars and logon opts with invalid pw",
        # Since there is no session ID in the env vars, a new session is created
        # on the HMC, using the invalid password, which fails.
        {},
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'invalid',
            '-n': 'valid',
            '-c': 'valid',
        },
        1, "ServerAuthError: HTTP authentication failed with 403,0",
        True
    ),
    (
        "Simple command with just session_id env var (valid session) "
        "and no logon opts",
        # A (valid) session ID is in the env vars, but for creating a Session
        # oject, an HMC host is also needed.
        {
            'ZHMC_SESSION_ID': 'valid',
        },
        {},
        1, 'No HMC host provided',
        True
    ),
    (
        "Simple command with all env vars (valid session) "
        "and no logon opts",
        # The valid session ID in the env vars is used to execute the command
        # on the HMC. The session is not deleted after the command.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'valid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {},
        0, None,
        True
    ),
    (
        "Simple command with all env vars (expired session) "
        "and no logon opts",
        # The invalid session ID in the env vars is attempted to be used to
        # execute the command, which fails, which causes a session renewal.
        # Because no password is created, it is prompted for.
        # A new session is created on the HMC and then the command is
        # successfully executed. The session is deleted after the command
        # (because it cannot be stored for reuse anyway).
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'invalid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {},
        0, None,
        False  # TODO: Provide the password to the password prompt
    ),
    (
        "Simple command with all env vars (valid session) "
        "and valid logon opts",
        # The valid session ID in the env vars is used to execute the command
        # on the HMC. The session is not deleted after the command. The
        # credentials in the options are not used.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'valid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'valid',
            '-n': 'valid',
            '-c': 'valid',
        },
        0, None,
        True
    ),
    (
        "Simple command with all env vars (expired session) "
        "and valid logon opts",
        # The invalid session ID in the env vars is attempted to be used to
        # execute the command, which fails, which causes a session renewal.
        # A new session is created on the HMC using the valid password,
        # and then the command is successfully executed. The session is
        # deleted after the command (because it cannot be stored for reuse
        # anyway).
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'invalid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'valid',
            '-n': 'valid',
            '-c': 'valid',
        },
        0, None,
        True
    ),
    (
        "Simple command with all env vars (valid session) "
        "and logon opts with invalid pw",
        # The valid session ID in the env vars is used to execute the command
        # on the HMC. The session is not deleted after the command. The
        # credentials in the options are not used, so it does not matter
        # that the password is invalid.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'valid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'invalid',
            '-n': 'valid',
            '-c': 'valid',
        },
        0, None,
        True
    ),
    (
        "Simple command with all env vars (expired session) "
        "and logon opts with invalid pw",
        # The invalid session ID in the env vars is attempted to be used to
        # execute the command, which fails, which causes a session renewal.
        # A new session is attempted to be created on the HMC using the invalid
        # password, which fails.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'invalid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'invalid',
            '-n': 'valid',
            '-c': 'valid',
        },
        1, "ServerAuthError: HTTP authentication failed with 403,0",
        True
    ),
]


@pytest.mark.parametrize(
    "desc, envvars, logon_opts, exp_rc, exp_err, run",
    TESTCASE_SESSION_COMMAND
)
def test_session_command(
        hmc_definition, desc, envvars, logon_opts, exp_rc,  # noqa: F811
        exp_err, run):
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Test sessions used with a simple command 'cpc list --names-only'.
    """
    if run is False:
        pytest.skip("Testcase disabled")

    cleanup_session_ids = []
    try:
        session_ids = prepare_environ(os.environ, envvars, hmc_definition)
        cleanup_session_ids += session_ids
        logon_args = prepare_logon_args(logon_opts, hmc_definition)

        pdb_ = run == 'pdb'
        log = (run == 'log' or TESTLOG)

        zhmc_args = logon_args + ['cpc', 'list', '--names-only']

        # The code to be tested
        # pylint: disable=unused-variable
        rc, stdout, stderr = run_zhmc(zhmc_args, pdb_=pdb_, log=log)

        if log:
            print("Debug: test case log begin ------------------")
            print(stderr)
            print("Debug: test case log end --------------------")

        assert_session_command(rc, stdout, stderr, hmc_definition,
                               exp_rc, exp_err, pdb_)

        # If a valid session ID was provided to the command in env vars,
        # verify that that session was not deleted on the HMC
        if envvars.get('ZHMC_SESSION_ID', None) == 'valid' and rc == 0 \
                and session_ids:
            session_id = session_ids[0]
            assert is_valid_hmc_session(hmc_definition, session_id)

    finally:
        for session_id in cleanup_session_ids:
            delete_hmc_session(hmc_definition, session_id)
        if run == 'sleep':
            time.sleep(60)
