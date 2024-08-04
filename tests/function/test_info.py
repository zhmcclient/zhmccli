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
Function tests for 'zhmc info' command, including tests for global options
that can be tested only with a subcommand.
"""


import os
import subprocess
import json
import pytest
import click
import urllib3

from zhmcclient_mock import FakedSession

from .utils import call_zhmc_child, call_zhmc_inline, assert_rc, \
    assert_patterns

CLICK_VERSION = [int(v) for v in click.__version__.split('.')]
URLLIB3_VERSION = [int(v) for v in urllib3.__version__.split('.')]

if URLLIB3_VERSION < [2, 0]:
    INVALID_HOST_MSG = "Failed to establish a new connection:"
else:
    INVALID_HOST_MSG = "Failed to resolve"

TEST_LOGFILE = 'tmp_testfile.log'


class TestInfo:
    """
    All tests for the 'zhmc info' command, including tests for global options
    that can be tested only with a subcommand.
    """

    def test_info_help(self):
        # pylint: disable=no-self-use
        """Test 'zhmc info --help'"""

        # Invoke the command to be tested
        rc, stdout, stderr = call_zhmc_child(['info', '--help'])

        assert_rc(0, rc, stdout, stderr)
        assert stdout.startswith(
            "Usage: zhmc info [OPTIONS]\n"), \
            f"stdout={stdout!r}"
        assert stderr == ""

    def test_info_error_no_host(self):
        # pylint: disable=no-self-use
        """Test 'zhmc info' when no host is provided"""

        # Invoke the command to be tested
        rc, stdout, stderr = call_zhmc_child(['info'])

        assert_rc(1, rc, stdout, stderr)
        assert stdout == ""
        assert stderr.startswith(
            "Error: No HMC host provided\n"), \
            f"stderr={stderr!r}"

    def test_info_error_no_conn(self):
        # pylint: disable=no-self-use
        """Test zhmc info when host is specified but no connection to host"""

        # Invoke the command to be tested
        rc, stdout, stderr = call_zhmc_child(
            ['info'],
            {'ZHMC_HOST': 'invalid_host'}
        )

        assert_rc(1, rc, stdout, stderr)
        assert stdout == ""
        assert stderr.startswith(
            "Error: ConnectionError: "), \
            f"stderr={stderr!r}"

    @pytest.mark.parametrize(
        # Transpose only affects metrics output, but not info output.
        # Transpose is accepted and ignored for all table output formats.
        "transpose_opt", [
            None,
            '-x',
            '--transpose',
        ]
    )
    @pytest.mark.parametrize(
        "out_format, exp_stdout_template", [
            ('table',
             # Order of properties must match:
             '+-------------------+----------+\n'
             '| Field Name        | Value    |\n'
             '|-------------------+----------|\n'
             '| api-major-version | {v[amaj]:<8} |\n'
             '| api-minor-version | {v[amin]:<8} |\n'
             '| hmc-name          | {v[hnam]:8} |\n'
             '| hmc-version       | {v[hver]:8} |\n'
             '+-------------------+----------+\n'),
            ('plain',
             # Order of properties must match:
             'Field Name         Value\n'
             'api-major-version  {v[amaj]}\n'
             'api-minor-version  {v[amin]}\n'
             'hmc-name           {v[hnam]}\n'
             'hmc-version        {v[hver]}\n'),
            ('simple',
             # Order of properties must match:
             'Field Name         Value\n'
             '-----------------  --------\n'
             'api-major-version  {v[amaj]}\n'
             'api-minor-version  {v[amin]}\n'
             'hmc-name           {v[hnam]}\n'
             'hmc-version        {v[hver]}\n'),
            ('psql',
             # Order of properties must match:
             '+-------------------+----------+\n'
             '| Field Name        | Value    |\n'
             '|-------------------+----------|\n'
             '| api-major-version | {v[amaj]:<8} |\n'
             '| api-minor-version | {v[amin]:<8} |\n'
             '| hmc-name          | {v[hnam]:8} |\n'
             '| hmc-version       | {v[hver]:8} |\n'
             '+-------------------+----------+\n'),
            ('rst',
             # Order of properties must match:
             '=================  ========\n'
             'Field Name         Value\n'
             '=================  ========\n'
             'api-major-version  {v[amaj]}\n'
             'api-minor-version  {v[amin]}\n'
             'hmc-name           {v[hnam]}\n'
             'hmc-version        {v[hver]}\n'
             '=================  ========\n'),
            ('mediawiki',
             # Order of properties must match:
             '{{| class="wikitable" style="text-align: left;"\n'
             '|+ <!-- caption -->\n'
             '|-\n'
             '! Field Name        !! Value\n'
             '|-\n'
             '| api-major-version || {v[amaj]}\n'
             '|-\n'
             '| api-minor-version || {v[amin]}\n'
             '|-\n'
             '| hmc-name          || {v[hnam]}\n'
             '|-\n'
             '| hmc-version       || {v[hver]}\n'
             '|}}\n'),
            ('html',
             # Order of properties must match:
             '<table>\n'
             '<thead>\n'
             '<tr><th>Field Name       </th><th>Value   </th></tr>\n'
             '</thead>\n'
             '<tbody>\n'
             '<tr><td>api-major-version</td><td>{v[amaj]:<8}</td></tr>\n'
             '<tr><td>api-minor-version</td><td>{v[amin]:<8}</td></tr>\n'
             '<tr><td>hmc-name         </td><td>{v[hnam]:8}</td></tr>\n'
             '<tr><td>hmc-version      </td><td>{v[hver]:8}</td></tr>\n'
             '</tbody>\n'
             '</table>\n'),
            ('latex',
             # Order of properties must match:
             '\\begin{{tabular}}{{ll}}\n'
             '\\hline\n'
             ' Field Name        & Value    \\\\\n'
             '\\hline\n'
             ' api-major-version & {v[amaj]:<8} \\\\\n'
             ' api-minor-version & {v[amin]:<8} \\\\\n'
             ' hmc-name          & {v[hnam]:8} \\\\\n'
             ' hmc-version       & {v[hver]:8} \\\\\n'
             '\\hline\n'
             '\\end{{tabular}}\n'),
        ]
    )
    @pytest.mark.parametrize(
        "out_opt", ['-o', '--output-format']
    )
    @pytest.mark.parametrize(
        "hmc_name, hmc_version, api_version", [
            ('hmc-name', '2.14.0', '2.20'),
        ]
    )
    def test_option_outputformat_table(
            self, hmc_name, hmc_version, api_version, out_opt, out_format,
            exp_stdout_template, transpose_opt):
        # pylint: disable=no-self-use
        """
        Test 'zhmc info' with global options (-o, --output-format) and
        (-x, --transpose), for all table formats.
        """

        faked_session = FakedSession(
            'fake-host', hmc_name, hmc_version, api_version)
        api_version_parts = [int(vp) for vp in api_version.split('.')]
        exp_values = {
            'hnam': hmc_name,
            'hver': hmc_version,
            'amaj': api_version_parts[0],
            'amin': api_version_parts[1],
        }
        exp_stdout = exp_stdout_template.format(v=exp_values)

        args = [out_opt, out_format]
        if transpose_opt is not None:
            args.append(transpose_opt)
        args.append('info')

        # Invoke the command to be tested
        rc, stdout, stderr = call_zhmc_inline(
            args, faked_session=faked_session)

        assert_rc(0, rc, stdout, stderr)
        assert stdout == exp_stdout
        assert stderr == ""

    JSON_STDOUT_TEMPLATE = \
        '{{' \
        '"api-major-version": {v[amaj]},' \
        '"api-minor-version": {v[amin]},' \
        '"hmc-name": "{v[hnam]}",' \
        '"hmc-version": "{v[hver]}"' \
        '}}'

    JSON_CONFLICT_PATTERNS = [
        r"Error: Transposing output tables .* conflicts with non-table "
        r"output format .* json",
    ]

    @pytest.mark.parametrize(
        "transpose_opt, exp_rc, exp_stdout_template, exp_stderr_patterns", [
            (None, 0, JSON_STDOUT_TEMPLATE, None),
            ('-x', 1, None, JSON_CONFLICT_PATTERNS),
            ('--transpose', 1, None, JSON_CONFLICT_PATTERNS),
        ]
    )
    @pytest.mark.parametrize(
        "out_opt", ['-o', '--output-format']
    )
    @pytest.mark.parametrize(
        "hmc_name, hmc_version, api_version", [
            ('hmc-name', '2.14.0', '2.20'),
        ]
    )
    def test_option_outputformat_json(
            self, hmc_name, hmc_version, api_version, out_opt, transpose_opt,
            exp_rc, exp_stdout_template, exp_stderr_patterns):
        # pylint: disable=no-self-use
        """
        Test 'zhmc info' with global options (-o, --output-format) and
        (-x, --transpose), for the 'json' output format.
        """

        faked_session = FakedSession(
            'fake-host', hmc_name, hmc_version, api_version)

        args = [out_opt, 'json']
        if transpose_opt is not None:
            args.append(transpose_opt)
        args.append('info')

        # Invoke the command to be tested
        rc, stdout, stderr = call_zhmc_inline(
            args, faked_session=faked_session)

        assert_rc(exp_rc, rc, stdout, stderr)

        if exp_stdout_template:
            api_version_parts = [int(vp) for vp in api_version.split('.')]
            exp_values = {
                'hnam': hmc_name,
                'hver': hmc_version,
                'amaj': api_version_parts[0],
                'amin': api_version_parts[1],
            }
            exp_stdout = exp_stdout_template.format(v=exp_values)
            exp_stdout_dict = json.loads(exp_stdout)
            stdout_dict = json.loads(stdout)
            assert stdout_dict == exp_stdout_dict
        else:
            assert stdout == ""

        if exp_stderr_patterns:
            assert_patterns(exp_stderr_patterns, stderr.splitlines(), 'stderr')
        else:
            assert stderr == ""

    @pytest.mark.parametrize(
        "err_format, exp_stderr_patterns", [
            (None,  # default format: msg
             [r"Error: ConnectionError: .*" + INVALID_HOST_MSG + r".*"]),
            ('msg',
             [r"Error: ConnectionError: .*" + INVALID_HOST_MSG + r".*"]),
            ('def',
             [r"Error: classname='ConnectionError'; message=['\"].*"
              + INVALID_HOST_MSG + r".*['\"];"]),  # noqa: W503
        ]
    )
    @pytest.mark.parametrize(
        "err_opt", ['-e', '--error-format']
    )
    def test_option_errorformat(self, err_opt, err_format, exp_stderr_patterns):
        # pylint: disable=no-self-use
        """Test 'zhmc info' with global option (-e, --error-format)"""

        if err_format is None:
            err_args = []
        else:
            err_args = [err_opt, err_format]

        # Invoke the command to be tested
        rc, stdout, stderr = call_zhmc_child(
            err_args + ['info'],
            {'ZHMC_HOST': 'invalid_host'}
        )

        assert_rc(1, rc, stdout, stderr)
        assert stdout == ""
        assert_patterns(exp_stderr_patterns, stderr.splitlines(), 'stderr')

    LOG_API_DEBUG_PATTERNS = [
        r"DEBUG zhmcclient.api: .* Client.query_api_version\(\), "
        r"args: \(.*\), kwargs: \{.*\}",
        r"DEBUG zhmcclient.api: .* Client.query_api_version\(\), "
        r"result: \{.*\}",
    ]

    @pytest.mark.parametrize(
        "log_value, exp_rc, exp_stderr_patterns", [
            ('api=error', 0, []),
            ('api=warning', 0, []),
            ('api=info', 0, []),
            ('api=debug', 0, LOG_API_DEBUG_PATTERNS),
            ('api=debug,hmc=error', 0, LOG_API_DEBUG_PATTERNS),
            (',api=debug,hmc=error', 0, LOG_API_DEBUG_PATTERNS),
            ('api=debug,,hmc=error', 0, LOG_API_DEBUG_PATTERNS),
            ('api=debug,hmc=error,', 0, LOG_API_DEBUG_PATTERNS),
            (',,api=debug,,', 0, LOG_API_DEBUG_PATTERNS),
            (',,', 0, []),
            ('api:debug', 1, ["Error: Missing '=' .*"]),
            ('api=debugx', 1, ["Error: Invalid log level .*"]),
            ('apix=debug', 1, ["Error: Invalid log component .*"]),
        ]
    )
    @pytest.mark.parametrize(
        "log_opt", ['--log']
    )
    @pytest.mark.parametrize(
        "hmc_name, hmc_version, api_version", [
            ('hmc-name', '2.14.0', '10.2'),
        ]
    )
    def test_option_log(
            self, hmc_name, hmc_version, api_version, log_opt, log_value,
            exp_rc, exp_stderr_patterns):
        # pylint: disable=no-self-use
        """Test 'zhmc info' with global option --log"""

        faked_session = FakedSession(
            'fake-host', hmc_name, hmc_version, api_version)

        # Invoke the command to be tested
        rc, stdout, stderr = call_zhmc_inline(
            [log_opt, log_value, 'info'],
            faked_session=faked_session)

        assert_rc(exp_rc, rc, stdout, stderr)
        assert_patterns(exp_stderr_patterns, stderr.splitlines(), 'stderr')

    @pytest.mark.parametrize(
        "logdest_value, exp_rc, exp_stderr_patterns", [
            (None, 0, LOG_API_DEBUG_PATTERNS),
            ('stderr', 0, LOG_API_DEBUG_PATTERNS),
            ('syslog', 0, []),
            ('none', 0, []),
            (TEST_LOGFILE, 0, []),
        ]
    )
    @pytest.mark.parametrize(
        "logdest_opt", ['--log-dest']
    )
    @pytest.mark.parametrize(
        "hmc_name, hmc_version, api_version", [
            ('fake-hmc', '2.14.0', '10.2'),
        ]
    )
    def test_option_logdest(
            self, hmc_name, hmc_version, api_version, logdest_opt,
            logdest_value, exp_rc, exp_stderr_patterns):
        """Test 'zhmc info' with global option --log-dest (and --log)"""

        faked_session = FakedSession(
            'fake-host', hmc_name, hmc_version, api_version)

        args = ['--log', 'api=debug']
        logger_name = 'zhmcclient.api'  # corresponds to --log option
        if logdest_value is not None:
            args.append(logdest_opt)
            args.append(logdest_value)
        args.append('info')

        try:

            # Remove a possibly existing log file
            if logdest_value == TEST_LOGFILE:
                if os.path.exists(TEST_LOGFILE):
                    os.remove(TEST_LOGFILE)

            # Invoke the command to be tested
            rc, stdout, stderr = call_zhmc_inline(
                args, faked_session=faked_session)

            assert_rc(exp_rc, rc, stdout, stderr)
            assert_patterns(exp_stderr_patterns, stderr.splitlines(), 'stderr')

            # Check system log
            if logdest_value == 'syslog':
                syslog_files = ['/var/log/messages', '/var/log/syslog']
                for syslog_file in syslog_files:
                    if os.path.exists(syslog_file):
                        break
                else:
                    syslog_file = None
                    print("Warning: Cannot check syslog; syslog file not found "
                          "in: {f!r}".format(f=syslog_files))
                syslog_lines = None
                if syslog_file:
                    try:
                        syslog_lines = subprocess.check_output(
                            'sudo tail {f} || tail {f}'.format(f=syslog_file),
                            shell=True)  # nosec: B602
                    except Exception as exc:  # pylint: disable=broad-except
                        print("Warning: Cannot tail syslog file {f}: {msg}".
                              format(f=syslog_file, msg=exc))
                if syslog_lines:
                    syslog_lines = syslog_lines.decode('utf-8').splitlines()
                    logger_lines = []
                    for line in syslog_lines:
                        if logger_name in line:
                            logger_lines.append(line)
                    logger_lines = logger_lines[
                        -len(self.LOG_API_DEBUG_PATTERNS):]
                    exp_patterns = [r'.*' + p
                                    for p in self.LOG_API_DEBUG_PATTERNS]
                    assert_patterns(exp_patterns, logger_lines, 'syslog')

            # Check log file
            if logdest_value == TEST_LOGFILE:
                with open(TEST_LOGFILE, encoding='utf-8') as fp:
                    log_lines = fp.readlines()
                    logger_lines = []
                    for line in log_lines:
                        if logger_name in line:
                            logger_lines.append(line)
                    logger_lines = logger_lines[
                        -len(self.LOG_API_DEBUG_PATTERNS):]
                    exp_patterns = [r'.*' + p
                                    for p in self.LOG_API_DEBUG_PATTERNS]
                    assert_patterns(exp_patterns, logger_lines, 'syslog')

        finally:
            # Clean up a possibly existing log file
            if logdest_value == TEST_LOGFILE:
                if os.path.exists(TEST_LOGFILE):
                    try:
                        os.remove(TEST_LOGFILE)
                    except OSError:
                        # On Windows with Python 3, PermissionError is raised.
                        # TODO: Find out why and resolve this better.
                        pass
