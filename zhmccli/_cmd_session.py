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
Commands for HMC sessions.
"""

from __future__ import absolute_import

import click

import zhmcclient
from .zhmccli import cli
from ._helper import click_exception


@cli.group('session')
def session_group():
    """
    Command group for managing sessions.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified before the
    command.
    """


@session_group.command('create')
@click.pass_obj
def session_create(cmd_ctx):
    """
    Create an HMC session.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified before the
    command.
    """
    cmd_ctx.execute_cmd(lambda: cmd_session_create(cmd_ctx))


@session_group.command('delete')
@click.pass_obj
def session_delete(cmd_ctx):
    """
    Delete the current HMC session.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified before the
    command.
    """
    cmd_ctx.execute_cmd(lambda: cmd_session_delete(cmd_ctx))


def cmd_session_create(cmd_ctx):
    """Create an HMC session."""
    session = cmd_ctx.session
    try:
        # We need to first log off, to make the logon really create a new
        # session. If we don't first log off, the session from the
        # ZHMC_SESSION_ID env var will be used and no new session be created.
        session.logoff(verify=True)
        session.logon(verify=True)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()

    if session.verify_cert is False:
        no_verify = 'TRUE'
        ca_certs = None
    elif session.verify_cert is True:
        no_verify = None
        ca_certs = None
    else:
        no_verify = None
        ca_certs = session.verify_cert

    click.echo("export ZHMC_HOST={h}".format(h=session.host))
    click.echo("export ZHMC_USERID={u}".format(u=session.userid))
    click.echo("export ZHMC_SESSION_ID={s}".format(s=session.session_id))
    if no_verify is None:
        click.echo("unset ZHMC_NO_VERIFY")
    else:
        click.echo("export ZHMC_NO_VERIFY={nv}".format(nv=no_verify))
    if ca_certs is None:
        click.echo("unset ZHMC_CA_CERTS")
    else:
        click.echo("export ZHMC_CA_CERTS={cc}".format(cc=ca_certs))


def cmd_session_delete(cmd_ctx):
    """Delete the current HMC session."""
    session = cmd_ctx.session
    try:
        session.logoff()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("unset ZHMC_SESSION_ID")
