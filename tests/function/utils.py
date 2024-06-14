# Copyright 2017,2019 IBM Corp. All Rights Reserved.
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
Unit tests for 'zhmccli info' command.
"""


import sys
import os
import re
import tempfile
from subprocess import Popen, PIPE
from copy import copy

import zhmcclient_mock
from zhmccli.zhmccli import cli


def call_zhmc_child(args, env=None):
    """
    Invoke the 'zhmc' command as a child process.

    This requires that the 'zhmc' command is installed in the current Python
    environment.

    Parameters:

      args (iterable of :term:`string`): Command line arguments, without the
        command name.
        Each single argument must be its own item in the iterable; combining
        the arguments into a string that is provided as a single argument is
        not allowed.
        The arguments may be binary strings encoded in UTF-8, or unicode
        strings.

      env (dict): Environment variables to be put into the environment when
        calling the command. May be `None`. Dict key is the variable name as a
        :term:`string`; dict value is the variable value as a :term:`string`
        (without any shell escaping needed).

    Returns:

      tuple(rc, stdout, stderr): Output of the command, where:

        * rc(int): Exit code of the command.
        * stdout(:term:`unicode string`): Standard output of the command,
          as a unicode string with newlines represented as '\\n'.
          An empty string, if there was no data.
        * stderr(:term:`unicode string`): Standard error of the command,
          as a unicode string with newlines represented as '\\n'.
          An empty string, if there was no data.
    """

    cli_cmd = 'zhmc'

    if env is None:
        env = {}
    else:
        env = copy(env)

    # Unset the zhmc-specific env vars if not provided:
    if 'ZHMC_HOST' not in env:
        env['ZHMC_HOST'] = None
    if 'ZHMC_USERID' not in env:
        env['ZHMC_USERID'] = None
    if 'ZHMC_SESSION_ID' not in env:
        env['ZHMC_SESSION_ID'] = None

    env['PYTHONPATH'] = '.'  # Use local files
    env['PYTHONWARNINGS'] = ''  # Disable for parsing output

    # Put the env vars into the environment of the current Python process,
    # from where they will be inherited into its child processes (-> shell ->
    # cli command).
    for name in env:
        value = env[name]
        if value is None:
            if name in os.environ:
                del os.environ[name]
        else:
            os.environ[name] = value

    assert isinstance(args, (list, tuple))
    cmd_args = [cli_cmd]
    for arg in args:
        if isinstance(arg, bytes):
            arg = arg.decode('utf-8')
        cmd_args.append(arg)

    # Note that the click package on Windows writes '\n' at the Python level
    # as '\r\n' at the level of the shell. Some other layer (presumably the
    # Windows shell) contriubutes another such translation, so we end up with
    # '\r\r\n' for each '\n'. Using universal_newlines=True undoes all of that.

    # pylint: disable=consider-using-with
    proc = Popen(cmd_args, shell=False, stdout=PIPE, stderr=PIPE,
                 universal_newlines=True)
    stdout_str, stderr_str = proc.communicate()
    rc = proc.returncode

    if isinstance(stdout_str, bytes):
        stdout_str = stdout_str.decode('utf-8')
    if isinstance(stderr_str, bytes):
        stderr_str = stderr_str.decode('utf-8')

    return rc, stdout_str, stderr_str


def call_zhmc_inline(args, env=None, faked_session=None):
    """
    Invoke the Python code of the 'zhmc' command in the current Python process.

    This does not require that the 'zhmc' command is installed in the current
    Python environment.

    Parameters:

      args (iterable of :term:`string`): Command line arguments, without the
        command name.
        Each single argument must be its own item in the iterable; combining
        the arguments into a string that is provided as a single argument is
        not allowed.
        The arguments may be binary strings encoded in UTF-8, or unicode
        strings.

      env (dict): Environment variables to be put into the environment when
        calling the command. May be `None`. Dict key is the variable name as a
        :term:`string`; dict value is the variable value as a :term:`string`,
        (without any shell escaping needed).

      faked_session (zhmcclient_mock.FakedSession): Faked session to be used,
        or `None` to not use a faked session. If a faked session is provided,
        that will cause a 'ZHMC_SESSION_ID' environment variable that may
        have been provided in the 'env' parameter, to be overridden.

    Returns:

      tuple(rc, stdout, stderr): Output of the command, where:

        * rc(int): Exit code of the command.
        * stdout(:term:`unicode string`): Standard output of the command,
          as a unicode string with newlines represented as '\\n'.
          An empty string, if there was no data.
        * stderr(:term:`unicode string`): Standard error of the command,
          as a unicode string with newlines represented as '\\n'.
          An empty string, if there was no data.
    """

    cli_cmd = 'zhmc'

    if env is None:
        env = {}
    else:
        env = copy(env)

    # Unset the zhmc-specific env vars if not provided
    if 'ZHMC_HOST' not in env:
        env['ZHMC_HOST'] = None
    if 'ZHMC_USERID' not in env:
        env['ZHMC_USERID'] = None
    if faked_session:
        # Communicate the faked session object to the zhmc CLI code.
        # It is accessed in CmdContext.execute_cmd().
        # The syntax of the session ID string is 'faked_session:' followed by
        # the expression to access the object.
        zhmcclient_mock.zhmccli_faked_session = faked_session
        session_id = 'faked_session:{s}'.format(
            s='zhmcclient_mock.zhmccli_faked_session')
        env['ZHMC_SESSION_ID'] = session_id
    else:
        if 'ZHMC_SESSION_ID' not in env:
            env['ZHMC_SESSION_ID'] = None

    env['PYTHONPATH'] = '.'  # Use local files
    env['PYTHONWARNINGS'] = ''  # Disable for parsing output

    # Put the env vars into the environment of the current Python process.
    # The cli command code will be run in the current Python process.
    for name in env:
        value = env[name]
        if value is None:
            if name in os.environ:
                del os.environ[name]
        else:
            os.environ[name] = value

    assert isinstance(args, (list, tuple))
    sys.argv = [cli_cmd]
    for arg in args:
        if isinstance(arg, bytes):
            arg = arg.decode('utf-8')
        sys.argv.append(arg)

    # In Python 3.6, the string type must match the file mode
    # (bytes/binary and str/text). sys.std* is open in text mode,
    # so we need to open the temp file also in text mode.
    with tempfile.TemporaryFile(mode='w+t') as tmp_stdout:
        saved_stdout = sys.stdout
        sys.stdout = tmp_stdout

        with tempfile.TemporaryFile(mode='w+t') as tmp_stderr:
            saved_stderr = sys.stderr
            sys.stderr = tmp_stderr

            exit_rcs = []  # Mutable object for storing sys.exit() rcs.

            def local_exit(rc):
                exit_rcs.append(rc)

            saved_exit = sys.exit
            sys.exit = local_exit

            # The arguments are passed via env vars.
            # pylint: disable=no-value-for-parameter
            cli_rc = cli()

            if len(exit_rcs) > 0:
                # The click command function called sys.exit(). This should
                # always be the case for zhmccli.

                # When --help is specified, click invokes the specified
                # subcommand without args when run in py.test (for whatever
                # reason...). As a consequence, sys.exit() is called an extra
                # time. We use the rc passed into the first invocation.
                rc = exit_rcs[0]
            else:
                # The click command function returned and did not call
                # sys.exit(). That can be done with click, but should not be
                # the case with zhmccli. We still handle that, just in case.
                rc = cli_rc

            sys.exit = saved_exit

            sys.stderr = saved_stderr
            tmp_stderr.flush()
            tmp_stderr.seek(0)
            stderr_str = tmp_stderr.read()

        sys.stdout = saved_stdout
        tmp_stdout.flush()
        tmp_stdout.seek(0)
        stdout_str = tmp_stdout.read()

    if isinstance(stdout_str, bytes):
        stdout_str = stdout_str.decode('utf-8')
    if isinstance(stderr_str, bytes):
        stderr_str = stderr_str.decode('utf-8')

    # Note that the click package on Windows writes '\n' at the Python level
    # as '\r\n' at the level of the shell, so we need to undo that.
    stdout_str = stdout_str.replace('\r\n', '\n')
    stderr_str = stderr_str.replace('\r\n', '\n')

    return rc, stdout_str, stderr_str


def assert_rc(exp_rc, rc, stdout, stderr):
    """
    Assert that the specified return code is as expected.

    The actual return code is compared with the expected return code,
    and if they don't match, stdout and stderr are displayed as a means
    to help debugging the issue.

    Parameters:

      exp_rc (int): expected return code.

      rc (int): actual return code.

      stdout (string): stdout of the command, for debugging purposes.

      stderr (string): stderr of the command, for debugging purposes.
    """

    assert exp_rc == rc, \
        "Unexpected exit code (expected {e}, got {g})\n" \
        "  stdout:\n" \
        "{so}\n" \
        "  stderr:\n" \
        "{se}". \
        format(e=exp_rc, g=rc, so=stdout, se=stderr)


def assert_patterns(exp_patterns, lines, meaning):
    """
    Assert that the specified lines match the specified patterns.

    The patterns are matched against the complete line from begin to end,
    even if no begin and end markers are specified in the patterns.

    Parameters:

      exp_patterns (iterable of string): regexp patterns defining the expected
        value for each line. Item values of None will be skipped / ignored.

      lines (iterable of string): the lines to be matched.

      meaning (string): A short descriptive text that identifies the meaning
        of the lines that are matched, e.g. 'stderr'.
    """
    exp_patterns = [ep for ep in exp_patterns if ep is not None]
    assert len(lines) == len(exp_patterns), \
        "Unexpected number of lines in {m}:\n" \
        "  expected patterns:\n" \
        "{e}\n" \
        "  actual lines:\n" \
        "{a}\n". \
        format(m=meaning,
               e='\n'.join(exp_patterns),
               a='\n'.join(lines))

    for i, line in enumerate(lines):
        pattern = exp_patterns[i]
        if not pattern.endswith('$'):
            pattern += '$'
        assert re.match(pattern, line), \
            "Unexpected line {n} in {m}:\n" \
            "  expected pattern:\n" \
            "{e}\n" \
            "  actual line:\n" \
            "{a}\n". \
            format(n=i, m=meaning, e=pattern, a=line)
