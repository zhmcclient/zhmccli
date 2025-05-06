# Copyright 2016,2019 IBM Corp. All Rights Reserved.
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
Commands for HMC sessions.
"""


import click

import zhmcclient
from .zhmccli import cli
from ._helper import click_exception, print_dicts, forbidden_option, \
    LogonSource
from ._session_file import HMCSession, HMCSessionFile, HMCSessionNotFound, \
    HMCSessionAlreadyExists, DEFAULT_SESSION_NAME, BLANKED_OUT_STRING


@cli.group('session')
def session_group():
    """
    Command group for managing permanent HMC sessions.

    zhmc commands can by used with a temporary HMC session that is created
    and deleted for each command execution, or with a permanent HMC session
    that exists across zhmc commands.

    A permanent HMC session can be created in two ways:

    \b
    * Using 'zhmc session logon'. This persists the session data in an HMC
      session file. The HMC session file is located in the user's home
      directory and has file permissions that allow access only for the user.
      It contains the session ID, but not the password.
    * Deprecated: Using 'zhmc session create'. This displays commands for
      setting ZHMC_* environment variables that persist the session data.
      These environment variables contain the session ID, but not the password.
      This command is deprecated, use 'zhmc session logon' instead.

    There are three ways how session data can be provided to any zhmc command.
    In order of decreasing priority, they are:

    \b
    * Command line options. This creates a session and is used if '--host' is
      specified.
    * Environment variables. This uses the permanent session defined in the
      ZHMC_* environment variables and is used if the ZHMC_HOST environment
      variable is set.
    * HMC session file. This uses a permanent session defined in the HMC
      session file and is used if none of the above is used.

    The HMC session file can store multiple sessions that are selected using
    the `-s` / `--session-name` option. If that option is not specified, a
    default session named 'default' is used.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified before the
    command.
    """


@session_group.command('logon')
@click.pass_obj
def session_logon(cmd_ctx):
    """
    Log on to the HMC and store the resulting session data in the HMC session
    file for use by subsequent commands.

    The logon is performed unconditionally, regardless of an existing valid
    session in the HMC session file or ZHMC_* environment variables.
    An existing valid session in the HMC session file or ZHMC_* environment
    variables is not logged off before logging on.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified before the
    command.
    """
    cmd_ctx.execute_cmd(lambda: cmd_session_logon(cmd_ctx), logoff=False)


@session_group.command('logoff')
@click.pass_obj
def session_logoff(cmd_ctx):
    """
    Log off from the HMC session defined in the HMC session file and delete
    its session data from the HMC session file.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified before the
    command.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_session_logoff(cmd_ctx), accept_no_session=True)


@session_group.command('create')
@click.pass_obj
def session_create(cmd_ctx):
    """
    Deprecated: Log on to the HMC and display commands to set environment
    variables for use by subsequent commands.

    The logon is performed unconditionally, regardless of an existing valid
    session in the HMC session file or ZHMC_* environment variables.
    An existing valid session in the HMC session file or ZHMC_* environment
    variables is not logged off before logging on.

    This can be used for example with the 'eval' function of the bash shell
    as follows, to immediately set the resulting environment variables:

        eval $(zhmc ... session create)

    This command is deprecated. Use 'zhmc session logon' instead.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified before the
    command.
    """
    cmd_ctx.execute_cmd(lambda: cmd_session_create(cmd_ctx), logoff=False)


@session_group.command('delete')
@click.pass_obj
def session_delete(cmd_ctx):
    """
    Deprecated: Log off from the HMC session defined in the ZHMC_*
    environment variables and display commands to unset these environment
    variables.

    This can be used for example with the 'eval' function of the bash shell
    as follows, to immediately unset the environment variables:

        eval $(zhmc session delete)

    This command is deprecated. Use 'zhmc session logoff' instead.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified before the
    command.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_session_delete(cmd_ctx), accept_no_session=True)


@session_group.command('list')
@click.pass_obj
def session_list(cmd_ctx):
    """
    List the sessions in the HMC session file.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified before the
    command.
    """
    cmd_ctx.execute_cmd(lambda: cmd_session_list(cmd_ctx), setup_session=False)


def cmd_session_logon(cmd_ctx):
    """Log on to the HMC, storing session data in session file."""
    session = cmd_ctx.session  # zhmcclient.Session
    try:
        session.logon(always=True)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    session_file = HMCSessionFile()
    session_name = cmd_ctx.session_name or DEFAULT_SESSION_NAME
    hmc_session = HMCSession.from_zhmcclient_session(session)
    try:
        session_file.add(session_name, hmc_session)
    except HMCSessionAlreadyExists:
        session_file.update(session_name, hmc_session.as_dict())

    cmd_ctx.spinner.stop()
    print(f"Logged on to HMC session {session_name}")


def cmd_session_logoff(cmd_ctx):
    """Log off from the HMC session defined in session file."""

    if cmd_ctx.logon_source not in (LogonSource.SESSION_FILE, LogonSource.NONE):
        raise click_exception(
            "Invalid logon source for the 'session logoff' command: "
            f"{cmd_ctx.logon_source}",
            cmd_ctx.error_format)

    session = cmd_ctx.session  # zhmcclient.Session
    if session is not None:
        try:
            session.logoff()  # ignores invalid session ID
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)

    session_file = HMCSessionFile()
    session_name = cmd_ctx.session_name
    try:
        session_file.remove(session_name)
    except HMCSessionNotFound as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    print(f"Logged off from HMC session {session_name}")


def cmd_session_create(cmd_ctx):
    """Log on to the HMC, storing session data in environment variables."""
    session = cmd_ctx.session  # zhmcclient.Session
    assert isinstance(session, zhmcclient.Session)
    try:
        session.logon(always=True)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    if session.verify_cert is False:
        no_verify = 'TRUE'
        ca_certs = None
    elif session.verify_cert is True:
        no_verify = None
        ca_certs = None
    else:
        no_verify = None
        ca_certs = session.verify_cert

    cmd_ctx.spinner.stop()
    click.echo(f"export ZHMC_HOST={session.host}")
    click.echo(f"export ZHMC_USERID={session.userid}")
    click.echo(f"export ZHMC_SESSION_ID={session.session_id}")
    if no_verify is None:
        click.echo("unset ZHMC_NO_VERIFY")
    else:
        click.echo(f"export ZHMC_NO_VERIFY={no_verify}")
    if ca_certs is None:
        click.echo("unset ZHMC_CA_CERTS")
    else:
        click.echo(f"export ZHMC_CA_CERTS={ca_certs}")


def cmd_session_delete(cmd_ctx):
    """Log off from the HMC session defined in environment variables."""

    if cmd_ctx.logon_source not in (LogonSource.ENVIRONMENT, LogonSource.NONE):
        raise click_exception(
            "Invalid logon source for the 'session delete' command: "
            f"{cmd_ctx.logon_source}",
            cmd_ctx.error_format)

    session = cmd_ctx.session  # zhmcclient.Session
    if session is not None:
        try:
            session.logoff()  # ignores invalid session ID
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("unset ZHMC_HOST")
    click.echo("unset ZHMC_USERID")
    click.echo("unset ZHMC_SESSION_ID")
    click.echo("unset ZHMC_NO_VERIFY")
    click.echo("unset ZHMC_CA_CERTS")


def cmd_session_list(cmd_ctx):
    """List the sessions in the HMC session file."""
    reason = ("this command does not log on to the HMC")
    forbidden_option(cmd_ctx.params['host'], '--host', reason)
    forbidden_option(cmd_ctx.params['userid'], '--userid', reason)
    forbidden_option(cmd_ctx.params['no_verify'], '--no-verify', reason)
    forbidden_option(cmd_ctx.params['ca_certs'], '--ca-certs', reason)

    session_file = HMCSessionFile()
    hmc_sessions = session_file.list()
    _session_list = []
    for session_name, session in hmc_sessions.items():
        session_props = {}
        session_props['session_name'] = session_name
        session_props.update(session.as_dict())
        if session_props['session_id']:
            session_props['session_id'] = BLANKED_OUT_STRING
        _session_list.append(session_props)

    cmd_ctx.spinner.stop()
    show_list = [
        'session_name', 'host', 'userid', 'ca_verify', 'ca_cert_path',
        'session_id', 'creation_time'
    ]

    print_dicts(cmd_ctx, _session_list, cmd_ctx.output_format,
                show_list=show_list)
