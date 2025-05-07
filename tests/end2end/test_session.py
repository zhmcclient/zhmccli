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
import subprocess
import urllib3
import yaml
import pytest

# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import
from zhmcclient.testutils import setup_hmc_session, teardown_hmc_session_id, \
    is_valid_hmc_session_id

from zhmccli._session_file import DEFAULT_SESSION_NAME
from ..function.test_session_file import create_session_file, \
    delete_session_file, session_file_content
from .utils import env2bool

urllib3.disable_warnings()

URLLIB3_VERSION = [int(v) for v in urllib3.__version__.split('.')]

if URLLIB3_VERSION < [2, 0]:
    INVALID_HOST_MSG = "Failed to establish a new connection:"
else:
    INVALID_HOST_MSG = "Failed to resolve"

# Enable logging via environment
TESTLOG = env2bool('TESTLOG')


def assert_session_logon(
        rc, stdout, stderr, env_session_id, sf_session_id, session_name,
        result_sf_str, hmc_definition,  # noqa: F811
        exp_rc, exp_err, pdb_):
    # pylint: disable=redefined-outer-name
    """
    Check the result of a 'session logon' command.
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
        result_sf_data = yaml.load(result_sf_str, Loader=yaml.SafeLoader)
        if session_name is None:
            session_name = DEFAULT_SESSION_NAME

        assert session_name in result_sf_data
        result_sf_dict = result_sf_data[session_name]
        result_session_id = result_sf_dict['session_id']

        assert result_sf_dict['host'] == hmc_definition.host
        assert result_sf_dict['userid'] == hmc_definition.userid
        assert result_sf_dict['ca_verify'] == hmc_definition.verify
        assert result_sf_dict['ca_cert_path'] == hmc_definition.ca_certs

        assert_session_state_logon(
            result_session_id, env_session_id, sf_session_id, hmc_definition)


def assert_session_create(
        rc, stdout, stderr, env_session_id, sf_session_id,
        hmc_definition,  # noqa: F811
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
        result_session_id = export_vars.pop('ZHMC_SESSION_ID')

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

        assert_session_state_logon(
            result_session_id, env_session_id, sf_session_id, hmc_definition)


def assert_session_state_logon(
        result_session_id, env_session_id, sf_session_id,
        hmc_definition):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Verify the session state after the logon.
    """
    # If a valid session ID was provided to the command in the env vars,
    # verify that it is still valid and that it has not been reused for the
    # new session ID.
    if env_session_id:
        assert is_valid_hmc_session_id(hmc_definition, env_session_id)
        assert result_session_id != env_session_id

    # If a valid session ID was provided to the command in the session file,
    # verify that it is still valid and that it has not been reused for the
    # new session ID.
    if sf_session_id:
        assert is_valid_hmc_session_id(hmc_definition, sf_session_id)
        assert result_session_id != sf_session_id


def assert_session_logoff(
        rc, stdout, stderr, logon_opts, envvars, env_session_id, sf_session_id,
        session_name, result_sf_str,
        hmc_definition,  # noqa: F811
        exp_rc, exp_err, pdb_):
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Check the result of a 'session logoff' command.
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

        # Verify that the session is not in the updated HMC session file.
        result_sf_data = yaml.load(result_sf_str, Loader=yaml.SafeLoader)
        if session_name is None:
            session_name = DEFAULT_SESSION_NAME
        assert session_name not in result_sf_data

        assert_session_state_logoff(
            logon_opts, envvars, env_session_id, sf_session_id, hmc_definition)


def assert_session_delete(
        rc, stdout, stderr, logon_opts, envvars, env_session_id, sf_session_id,
        session_name, result_sf_str,
        hmc_definition,  # noqa: F811
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

        assert 'ZHMC_HOST' in unset_vars
        del unset_vars['ZHMC_HOST']
        assert 'ZHMC_USERID' in unset_vars
        del unset_vars['ZHMC_USERID']
        assert 'ZHMC_SESSION_ID' in unset_vars
        del unset_vars['ZHMC_SESSION_ID']
        assert 'ZHMC_NO_VERIFY' in unset_vars
        del unset_vars['ZHMC_NO_VERIFY']
        assert 'ZHMC_CA_CERTS' in unset_vars
        del unset_vars['ZHMC_CA_CERTS']

        assert not export_vars
        assert not unset_vars

        assert_session_state_logoff(
            logon_opts, envvars, env_session_id, sf_session_id, hmc_definition)


def assert_session_state_logoff(
        logon_opts, envvars, env_session_id, sf_session_id,
        hmc_definition):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Verify the session state after the logoff.
    """
    # If a valid session ID was provided to the command in the env vars,
    # verify the state of its session on the HMC.
    if env_session_id:
        if '-h' not in logon_opts and '--host' not in logon_opts and \
                'ZHMC_HOST' in envvars:
            # Logon data came from the env vars. Verify that the session
            # has been deleted.
            assert not is_valid_hmc_session_id(hmc_definition, env_session_id)
        else:
            # Logon data came from the logon options or session file.
            # Verify that the session is still valid.
            assert is_valid_hmc_session_id(hmc_definition, env_session_id)

    # If a valid session ID was provided to the command in the session file,
    # verify the state of its session on the HMC.
    if sf_session_id:
        if '-h' not in logon_opts and '--host' not in logon_opts and \
                'ZHMC_HOST' not in envvars:
            # Logon data came from the session file. Verify that the session
            # has been deleted.
            assert not is_valid_hmc_session_id(hmc_definition, sf_session_id)
        else:
            # Logon data came from the logon options or env vars.
            # Verify that the session is still valid.
            assert is_valid_hmc_session_id(hmc_definition, sf_session_id)


def assert_session_command(
        rc, stdout, stderr, env_session_id, sf_session_id,
        hmc_definition,  # noqa: F811
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

    # If a valid session ID was provided to the command in the env vars,
    # verify that that session was not deleted on the HMC
    if env_session_id:
        assert is_valid_hmc_session_id(hmc_definition, env_session_id)

    # If a valid session ID was provided to the command in the session file,
    # verify that that session was not deleted on the HMC
    if sf_session_id:
        assert is_valid_hmc_session_id(hmc_definition, sf_session_id)


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

    Returns:
      str: Session ID to be cleaned up, if a valid session was created. None,
        if no session ID needs to be cleaned up.
    """
    cleanup_session_id = None

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
                session = setup_hmc_session(hmc_definition)
                cleanup_session_id = session.session_id
                environ[name] = session.session_id
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

    return cleanup_session_id


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
                    logon_args.extend([name, 'invalid-cert-path'])
        else:
            raise AssertionError(
                "Invalid testcase: logon_opts specifies unknown "
                "option: {!r}".format(name))

    return logon_args


def prepare_session_content(sf_str, hmc_definition):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Update HMC session file content to replace 'valid' with the valid
    values from the HMC definition, and 'invalid' with invalid values.

    Parameters:
      sf_str (str): HMC session file content, with values that may be
        'valid' or 'invalid'.
      hmc_definition (): HMC definition.

    Returns:
      str: HMC session file content, with 'valid' and 'invalid' values replaced.
    """
    sf_data = yaml.load(sf_str, Loader=yaml.SafeLoader)
    for item in sf_data.values():
        if item['host'] == 'valid':
            item['host'] = hmc_definition.host
        elif item['host'] == 'invalid':
            item['host'] = 'invalid-host'
        if item['userid'] == 'valid':
            item['userid'] = hmc_definition.userid
        elif item['userid'] == 'invalid':
            item['userid'] = 'invalid-userid'
        sf_session_id = None
        if item['session_id'] == 'valid':
            session = setup_hmc_session(hmc_definition)
            item['session_id'] = session.session_id
            sf_session_id = item['session_id']
        elif item['session_id'] == 'invalid':
            item['session_id'] = 'invalid-session-id'
        if item['ca_verify'] == 'valid':
            item['ca_verify'] = hmc_definition.verify
        elif item['ca_verify'] == 'invalid':
            # Do it the opposite way -> invalid
            item['ca_verify'] = not hmc_definition.verify
        if item['ca_cert_path'] == 'valid':
            item['ca_cert_path'] = hmc_definition.ca_certs
        elif item['ca_cert_path'] == 'invalid':
            item['ca_cert_path'] = 'invalid-cert-path'
    sf_str = yaml.dump(sf_data)
    return sf_str, sf_session_id


def run_zhmc_with_session_file(
        args, env=None, pdb_=False, log=False, initial_sf_str=None):
    """
    Run the zhmc command after preparing an HMC session file and return its
    exit code, stdout and stderr.

    Parameters:

      args(list/tuple of str): List of command line arguments, not including
        the 'zhmc' command name itself.

      env(dict of str/str): Environment variables to be used instead of the
        current process' variables.

      pdb_(bool): If True, debug the zhmc command. This is done by inserting
        the '--pdb' option to the command arguments, and by not capturing the
        stdout/stderr.

        If both log and pdb_ are set, only pdb_ is performed.

      log(bool): If True, enable HMC logging for the zhmc command. This is done
        by inserting the '--log hmc=debug' option to the command arguments,
        and by not capturing the stdout/stderr.

        If both log and pdb_ are set, only pdb_ is performed.

      initial_sf_str(str): Initial content of HMC session file to be created for
        use by this zhmc run. If None, an empty HMC session file is created.

    Returns:
      tuple (rc, stdout, stderr) as follows:
      - rc(int): zhmc exit code
      - stdout(str): stdout string, or None if debugging the zhmc command
      - stderr(str): stderr string, or None if debugging the zhmc command
      - result_sf_str(str): Resulting content of HMC session file
    """
    assert isinstance(args, (list, tuple))
    if env is not None:
        assert isinstance(env, dict)

    p_args = ['zhmc'] + args

    # Set up output capturing, dependent on pdb_ flag
    if pdb_:
        kwargs = {}
        p_args.insert(1, '--pdb')
    else:
        if log:
            p_args.insert(1, 'all=debug')
            p_args.insert(1, '--log')
        kwargs = {
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
        }

    # Prepare the temporary HMC session file for this test and make sure it
    # is used.
    session_file = create_session_file(initial_sf_str)
    os.environ['_ZHMC_TEST_SESSION_FILEPATH'] = session_file.filepath

    try:

        # pylint: disable=consider-using-with
        proc = subprocess.Popen(p_args, env=env, **kwargs)

        stdout, stderr = proc.communicate()
        rc = proc.returncode
        if not pdb_:
            stdout = stdout.decode()
            stderr = stderr.decode()

        result_sf_str = session_file_content(session_file)

    finally:
        delete_session_file(session_file)

    return rc, stdout, stderr, result_sf_str


TESTCASE_SESSION_LOGON_CREATE = [

    # Each item is a testcase for test_session_logon() and
    # test_session_create(), with the following items:
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
    # * session_name (str): Session name in HMC session file to be used, used
    #   to specify the '-s' option. None means the option is not specified,
    #   using the default session name.
    # * initial_sf_str (str): Initial content of HMC session file to be
    #   created for the zhmc run. If None, an empty HMC session file is created.
    # * exp_rc (int): Expected command exit code.
    # * exp_err (str): Pattern for expected error message, or None for success.
    # * run: Testcase run control, as follows:
    #   - True - run the testcase
    #   - False - skip the testcase
    #   - 'pdb' - debug the testcase (wake up in pdb before command function)
    #   - 'log' - enable HMC logging and display the log records
    #   - 'sleep' - sleep for 60 sec after the testcase (used to circumvent
    #     temporary disablement of logon due to too many logons).

    (
        "Logon data from logon opts (no env vars, empty session file)",
        # A new session is created from the logon options, using the valid
        # password.
        {},
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'valid',
            '-n': 'valid',
            '-c': 'valid',
        },
        None,
        None,
        0, None,
        True
    ),
    (
        "Logon data from logon opts without -c",
        # A new session is created from the logon options, using the valid
        # password. Because -n is specified, it does not matter that -c is
        # omitted.
        {},
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'valid',
            '-n': 'valid',
        },
        None,
        None,
        0, None,
        True
    ),
    (
        "Logon data from logon opts with missing -u",
        # If logon options are used (detected by presence of -h), a userid is
        # required.
        {},
        {
            '-h': 'valid',
        },
        None,
        None,
        1, "Required option not specified: --userid",
        True
    ),
    (
        "Logon data from logon opts with invalid password",
        # A new session is attempted to be created from the logon options,
        # which fails due to the invalid password.
        {},
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'invalid',
            '-n': 'valid',
            '-c': 'valid',
        },
        None,
        None,
        1, "ServerAuthError: HTTP authentication failed with 403,0",
        True
    ),
    (
        "Just valid session ID in env vars",
        # A (valid) session ID is in the env vars, but for creating a Session
        # object, host and userid are also needed.
        {
            'ZHMC_SESSION_ID': 'valid',
        },
        {},
        None,
        None,
        1, 'No HMC host or session in HMC session file provided',
        True
    ),
    (
        "Logon data from env vars with valid session ID",
        # A new session is created from the env vars, using the valid password.
        # It does not matter that a valid session ID is specified, because the
        # logon happens regardless of that.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'valid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {
            '-p': 'valid',
        },
        None,
        None,
        0, None,
        True
    ),
    (
        "Logon data from env vars with invalid session ID",
        # A new session is created from the env vars, using the valid password.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'invalid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {
            '-p': 'valid',
        },
        None,
        None,
        0, None,
        True
    ),
    (
        "Logon data from env vars with invalid password",
        # A new session is attempted to be created from the env vars, which
        # fails due to the invalid password. It does not matter that a valid
        # session ID is specified, because the logon happens regardless of that.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'valid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {
            '-p': 'invalid',
        },
        None,
        None,
        1, "ServerAuthError: HTTP authentication failed with 403,0",
        True
    ),
    (
        "Logon data from logon opts preceding env vars",
        # A new session is created from the logon options, using the valid
        # password. The logon options take precedence and the env vars are
        # ignored, which is verified by specifying an invalid host.
        {
            'ZHMC_HOST': 'invalid',
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
        None,
        None,
        0, None,
        True
    ),
    (
        "Logon data from session file with valid session ID",
        # A new session is created from the session file, using the valid
        # password. It does not matter that a valid session ID is specified,
        # because the logon happens regardless of that.
        {},
        {
            '-p': 'valid',
        },
        None,
        """
default:
  host: valid
  userid: valid
  session_id: valid
  ca_verify: valid
  ca_cert_path: valid
  creation_time: "2025-05-06 07:14:58"
""",
        0, None,
        True
    ),
    (
        "Logon data from session file with invalid password",
        # A new session is attempted to be created from the session file, which
        # fails due to the invalid password. It does not matter that a valid
        # session ID is specified, because the logon happens regardless of that.
        {},
        {
            '-p': 'invalid',
        },
        None,
        """
default:
  host: valid
  userid: valid
  session_id: valid
  ca_verify: valid
  ca_cert_path: valid
  creation_time: "2025-05-06 07:14:58"
""",
        1, "ServerAuthError: HTTP authentication failed with 403,0",
        True
    ),
    (
        "Logon data from session file with session name",
        # A new session is created from the session file, using the valid
        # password. It does not matter that a valid session ID is specified,
        # because the logon happens regardless of that.
        # The specified session s1 is used, which is verified by defining the
        # default session with invalid values.
        {},
        {
            '-p': 'valid',
        },
        's1',
        """
default:
  host: invalid
  userid: invalid
  session_id: invalid
  ca_verify: invalid
  ca_cert_path: invalid
  creation_time: "2025-05-06 07:14:58"
s1:
  host: valid
  userid: valid
  session_id: valid
  ca_verify: valid
  ca_cert_path: valid
  creation_time: "2025-05-06 07:18:58"
""",
        0, None,
        True
    ),
    (
        "Logon data from logon opts preceding session file",
        # A new session is created from the logon options, using the valid
        # password. It does not matter that a valid session ID is specified,
        # because the logon happens regardless of that. The logon options take
        # precedence over the session file, which is verified by specifying an
        # invalid host there.
        {},
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'valid',
            '-n': 'valid',
            '-c': 'valid',
        },
        None,
        """
default:
  host: invalid
  userid: valid
  session_id: valid
  ca_verify: valid
  ca_cert_path: valid
  creation_time: "2025-05-06 07:14:58"
""",
        0, None,
        True
    ),
    (
        "Logon data from env vars preceding session file",
        # A new session is created from the env vars, using the valid
        # password. It does not matter that a valid session ID is specified,
        # because the logon happens regardless of that. The env vars take
        # precedence over the session file, which is verified by specifying an
        # invalid host there.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'valid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {
            '-p': 'valid',
        },
        None,
        """
default:
  host: invalid
  userid: valid
  session_id: valid
  ca_verify: valid
  ca_cert_path: valid
  creation_time: "2025-05-06 07:14:58"
""",
        0, None,
        True
    ),
    (
        "No connection to host",
        # A new session is created from the logon options, with an invalid HMC
        # host.
        {},
        {
            '-h': 'invalid',
            '-u': 'valid',
            '-p': 'valid',
            '-n': 'valid',
            '-c': 'valid',
        },
        None,
        None,
        1, "ConnectionError: .* Max retries exceeded",
        True
    ),
]


@pytest.mark.parametrize(
    "desc, envvars, logon_opts, session_name, initial_sf_str, exp_rc, "
    "exp_err, run",
    TESTCASE_SESSION_LOGON_CREATE
)
def test_session_logon(
        hmc_definition,  # noqa: F811
        desc, envvars, logon_opts, session_name, initial_sf_str, exp_rc,
        exp_err, run):
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Test 'session logon' command.
    """
    if run is False:
        pytest.skip("Testcase disabled")

    cleanup_session_ids = []
    try:
        env_session_id = prepare_environ(os.environ, envvars, hmc_definition)
        cleanup_session_ids.append(env_session_id)
        logon_args = prepare_logon_args(logon_opts, hmc_definition)
        if session_name:
            logon_args.extend(['-s', session_name])
        else:
            session_name = DEFAULT_SESSION_NAME
        if initial_sf_str is not None:
            initial_sf_str, sf_session_id = prepare_session_content(
                initial_sf_str, hmc_definition)
        else:
            sf_session_id = None

        pdb_ = run == 'pdb'
        log = (run == 'log' or TESTLOG)

        zhmc_args = logon_args + ['session', 'logon']

        # The code to be tested
        rc, stdout, stderr, result_sf_str = run_zhmc_with_session_file(
            zhmc_args, pdb_=pdb_, log=log, initial_sf_str=initial_sf_str)

        if log:
            print("Debug: test case log begin ------------------")
            print(stderr)
            print("Debug: test case log end --------------------")

        assert_session_logon(
            rc, stdout, stderr, env_session_id, sf_session_id, session_name,
            result_sf_str, hmc_definition, exp_rc, exp_err, pdb_)

    finally:
        for session_id in cleanup_session_ids:
            teardown_hmc_session_id(hmc_definition, session_id)
        if run == 'sleep':
            time.sleep(60)


@pytest.mark.parametrize(
    "desc, envvars, logon_opts, session_name, initial_sf_str, exp_rc, "
    "exp_err, run",
    TESTCASE_SESSION_LOGON_CREATE
)
def test_session_create(
        hmc_definition,  # noqa: F811
        desc, envvars, logon_opts, session_name, initial_sf_str, exp_rc,
        exp_err, run):
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Test 'session create' command.
    """
    if run is False:
        pytest.skip("Testcase disabled")

    cleanup_session_ids = []
    try:
        env_session_id = prepare_environ(os.environ, envvars, hmc_definition)
        cleanup_session_ids.append(env_session_id)
        logon_args = prepare_logon_args(logon_opts, hmc_definition)
        if session_name:
            logon_args.extend(['-s', session_name])
        else:
            session_name = DEFAULT_SESSION_NAME
        if initial_sf_str is not None:
            initial_sf_str, sf_session_id = prepare_session_content(
                initial_sf_str, hmc_definition)
        else:
            sf_session_id = None

        pdb_ = run == 'pdb'
        log = (run == 'log' or TESTLOG)

        zhmc_args = logon_args + ['session', 'create']

        # The code to be tested
        rc, stdout, stderr, _ = run_zhmc_with_session_file(
            zhmc_args, pdb_=pdb_, log=log, initial_sf_str=initial_sf_str)

        if log:
            print("Debug: test case log begin ------------------")
            print(stderr)
            print("Debug: test case log end --------------------")

        if not pdb_ and rc == 0:
            export_vars = get_session_create_exports(stdout)
            new_session_id = export_vars.get('ZHMC_SESSION_ID', None)
            if new_session_id:
                cleanup_session_ids.append(new_session_id)

        assert_session_create(
            rc, stdout, stderr, env_session_id, sf_session_id,
            hmc_definition, exp_rc, exp_err, pdb_)

    finally:
        for session_id in cleanup_session_ids:
            teardown_hmc_session_id(hmc_definition, session_id)
        if run == 'sleep':
            time.sleep(60)


TESTCASE_SESSION_LOGOFF = [

    # Each item is a testcase for test_session_logoff(), with the following
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
    # * session_name (str): Session name in HMC session file to be used, used
    #   to specify the '-s' option. None means the option is not specified,
    #   using the default session name.
    # * initial_sf_str (str): Initial content of HMC session file to be
    #   created for the zhmc run. If None, an empty HMC session file is created.
    # * exp_rc (int): Expected command exit code.
    # * exp_err (str): Pattern for expected error message, or None for success.
    # * run: Testcase run control, as follows:
    #   - True - run the testcase
    #   - False - skip the testcase
    #   - 'pdb' - debug the testcase (wake up in pdb before command function)
    #   - 'log' - enable HMC logging and display the log records
    #   - 'sleep' - sleep for 60 sec after the testcase (used to circumvent
    #     temporary disablement of logon due to too many logons).

    (
        "Empty session file, no env vars and no logon opts",
        # Fails because the default session is not found in the session file.
        {},
        {},
        None,
        None,
        1, "Session not found .*: default",
        True
    ),
    (
        "Logon opts not allowed (with empty session file)",
        # Rejected because 'session logoff' intends to delete the session
        # defined in the session file.
        {},
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'valid',
            '-n': 'valid',
            '-c': 'valid',
        },
        None,
        None,
        1, " Invalid logon source .*: options",
        True
    ),
    (
        "Logon opts not allowed (with default session file)",
        # Rejected because 'session logoff' intends to delete the session
        # defined in the session file. The presence of the default session in
        # the session file does not matter for this.
        {},
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'valid',
            '-n': 'valid',
            '-c': 'valid',
        },
        None,
        """
default:
  host: valid
  userid: valid
  session_id: valid
  ca_verify: valid
  ca_cert_path: valid
  creation_time: "2025-05-06 07:14:58"
""",
        1, " Invalid logon source .*: options",
        True
    ),
    (
        "Env vars not allowed (with empty session file)",
        # Rejected because 'session logoff' intends to delete the session
        # defined in the session file.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'valid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {},
        None,
        None,
        1, " Invalid logon source .*: environment",
        True
    ),
    (
        "Env vars not allowed (with default session file)",
        # Rejected because 'session logoff' intends to delete the session
        # defined in the session file. The presence of the default session in
        # the session file does not matter for this.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'valid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {},
        None,
        """
default:
  host: valid
  userid: valid
  session_id: valid
  ca_verify: valid
  ca_cert_path: valid
  creation_time: "2025-05-06 07:14:58"
""",
        1, " Invalid logon source .*: environment",
        True
    ),
    (
        "Logon data from session file with valid session ID",
        # The valid session from the session file is deleted on the HMC.
        {},
        {},
        None,
        """
default:
  host: valid
  userid: valid
  session_id: valid
  ca_verify: valid
  ca_cert_path: valid
  creation_time: "2025-05-06 07:14:58"
""",
        0, None,
        True
    ),
    (
        "Logon data from session file with invalid session ID",
        # The invalid session from the session file is attempted to be deleted,
        # which fails because it is invalid. This failure is ignored.
        {},
        {},
        None,
        """
default:
  host: valid
  userid: valid
  session_id: invalid
  ca_verify: valid
  ca_cert_path: valid
  creation_time: "2025-05-06 07:14:58"
""",
        0, None,
        True
    ),
    (
        "Logon data from session file with session name",
        # The valid session s1 from the session file is deleted.
        {},
        {},
        's1',
        """
default:
  host: invalid
  userid: invalid
  session_id: invalid
  ca_verify: invalid
  ca_cert_path: invalid
  creation_time: "2025-05-06 07:14:58"
s1:
  host: valid
  userid: valid
  session_id: valid
  ca_verify: valid
  ca_cert_path: valid
  creation_time: "2025-05-06 07:18:58"
""",
        0, None,
        True
    ),
]


@pytest.mark.parametrize(
    "desc, envvars, logon_opts, session_name, initial_sf_str, exp_rc, "
    "exp_err, run",
    TESTCASE_SESSION_LOGOFF
)
def test_session_logoff(
        hmc_definition,  # noqa: F811
        desc, envvars, logon_opts, session_name, initial_sf_str, exp_rc,
        exp_err, run):
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Test 'session logoff' command.
    """
    if run is False:
        pytest.skip("Testcase disabled")

    cleanup_session_ids = []
    try:
        env_session_id = prepare_environ(os.environ, envvars, hmc_definition)
        cleanup_session_ids.append(env_session_id)
        logon_args = prepare_logon_args(logon_opts, hmc_definition)
        if session_name:
            logon_args.extend(['-s', session_name])
        else:
            session_name = DEFAULT_SESSION_NAME
        if initial_sf_str is not None:
            initial_sf_str, sf_session_id = prepare_session_content(
                initial_sf_str, hmc_definition)
        else:
            sf_session_id = None

        pdb_ = run == 'pdb'
        log = (run == 'log' or TESTLOG)

        zhmc_args = logon_args + ['session', 'logoff']

        # The code to be tested
        rc, stdout, stderr, result_sf_str = run_zhmc_with_session_file(
            zhmc_args, pdb_=pdb_, log=log, initial_sf_str=initial_sf_str)

        if log:
            print("Debug: test case log begin ------------------")
            print(stderr)
            print("Debug: test case log end --------------------")

        assert_session_logoff(
            rc, stdout, stderr, logon_opts, envvars, env_session_id,
            sf_session_id, session_name, result_sf_str, hmc_definition,
            exp_rc, exp_err, pdb_)

    finally:
        for session_id in cleanup_session_ids:
            teardown_hmc_session_id(hmc_definition, session_id)
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
    # * session_name (str): Session name in HMC session file to be used, used
    #   to specify the '-s' option. None means the option is not specified,
    #   using the default session name.
    # * initial_sf_str (str): Initial content of HMC session file to be
    #   created for the zhmc run. If None, an empty HMC session file is created.
    # * exp_rc (int): Expected command exit code.
    # * exp_err (str): Pattern for expected error message, or None for success.
    # * run: Testcase run control, as follows:
    #   - True - run the testcase
    #   - False - skip the testcase
    #   - 'pdb' - debug the testcase (wake up in pdb before command function)
    #   - 'log' - enable HMC logging and display the log records
    #   - 'sleep' - sleep for 60 sec after the testcase (used to circumvent
    #     temporary disablement of logon due to too many logons).

    (
        "No env vars and no logon opts",
        # Since there is no session ID in the env vars, no session will be
        # deleted on the HMC. The unset commands are still displayed.
        {},
        {},
        None,
        None,
        0, None,
        True
    ),
    (
        "Logon opts not allowed",
        # Rejected because 'session delete' intends to delete the session
        # defined in the env vars.
        {},
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'valid',
            '-n': 'valid',
            '-c': 'valid',
        },
        None,
        None,
        1, "Invalid logon source .*: options",
        True
    ),
    (
        "Session name option not allowed",
        # Rejected because 'session delete' intends to delete the session
        # defined in the env vars.
        {},
        {},
        'default',
        """
default:
  host: valid
  userid: valid
  session_id: valid
  ca_verify: valid
  ca_cert_path: valid
  creation_time: "2025-05-06 07:14:58"
""",
        1, "Invalid logon source .*: session file",
        True
    ),
    (
        "Just session ID env var with a valid session",
        # Because ZHMC_HOST is not set, this is not recognized as logon data
        # from env vars, so the logon data defaults to the HMC session file,
        # where no session is defined. As a result, no session is deleted on
        # the HMC. The unset commands are still displayed.
        {
            'ZHMC_SESSION_ID': 'valid',
        },
        {},
        None,
        None,
        0, None,
        True
    ),
    (
        "Just session ID env var with an invalid session",
        # Because ZHMC_HOST is not set, this is not recognized as logon data
        # from env vars, so the logon data defaults to the HMC session file,
        # where no session is defined. As a result, no session is deleted on
        # the HMC. The unset commands are still displayed.
        {
            'ZHMC_SESSION_ID': 'invalid',
        },
        {},
        None,
        None,
        0, None,
        True
    ),
    (
        "All env vars with a valid session",
        # The session is logged off on the HMC and the unset commands are
        # displayed.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'valid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {},
        None,
        None,
        0, None,
        True
    ),
    (
        "All env vars with an invalid session",
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
        None,
        None,
        0, None,
        True
    ),
    (
        "Session file is ignored",
        # An existing session file is ignored as long as it is not the logon
        # source.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'valid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {},
        None,
        """
default:
  host: valid
  userid: valid
  session_id: valid
  ca_verify: valid
  ca_cert_path: valid
  creation_time: "2025-05-06 07:14:58"
""",
        0, None,
        True
    ),
]


@pytest.mark.parametrize(
    "desc, envvars, logon_opts, session_name, initial_sf_str, exp_rc, "
    "exp_err, run",
    TESTCASE_SESSION_DELETE
)
def test_session_delete(
        hmc_definition,  # noqa: F811
        desc, envvars, logon_opts, session_name, initial_sf_str, exp_rc,
        exp_err, run):
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Test 'session delete' command.
    """
    if run is False:
        pytest.skip("Testcase disabled")

    cleanup_session_ids = []
    try:
        env_session_id = prepare_environ(os.environ, envvars, hmc_definition)
        cleanup_session_ids.append(env_session_id)
        logon_args = prepare_logon_args(logon_opts, hmc_definition)
        if session_name:
            logon_args.extend(['-s', session_name])
        else:
            session_name = DEFAULT_SESSION_NAME
        if initial_sf_str is not None:
            initial_sf_str, sf_session_id = prepare_session_content(
                initial_sf_str, hmc_definition)
        else:
            sf_session_id = None

        pdb_ = run == 'pdb'
        log = (run == 'log' or TESTLOG)

        zhmc_args = logon_args + ['session', 'delete']

        # The code to be tested
        rc, stdout, stderr, result_sf_str = run_zhmc_with_session_file(
            zhmc_args, pdb_=pdb_, log=log, initial_sf_str=initial_sf_str)

        if log:
            print("Debug: test case log begin ------------------")
            print(stderr)
            print("Debug: test case log end --------------------")

        assert_session_delete(
            rc, stdout, stderr, logon_opts, envvars, env_session_id,
            sf_session_id, session_name, result_sf_str, hmc_definition,
            exp_rc, exp_err, pdb_)

    finally:
        for session_id in cleanup_session_ids:
            teardown_hmc_session_id(hmc_definition, session_id)
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
    # * session_name (str): Session name in HMC session file to be used, used
    #   to specify the '-s' option. None means the option is not specified,
    #   using the default session name.
    # * initial_sf_str (str): Initial content of HMC session file to be
    #   created for the zhmc run. If None, an empty HMC session file is created.
    # * exp_rc (int): Expected command exit code.
    # * exp_err (str): Pattern for expected error message, or None for success.
    # * run: Testcase run control, as follows:
    #   - True - run the testcase
    #   - False - skip the testcase
    #   - 'pdb' - debug the testcase (wake up in pdb before command function)
    #   - 'log' - enable HMC logging and display the log records
    #   - 'sleep' - sleep for 60 sec after the testcase (used to circumvent
    #     temporary disablement of logon due to too many logons).

    (
        "Logon data from opts",
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
        None,
        None,
        0, None,
        True
    ),
    (
        "Logon data from logon opts without -c",
        # Since there is no session ID in the env vars, a new session is created
        # on the HMC, using the valid password, and again deleted on the HMC
        # after the command.
        # Because -n is specified, it does not matter that -c is omitted.
        {},
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'valid',
            '-n': 'valid',
        },
        None,
        None,
        0, None,
        True
    ),
    (
        "Logon data from opts with only -h",
        # If logon opts are used (detected by presence of -h), a userid is
        # required.
        {},
        {
            '-h': 'valid',
        },
        None,
        None,
        1, "Required option not specified: --userid",
        True
    ),
    (
        "Logon data from opts with invalid password",
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
        None,
        None,
        1, "ServerAuthError: HTTP authentication failed with 403,0",
        True
    ),
    (
        "Just session ID env var with valid session",
        # A (valid) session ID is in the env vars, but for creating a Session
        # object, an HMC host is also needed.
        {
            'ZHMC_SESSION_ID': 'valid',
        },
        {},
        None,
        None,
        1, 'No HMC host or session in HMC session file provided',
        True
    ),
    (
        "Logon data from all env vars with valid session",
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
        None,
        None,
        0, None,
        True
    ),
    (
        "Logon data from all env vars with invalid session",
        # The invalid session ID in the env vars is attempted to be used to
        # execute the command, which fails, which causes a session renewal.
        # A new session is created on the HMC using the valid password, and
        # then the command is successfully executed. The session is deleted
        # after the command.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'invalid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {
            '-p': 'valid'
        },
        None,
        None,
        0, None,
        True
    ),
    (
        "Logon data from logon opts preceding env vars",
        # The logon options take precedence and the env vars are ignored,
        # which is verified by specifying an invalid host.
        # The command is executed with a new temporary session created from
        # the logon options.
        {
            'ZHMC_HOST': 'invalid',
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
        None,
        None,
        0, None,
        True
    ),
    (
        "Logon data from logon opts preceding session file",
        # The logon options take precedence and the session file is ignored,
        # which is verified by specifying an invalid host.
        # The command is executed with a new temporary session created from
        # the logon options.
        {},
        {
            '-h': 'valid',
            '-u': 'valid',
            '-p': 'valid',
            '-n': 'valid',
            '-c': 'valid',
        },
        None,
        """
default:
  host: invalid
  userid: valid
  session_id: valid
  ca_verify: valid
  ca_cert_path: valid
  creation_time: "2025-05-06 07:14:58"
""",
        0, None,
        True
    ),
    (
        "Logon data from env vars preceding session file",
        # The env vars take precedence and the session file is ignored,
        # which is verified by specifying an invalid host.
        # The command is executed using the session from the env vars.
        {
            'ZHMC_HOST': 'valid',
            'ZHMC_USERID': 'valid',
            'ZHMC_SESSION_ID': 'valid',
            'ZHMC_NO_VERIFY': 'valid',
            'ZHMC_CA_CERTS': 'valid',
        },
        {},
        None,
        """
default:
  host: invalid
  userid: valid
  session_id: valid
  ca_verify: valid
  ca_cert_path: valid
  creation_time: "2025-05-06 07:14:58"
""",
        0, None,
        True
    ),
]


@pytest.mark.parametrize(
    "desc, envvars, logon_opts, session_name, initial_sf_str, exp_rc, "
    "exp_err, run",
    TESTCASE_SESSION_COMMAND
)
def test_session_command(
        hmc_definition,   # noqa: F811
        desc, envvars, logon_opts, session_name, initial_sf_str, exp_rc,
        exp_err, run):
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Test sessions used with a simple command 'cpc list --names-only'.
    """
    if run is False:
        pytest.skip("Testcase disabled")

    cleanup_session_ids = []
    try:
        env_session_id = prepare_environ(os.environ, envvars, hmc_definition)
        cleanup_session_ids.append(env_session_id)
        logon_args = prepare_logon_args(logon_opts, hmc_definition)
        if session_name:
            logon_args.extend(['-s', session_name])
        else:
            session_name = DEFAULT_SESSION_NAME
        if initial_sf_str is not None:
            initial_sf_str, sf_session_id = prepare_session_content(
                initial_sf_str, hmc_definition)
        else:
            sf_session_id = None

        pdb_ = run == 'pdb'
        log = (run == 'log' or TESTLOG)

        zhmc_args = logon_args + ['cpc', 'list', '--names-only']

        # The code to be tested
        rc, stdout, stderr, _ = run_zhmc_with_session_file(
            zhmc_args, pdb_=pdb_, log=log, initial_sf_str=initial_sf_str)

        if log:
            print("Debug: test case log begin ------------------")
            print(stderr)
            print("Debug: test case log end --------------------")

        assert_session_command(
            rc, stdout, stderr, env_session_id, sf_session_id, hmc_definition,
            exp_rc, exp_err, pdb_)

    finally:
        for session_id in cleanup_session_ids:
            teardown_hmc_session_id(hmc_definition, session_id)
        if run == 'sleep':
            time.sleep(60)
