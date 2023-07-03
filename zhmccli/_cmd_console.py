# Copyright 2022 IBM Corp. All Rights Reserved.
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
Commands for the HMC console.
"""

from __future__ import absolute_import

import click
import dateutil.parser

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_dicts, print_list, \
    TABLE_FORMATS, hide_property, COMMAND_OPTIONS_METAVAR, click_exception


@cli.group('console', options_metavar=COMMAND_OPTIONS_METAVAR)
def console_group():
    """
    Command group for the HMC console.

    These commands always target the (one) console of the targeted HMC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@console_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--all', is_flag=True, required=False,
              help='Show all properties. Default: Hide some properties in '
              'table output formats')
@click.pass_obj
def console_show(cmd_ctx, **options):
    """
    Show properties of the console of the targeted HMC.

    \b
    In table output formats, the following properties are hidden by default
    but can be shown by using the --all option:
      - ec-mcl-description
      - network-info

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_console_show(cmd_ctx, options))


@console_group.command('restart', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--force', '-f', is_flag=True, required=False,
              help='Perform the restart regardless of whether users are '
              'logged in to the HMC. Users in this sense are local or remote '
              'GUI users. Disconnected GUI users and users at the WS-API do '
              'not count for this.')
@click.option('--wait', '-w', is_flag=True, required=False,
              help='Wait for the HMC to become available again. Note that '
              'any session IDs have become invalid.')
@click.option('--timeout', '-T', type=int, required=False, default=60,
              help='Timeout (in seconds) when waiting for the HMC to become '
              'available again. Default: 60.')
@click.pass_obj
def console_restart(cmd_ctx, **options):
    """
    Restart the targeted HMC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_console_restart(cmd_ctx, options))


@console_group.command('get-audit-log', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--begin', type=str, required=False,
              help='Begin time for the log, in a format supported by '
              'the python-dateutil package. Default: Earliest available.')
@click.option('--end', type=str, required=False,
              help='End time for the log, in a format supported by '
              'the python-dateutil package. Default: Latest available.')
@click.pass_obj
def get_audit_log(cmd_ctx, **options):
    """
    Get the audit log of the targeted HMC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_get_audit_log(cmd_ctx, options))


@console_group.command('get-security-log',
                       options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--begin', type=str, required=False,
              help='Begin time for the log, in a format supported by '
              'the python-dateutil package. Default: Earliest available.')
@click.option('--end', type=str, required=False,
              help='End time for the log, in a format supported by '
              'the python-dateutil package. Default: Latest available.')
@click.pass_obj
def get_security_log(cmd_ctx, **options):
    """
    Get the security log of the targeted HMC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_get_security_log(cmd_ctx, options))


@console_group.command('list-api-features',
                       options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--name', type=str, metavar='NAME',
              required=False,
              help='A regular expression used to limit returned objects to '
                   'those that have a matching name field.')
@click.pass_obj
def list_api_features(cmd_ctx, **options):
    """
    Lists the Web Services API features available of the console of the
    targeted HMC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_list_api_features(cmd_ctx, options))


def cmd_console_show(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    try:
        console.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(console.properties)

    # Hide some long or deeply nested properties in table output formats.
    if not options['all'] and cmd_ctx.output_format in TABLE_FORMATS:
        hide_property(properties, 'ec-mcl-description')
        hide_property(properties, 'network-info')

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def cmd_console_restart(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    force = options['force']
    wait = options['wait']
    timeout = options['timeout']

    if wait:
        click.echo("Restarting the HMC and waiting for its availability "
                   "(timeout: {} s)".format(timeout))
    else:
        click.echo("Restarting the HMC")
    try:
        console.restart(force=force, wait_for_available=wait,
                        operation_timeout=timeout)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    if wait:
        click.echo("The HMC has restarted and is available again. Any earlier "
                   "session IDs have become invalid")
    else:
        click.echo("The HMC is currently restarting. Wait for it to be "
                   "available again before issuing any commands. Any earlier "
                   "session IDs will be invalid")


def cmd_get_audit_log(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    begin_time = options['begin'] or None
    if begin_time:
        begin_time = dateutil.parser.parse(begin_time)
    end_time = options['end'] or None
    if end_time:
        end_time = dateutil.parser.parse(end_time)

    try:
        log_items = console.get_audit_log(begin_time, end_time)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    show_list = [
        'timestamp',
        'event-name',
        'event-id',
        'userid',
        'event-message',
    ]

    ts_additions = {}
    for i, log_item in enumerate(log_items):
        hmc_ts = log_item['event-time']
        dt = zhmcclient.datetime_from_timestamp(hmc_ts)
        ts_additions[i] = str(dt)
    additions = {
        'timestamp': ts_additions,
    }

    cmd_ctx.spinner.stop()
    print_dicts(cmd_ctx, log_items, cmd_ctx.output_format,
                show_list=show_list, additions=additions, all=False)


def cmd_get_security_log(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    begin_time = options['begin'] or None
    if begin_time:
        begin_time = dateutil.parser.parse(begin_time)
    end_time = options['end'] or None
    if end_time:
        end_time = dateutil.parser.parse(end_time)

    try:
        log_items = console.get_security_log(begin_time, end_time)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    show_list = [
        'timestamp',
        'event-name',
        'event-id',
        'userid',
        'event-message',
    ]

    ts_additions = {}
    for i, log_item in enumerate(log_items):
        hmc_ts = log_item['event-time']
        dt = zhmcclient.datetime_from_timestamp(hmc_ts)
        ts_additions[i] = str(dt)
    additions = {
        'timestamp': ts_additions,
    }

    cmd_ctx.spinner.stop()
    print_dicts(cmd_ctx, log_items, cmd_ctx.output_format,
                show_list=show_list, additions=additions, all=False)


def cmd_list_api_features(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    name = options['name']
    try:
        features = console.list_api_features(name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    print_list(cmd_ctx, features, cmd_ctx.output_format)
