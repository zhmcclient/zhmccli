# Copyright 2026 IBM Corp. All Rights Reserved.
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
Commands for storage subsystems in the FICON storage configuration.
"""


import click

import zhmcclient
from .zhmccli import cli
from ._cmd_storagesite import find_storagesite
from ._helper import print_properties, print_resources, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS, FILTER_OPTIONS, \
    build_filter_args, SORT_OPTIONS, build_sort_props


def find_storagesubsystem(cmd_ctx, client, stosub_name):
    """
    Find a storage subsystem by name and return its resource object.
    """
    console = client.consoles.console
    try:
        stosub = console.storage_subsystems.find(name=stosub_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return stosub


@cli.group('storagesubsystem', options_metavar=COMMAND_OPTIONS_METAVAR)
def storagesubsystem_group():
    """
    Command group for managing storage subsystems.

    A storage subsystem is a physical storage device (e.g. DS8000) connected
    to a storage site in the FICON storage configuration of a DPM-enabled CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@storagesubsystem_group.command('list',
                                options_metavar=COMMAND_OPTIONS_METAVAR)
@add_options(LIST_OPTIONS)
@add_options(FILTER_OPTIONS)
@add_options(SORT_OPTIONS)
@click.pass_obj
def storagesubsystem_list(cmd_ctx, **options):
    """
    List the storage subsystems defined in the HMC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_storagesubsystem_list(cmd_ctx, options))


@storagesubsystem_group.command('show',
                                options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGESUBSYSTEM', type=str, metavar='STORAGESUBSYSTEM')
@click.pass_obj
def storagesubsystem_show(cmd_ctx, storagesubsystem):
    """
    Show the details of a storage subsystem.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagesubsystem_show(cmd_ctx, storagesubsystem))


@storagesubsystem_group.command('update',
                                options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGESUBSYSTEM', type=str, metavar='STORAGESUBSYSTEM')
@click.option('--name', type=str, required=False,
              help='The new name of the storage subsystem.')
@click.option('--description', type=str, required=False,
              help='The new description of the storage subsystem.')
@click.pass_obj
def storagesubsystem_update(cmd_ctx, storagesubsystem, **options):
    """
    Update the properties of a storage subsystem.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagesubsystem_update(
            cmd_ctx, storagesubsystem, options))


@storagesubsystem_group.command('move-to-storage-site',
                                options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGESUBSYSTEM', type=str, metavar='STORAGESUBSYSTEM')
@click.option('--storage-site', type=str, required=True,
              help='The name of the target storage site.')
@click.pass_obj
def storagesubsystem_move_to_storage_site(cmd_ctx, storagesubsystem,
                                          **options):
    """
    Move a storage subsystem to a different storage site.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagesubsystem_move_to_storage_site(
            cmd_ctx, storagesubsystem, options))


@storagesubsystem_group.command('add-connection-endpoint',
                                options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGESUBSYSTEM', type=str, metavar='STORAGESUBSYSTEM')
@click.option('--endpoint-uri', type=str, required=True,
              help='The URI of the Storage Switch or Adapter to connect.')
@click.option('--port-id', type=str, required=False,
              help='A two-character lowercase hex port ID. Required when '
              'connecting to a Storage Switch; prohibited for an Adapter.')
@click.pass_obj
def storagesubsystem_add_connection_endpoint(cmd_ctx, storagesubsystem,
                                             **options):
    """
    Add a connection endpoint to a storage subsystem.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagesubsystem_add_connection_endpoint(
            cmd_ctx, storagesubsystem, options))


@storagesubsystem_group.command('remove-connection-endpoint',
                                options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGESUBSYSTEM', type=str, metavar='STORAGESUBSYSTEM')
@click.option('--endpoint-uri', type=str, required=True,
              help='The URI of the Storage Switch or Adapter to disconnect.')
@click.option('--port-id', type=str, required=False,
              help='A two-character lowercase hex port ID. Required when '
              'disconnecting from a Storage Switch.')
@click.pass_obj
def storagesubsystem_remove_connection_endpoint(  # pylint: disable=invalid-name
        cmd_ctx, storagesubsystem, **options):
    """
    Remove a connection endpoint from a storage subsystem.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagesubsystem_remove_connection_endpoint(
            cmd_ctx, storagesubsystem, options))


def cmd_storagesubsystem_list(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    filter_args = build_filter_args(cmd_ctx, options['filter'])

    try:
        stosubs = console.storage_subsystems.list(filter_args=filter_args)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    show_list = [
        'name',
    ]
    if not options['names_only']:
        show_list.extend([
            'description',
        ])
    if options['uri']:
        show_list.extend([
            'object-uri',
        ])

    sort_props = build_sort_props(cmd_ctx, options['sort'], default=['name'])
    try:
        print_resources(cmd_ctx, stosubs, cmd_ctx.output_format, show_list,
                        None, all=options['all'], sort_props=sort_props)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_storagesubsystem_show(cmd_ctx, stosub_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    stosub = find_storagesubsystem(cmd_ctx, client, stosub_name)

    try:
        stosub.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(stosub.properties)

    # Add artificial property 'parent-name'
    properties['parent-name'] = console.name

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def cmd_storagesubsystem_update(cmd_ctx, stosub_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stosub = find_storagesubsystem(cmd_ctx, client, stosub_name)

    org_options = original_options(options)
    properties = options_to_properties(org_options, {})

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating storage subsystem "
                   "'{ss}'.".format(ss=stosub_name))
        return

    try:
        stosub.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    if 'name' in properties and properties['name'] != stosub_name:
        click.echo("Storage subsystem '{ss}' has been renamed to '{ssn}' and "
                   "was updated.".
                   format(ss=stosub_name, ssn=properties['name']))
    else:
        click.echo("Storage subsystem '{ss}' has been updated.".
                   format(ss=stosub_name))


def cmd_storagesubsystem_move_to_storage_site(  # pylint: disable=invalid-name
        cmd_ctx, stosub_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stosub = find_storagesubsystem(cmd_ctx, client, stosub_name)

    stosite_name = options['storage_site']
    stosite = find_storagesite(cmd_ctx, client, stosite_name)

    try:
        stosub.move_to_storage_site(stosite.uri)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Storage subsystem '{ss}' has been moved to storage site "
               "'{si}'.".format(ss=stosub_name, si=stosite_name))


def cmd_storagesubsystem_add_connection_endpoint(
        cmd_ctx, stosub_name, options):
    # pylint: disable=missing-function-docstring,invalid-name

    client = zhmcclient.Client(cmd_ctx.session)
    stosub = find_storagesubsystem(cmd_ctx, client, stosub_name)

    endpoint_uri = options['endpoint_uri']
    port_id = options.get('port_id')

    try:
        stosub.add_connection_endpoint(endpoint_uri, port_id)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Connection endpoint '{ep}' has been added to storage "
               "subsystem '{ss}'.".
               format(ep=endpoint_uri, ss=stosub_name))


def cmd_storagesubsystem_remove_connection_endpoint(
        cmd_ctx, stosub_name, options):
    # pylint: disable=missing-function-docstring,invalid-name

    client = zhmcclient.Client(cmd_ctx.session)
    stosub = find_storagesubsystem(cmd_ctx, client, stosub_name)

    endpoint_uri = options['endpoint_uri']
    port_id = options.get('port_id')

    try:
        stosub.remove_connection_endpoint(endpoint_uri, port_id)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Connection endpoint '{ep}' has been removed from storage "
               "subsystem '{ss}'.".
               format(ep=endpoint_uri, ss=stosub_name))
