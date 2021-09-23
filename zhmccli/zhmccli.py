# Copyright 2016-2019 IBM Corp. All Rights Reserved.
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
Main script.
"""

from __future__ import absolute_import, print_function

import os
import sys
import logging
from logging.handlers import SysLogHandler
from logging import StreamHandler, NullHandler
import platform
from requests.packages import urllib3
import click
import click_repl
from prompt_toolkit.history import FileHistory

import zhmcclient
import zhmcclient_mock
from ._helper import CmdContext, GENERAL_OPTIONS_METAVAR, REPL_HISTORY_FILE, \
    REPL_PROMPT, TABLE_FORMATS, LOG_LEVELS, LOG_DESTINATIONS, \
    SYSLOG_FACILITIES, click_exception

urllib3.disable_warnings()


# Default values for some options
DEFAULT_OUTPUT_FORMAT = 'table'
DEFAULT_ERROR_FORMAT = 'msg'
DEFAULT_TIMESTATS = False
DEFAULT_LOG = 'all=warning'
DEFAULT_LOG_DESTINATION = 'stderr'
DEFAULT_SYSLOG_FACILITY = 'user'
DEFAULT_NO_VERIFY = False

CONSOLE_LOGGER_NAME = 'zhmccli.console'

ERROR_FORMATS = ['msg', 'def']

# List of values to try for the 'address' parameter when creating
# a SysLogHandler object.
# Key: Operating system type, as returned by platform.system(). For CygWin,
# the returned value is 'CYGWIN_NT-6.1', which is special-cased to 'CYGWIN_NT'.
# Value: List of values for the 'address' parameter; to be tried in the
# specified order.
SYSLOG_ADDRESSES = {
    'Linux': ['/dev/log', ('localhost', 514)],
    'Darwin': ['/var/run/syslog', ('localhost', 514)],  # OS-X
    'Windows': [('localhost', 514)],
    'CYGWIN_NT': ['/dev/log', ('localhost', 514)],  # Requires syslog-ng pkg
}

# The getattr() is used to work around a Pylint false positive no-member issue
ZHMCCLIENT_VERSION = "zhmcclient, version {v}".format(
    v=getattr(zhmcclient, '__version__', 'unknown'))

# Logger names by log component
LOGGER_NAMES = {
    'all': '',  # root logger
    'api': zhmcclient.API_LOGGER_NAME,
    'hmc': zhmcclient.HMC_LOGGER_NAME,
    'console': CONSOLE_LOGGER_NAME,
}
LOG_COMPONENTS = LOGGER_NAMES.keys()


@click.group(invoke_without_command=True,
             options_metavar=GENERAL_OPTIONS_METAVAR)
@click.option('-h', '--host', type=str, envvar='ZHMC_HOST',
              help="Hostname or IP address of the HMC "
                   "(Default: ZHMC_HOST environment variable).")
@click.option('-u', '--userid', type=str, envvar='ZHMC_USERID',
              help="Username for the HMC "
                   "(Default: ZHMC_USERID environment variable).")
@click.option('-p', '--password', type=str, envvar='ZHMC_PASSWORD',
              help="Password for the HMC "
                   "(Default: ZHMC_PASSWORD environment variable).")
@click.option('-n', '--no-verify', is_flag=True, default=None,
              envvar='ZHMC_NO_VERIFY',
              help="Do not verify the HMC certificate. "
                   "(Default: ZHMC_NO_VERIFY environment variable, or verify "
                   "the HMC certificate).")
@click.option('-c', '--ca-certs', type=str, envvar='ZHMC_CA_CERTS',
              help="Path name of certificate file or directory with CA "
                   "certificates to be used for verifying the HMC certificate. "
                   "(Default: Path name in ZHMC_CA_CERTS environment variable, "
                   "or path name in REQUESTS_CA_BUNDLE environment variable, "
                   "or path name in CURL_CA_BUNDLE environment variable, "
                   "or the 'certifi' Python package which provides the "
                   "Mozilla CA Certificate List).")
@click.option('-o', '--output-format',
              type=click.Choice(TABLE_FORMATS + ['json']),
              help='Output format (Default: {def_of}).'.
              format(def_of=DEFAULT_OUTPUT_FORMAT))
@click.option('-x', '--transpose', type=str, is_flag=True,
              help='Transpose the output table for metrics.')
@click.option('-e', '--error-format', type=click.Choice(ERROR_FORMATS),
              help='Error message format (Default: {def_ef}).'.
              format(def_ef=DEFAULT_ERROR_FORMAT))
@click.option('-t', '--timestats', type=str, is_flag=True,
              help='Show time statistics of HMC operations.')
@click.option('--log', type=str, metavar='COMP=LEVEL,...',
              help="Set a component to a log level (COMP: [{comps}], "
              "LEVEL: [{levels}], Default: {def_log}).".
              format(comps='|'.join(LOG_COMPONENTS),
                     levels='|'.join(LOG_LEVELS),
                     def_log=DEFAULT_LOG))
@click.option('--log-dest', type=click.Choice(LOG_DESTINATIONS),
              help="Log destination for this command (Default: {def_dest}).".
              format(def_dest=DEFAULT_LOG_DESTINATION))
@click.option('--syslog-facility', type=click.Choice(SYSLOG_FACILITIES),
              help="Syslog facility when logging to the syslog "
              "(Default: {def_slf}).".
              format(def_slf=DEFAULT_SYSLOG_FACILITY))
@click.version_option(
    message='%(prog)s, version %(version)s\n' + ZHMCCLIENT_VERSION,
    help="Show the versions of this command and of the zhmcclient package and "
    "exit.")
@click.pass_context
def cli(ctx, host, userid, password, no_verify, ca_certs, output_format,
        transpose, error_format, timestats, log, log_dest, syslog_facility):
    """
    Command line interface for the IBM Z HMC.

    The options shown in this help text are general options that can also
    be specified on any of the (sub-)commands.
    """

    # Concept: In interactive mode, the global options specified in the command
    # line are used as defaults for the commands that are issued interactively.
    # The interactive commands may override these options.
    # This requires being able to determine for each option whether it has been
    # specified. This is the reason the options don't define defaults in the
    # decorators that define them.

    if ctx.obj is None:
        # We are in command mode or are processing the command line options in
        # interactive mode.
        # We apply the documented option defaults.
        if output_format is None:
            output_format = DEFAULT_OUTPUT_FORMAT
        if transpose is None:
            transpose = False
        if error_format is None:
            error_format = DEFAULT_ERROR_FORMAT
        if timestats is None:
            timestats = DEFAULT_TIMESTATS
        if no_verify is None:
            no_verify = DEFAULT_NO_VERIFY
    else:
        # We are processing an interactive command.
        # We apply the option defaults from the command line options.
        if host is None:
            host = ctx.obj.host
        if userid is None:
            userid = ctx.obj.userid
        if password is None:
            # pylint: disable=protected-access
            password = ctx.obj._password
        if no_verify is None:
            no_verify = ctx.obj.no_verify
        if ca_certs is None:
            ca_certs = ctx.obj.ca_certs
        if output_format is None:
            output_format = ctx.obj.output_format
        if transpose is None:
            transpose = ctx.obj.transpose
        if error_format is None:
            error_format = ctx.obj.error_format
        if timestats is None:
            timestats = ctx.obj.timestats

    if transpose and output_format == 'json':
        raise click_exception(
            "Transposing output tables (-x / --transpose) conflicts with "
            "non-table output format (-o / --output-format): {of}".
            format(of=output_format),
            error_format)

    if no_verify and ca_certs:
        raise click_exception(
            "Disabling HMC certificate verification (-n / --no-verify / "
            "ZHMC_NO_VERIFY) conflicts with specifying a CA certificate path "
            "(-c / --ca-certs / ZHMC_CA_CERTS)",
            error_format)

    # TODO: Add context support for the following options:
    if log is None:
        log = DEFAULT_LOG
    if log_dest is None:
        log_dest = DEFAULT_LOG_DESTINATION
    if syslog_facility is None:
        syslog_facility = DEFAULT_SYSLOG_FACILITY

    # Now we have the effective values for the options as they should be used
    # by the current command, regardless of the mode.

    # Set up logging

    for lc in LOG_COMPONENTS:
        reset_logger(lc)

    if log_dest == 'syslog':
        # The choices in SYSLOG_FACILITIES have been validated by click
        # so we don't need to further check them.
        facility = SysLogHandler.facility_names[syslog_facility]
        system = platform.system()
        if system.startswith('CYGWIN_NT'):
            # Value is 'CYGWIN_NT-6.1'; strip off trailing version:
            system = 'CYGWIN_NT'
        try:
            addresses = SYSLOG_ADDRESSES[system]
        except KeyError:
            raise NotImplementedError(
                "Logging to syslog is not supported on this platform: {p}".
                format(p=system))
        assert isinstance(addresses, list)
        for address in addresses:
            try:
                handler = SysLogHandler(address=address, facility=facility)
            except Exception:  # pylint: disable=broad-except
                continue
            break
        else:
            exc = sys.exc_info()[1]
            exc_name = exc.__class__.__name__ if exc else None
            raise RuntimeError(
                "Creating SysLogHandler with addresses {al!r} failed. "
                "Failure on last address {a!r} was: {exc}: {msg}".
                format(al=addresses, a=address, exc=exc_name, msg=exc))
        fs = '%(levelname)s %(name)s: %(message)s'
        handler.setFormatter(logging.Formatter(fs))
    elif log_dest == 'stderr':
        handler = StreamHandler(stream=sys.stderr)
        fs = '%(levelname)s %(name)s: %(message)s'
        handler.setFormatter(logging.Formatter(fs))
    else:
        # The choices in LOG_DESTINATIONS have been validated by click
        assert log_dest == 'none'
        handler = None

    log_specs = log.split(',')
    for log_spec in log_specs:

        # ignore extra ',' at begin, end or in between
        if log_spec == '':
            continue

        try:
            log_comp, log_level = log_spec.split('=', 1)
        except ValueError:
            raise click_exception("Missing '=' in COMP=LEVEL specification in "
                                  "--log option: {ls}".format(ls=log_spec),
                                  error_format)

        level = getattr(logging, log_level.upper(), None)
        if level is None:
            raise click_exception("Invalid log level in COMP=LEVEL "
                                  "specification in --log option: {ls}".
                                  format(ls=log_spec),
                                  error_format)

        if log_comp not in LOG_COMPONENTS:
            raise click_exception("Invalid log component in COMP=LEVEL "
                                  "specification in --log option: {ls}".
                                  format(ls=log_spec), error_format)

        if handler:
            setup_logger(log_comp, handler, level)

    session_id = os.environ.get('ZHMC_SESSION_ID', None)
    if session_id and session_id.startswith('faked_session:'):
        # This should be used by the zhmc function tests only.
        # A SyntaxError raised by an incorrect expression is considered
        # an internal error in the function tests and is therefore not
        # handled.
        expr = session_id.split(':', 1)[1]
        faked_session = eval(expr)  # pylint: disable=eval-used
        assert isinstance(faked_session, zhmcclient_mock.FakedSession)
        session_id = faked_session

    def get_password_via_prompt(host, userid):
        """
        Password retrieval function that prompts for the password.

        It follows the interface defined in
        :func:`~zhmcclient.get_password_interface` and needs access to the
        click context (ctx).
        """
        if userid is not None and host is not None:
            ctx.obj.spinner.stop()
            password = click.prompt(
                "Enter password (for user {userid} at HMC {host})".
                format(userid=userid, host=host), hide_input=True,
                confirmation_prompt=False, type=str, err=True)
            ctx.obj.spinner.start()
            return password

        raise click_exception("{cmd} command requires logon, but no "
                              "session-id or userid provided.".
                              format(cmd=ctx.invoked_subcommand),
                              error_format)

    # We create a command context for each command: An interactive command has
    # its own command context different from the command context for the
    # command line.
    ctx.obj = CmdContext(host, userid, password, no_verify, ca_certs,
                         output_format, transpose, error_format, timestats,
                         session_id, get_password_via_prompt)

    # Invoke default command
    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


def reset_logger(log_comp):
    """
    Reset the logger for the specified log component to have exactly one
    NullHandler.
    """

    name = LOGGER_NAMES[log_comp]
    logger = logging.getLogger(name)

    has_nh = False
    for h in logger.handlers:
        if not has_nh and isinstance(h, NullHandler):
            has_nh = True
            continue
        logger.removeHandler(h)

    if not has_nh:
        nh = NullHandler()
        logger.addHandler(nh)


def setup_logger(log_comp, handler, level):
    """
    Setup the logger for the specified log component to add the specified
    handler and to set it to the specified log level.
    """

    name = LOGGER_NAMES[log_comp]
    logger = logging.getLogger(name)

    logger.addHandler(handler)
    logger.setLevel(level)


@cli.command('help')
@click.pass_context
def repl_help(ctx):
    # pylint: disable=unused-argument
    """
    Show help message for interactive mode.

    Parameters:

      ctx (:class:`click.Context`): The click context object. Created by the
        ``@click.pass_context`` decorator.
    """
    print("""
The following can be entered in interactive mode:

  <zhmc-cmd>                  Execute zhmc command <zhmc-cmd>.
  !<shell-cmd>                Execute shell command <shell-cmd>.

  <CTRL-D>, :q, :quit, :exit  Exit interactive mode.

  <TAB>                       Tab completion (can be used anywhere).
  --help                      Show zhmc general help message, including a list
                              of zhmc commands.
  <zhmc-cmd> --help           Show help message for zhmc command <zhmc-cmd>.
  help                        Show this help message.
  :?, :h, :help               Show (incomplete) help message about interactive
                              mode.
""")


@cli.command('repl')
@click.pass_context
def repl(ctx):
    """
    Enter interactive (REPL) mode (default).

    Parameters:

      ctx (:class:`click.Context`): The click context object. Created by the
        ``@click.pass_context`` decorator.
    """

    history_file = REPL_HISTORY_FILE
    if history_file.startswith('~'):
        history_file = os.path.expanduser(history_file)

    print("Enter 'help' for help, <CTRL-D> or ':q' to exit.")

    prompt_kwargs = {
        'message': REPL_PROMPT,
        'history': FileHistory(history_file),
    }
    click_repl.repl(ctx, prompt_kwargs=prompt_kwargs)


# TODO: Apparently registering is not needed, clarify that.
# click_repl.register_repl(repl)
