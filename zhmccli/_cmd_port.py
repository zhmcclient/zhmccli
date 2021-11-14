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
Commands for adapter ports.
"""

from __future__ import absolute_import

import click

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_resources, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS
from ._cmd_adapter import find_adapter


def find_port(cmd_ctx, client, cpc_or_name, adapter_name, port_name):
    """
    Find a port by name and return its resource object.
    """
    adapter = find_adapter(cmd_ctx, client, cpc_or_name, adapter_name)
    try:
        port = adapter.ports.find(name=port_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return port


@cli.group('port', options_metavar=COMMAND_OPTIONS_METAVAR)
def port_group():
    """
    Command group for managing adapter ports (DPM mode only).

    The commands in this group work only on CPCs that are in DPM mode.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@port_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('ADAPTER', type=str, metavar='ADAPTER')
@add_options(LIST_OPTIONS)
@click.pass_obj
def port_list(cmd_ctx, cpc, adapter, **options):
    """
    List the ports of an adapter.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_port_list(cmd_ctx, cpc, adapter, options))


@port_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('ADAPTER', type=str, metavar='ADAPTER')
@click.argument('PORT', type=str, metavar='PORT')
@click.pass_obj
def port_show(cmd_ctx, cpc, adapter, port):
    """
    Show the details of an adapter port.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_port_show(cmd_ctx, cpc, adapter, port))


@port_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('ADAPTER', type=str, metavar='ADAPTER')
@click.argument('PORT', type=str, metavar='PORT')
@click.option('--description', type=str, required=False,
              help='The new description of the port.')
@click.pass_obj
def port_update(cmd_ctx, cpc, adapter, port, **options):
    """
    Update the properties of an adapter port.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    The port may be on a physical adapter (e.g. a discovered OSA card) or a
    logical adapter (e.g. HiperSockets).

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_port_update(cmd_ctx, cpc, adapter, port,
                                                options))


def cmd_port_list(cmd_ctx, cpc_name, adapter_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    adapter = find_adapter(cmd_ctx, client, cpc_name, adapter_name)

    try:
        ports = adapter.ports.list(full_properties=True)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    show_list = [
        'name',
        'adapter',
        'cpc',
    ]
    if not options['names_only']:
        show_list.extend([
            'index',
        ])
    if options['uri']:
        show_list.extend([
            'element-uri',
        ])

    cpc_additions = {}
    adapter_additions = {}
    for port in ports:
        cpc_additions[port.uri] = cpc_name
        adapter_additions[port.uri] = adapter_name
    additions = {
        'adapter': adapter_additions,
        'cpc': cpc_additions,
    }

    try:
        print_resources(cmd_ctx, ports, cmd_ctx.output_format, show_list,
                        additions, all=options['all'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_port_show(cmd_ctx, cpc_name, adapter_name, port_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    port = find_port(cmd_ctx, client, cpc_name, adapter_name, port_name)

    try:
        port.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    print_properties(cmd_ctx, port.properties, cmd_ctx.output_format)


def cmd_port_update(cmd_ctx, cpc_name, adapter_name, port_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    port = find_port(cmd_ctx, client, cpc_name, adapter_name, port_name)

    org_options = original_options(options)
    properties = options_to_properties(org_options)

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating port '{p}'.".
                   format(p=port_name))
        return

    try:
        port.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    # Adapter ports cannot be renamed.
    click.echo("Port '{p}' has been updated.".format(p=port_name))
