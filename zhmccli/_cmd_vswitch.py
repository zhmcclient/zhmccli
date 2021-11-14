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
Commands for virtual switches.
"""

from __future__ import absolute_import

import click

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_resources, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS
from ._cmd_cpc import find_cpc


def find_vswitch(cmd_ctx, client, cpc_or_name, vswitch_name):
    """
    Find a virtual switch by name and return its resource object.
    """
    if isinstance(cpc_or_name, zhmcclient.Cpc):
        cpc = cpc_or_name
    else:
        cpc = find_cpc(cmd_ctx, client, cpc_or_name)
    # The CPC must be in DPM mode. We don't check that because it would
    # cause a GET to the CPC resource that we otherwise don't need.
    try:
        vswitch = cpc.virtual_switches.find(name=vswitch_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return vswitch


@cli.group('vswitch', options_metavar=COMMAND_OPTIONS_METAVAR)
def vswitch_group():
    """
    Command group for managing virtual switches (DPM mode only).

    Virtual switches are automatically established by the system for OSA
    and Hipersocket adapters. They do not exist for ROCE and CNA adapters.

    The commands in this group work only on CPCs that are in DPM mode.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@vswitch_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@add_options(LIST_OPTIONS)
@click.option('--adapter', is_flag=True, required=False, hidden=True)
@click.pass_obj
def vswitch_list(cmd_ctx, cpc, **options):
    """
    List the virtual switches in a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_vswitch_list(cmd_ctx, cpc, options))


@vswitch_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('VSWITCH', type=str, metavar='VSWITCH')
@click.pass_obj
def vswitch_show(cmd_ctx, cpc, vswitch):
    """
    Show the details of a virtual switch.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_vswitch_show(cmd_ctx, cpc, vswitch))


@vswitch_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('VSWITCH', type=str, metavar='VSWITCH')
@click.option('--name', type=str, required=False,
              help='The new name of the virtual switch.')
@click.option('--description', type=str, required=False,
              help='The new description of the virtual switch.')
@click.pass_obj
def vswitch_update(cmd_ctx, cpc, vswitch, **options):
    """
    Update the properties of a virtual switch.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_vswitch_update(cmd_ctx, cpc, vswitch,
                                                   options))


def cmd_vswitch_list(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    try:
        vswitches = cpc.virtual_switches.list()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    if options['adapter']:
        click.echo("The --adapter option is deprecated and adapter information "
                   "is now always shown.")

    show_list = [
        'name',
        'cpc',
    ]
    if not options['names_only']:
        show_list.extend([
            'adapter',
            'type',
            'port',
        ])
    if options['uri']:
        show_list.extend([
            'object-uri',
        ])

    cpc_additions = {}
    adapter_additions = {}
    for vswitch in vswitches:
        cpc_additions[vswitch.uri] = cpc_name
        try:
            adapter_uri = vswitch.prop('backing-adapter-uri')
            adapter = cpc.adapters.find(**{'object-uri': adapter_uri})
            adapter_additions[vswitch.uri] = adapter.name
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)
    additions = {
        'cpc': cpc_additions,
        'adapter': adapter_additions,
    }

    try:
        print_resources(cmd_ctx, vswitches, cmd_ctx.output_format, show_list,
                        additions, all=options['all'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_vswitch_show(cmd_ctx, cpc_name, vswitch_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    vswitch = find_vswitch(cmd_ctx, client, cpc_name, vswitch_name)

    try:
        vswitch.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    print_properties(cmd_ctx, vswitch.properties, cmd_ctx.output_format)


def cmd_vswitch_update(cmd_ctx, cpc_name, vswitch_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    vswitch = find_vswitch(cmd_ctx, client, cpc_name, vswitch_name)

    org_options = original_options(options)
    properties = options_to_properties(org_options)

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating virtual switch '{s}'.".
                   format(s=vswitch_name))
        return

    try:
        vswitch.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    if 'name' in properties and properties['name'] != vswitch_name:
        click.echo("Virtual switch '{s}' has been renamed to '{sn}' and was "
                   "updated.".format(s=vswitch_name, sn=properties['name']))
    else:
        click.echo("Virtual switch '{s}' has been updated.".
                   format(s=vswitch_name))
