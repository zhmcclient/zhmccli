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
Commands for storage fabrics in the FICON storage configuration.
"""


import click

import zhmcclient
from .zhmccli import cli
from ._cmd_cpc import find_cpc
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS, FILTER_OPTIONS, \
    build_filter_args, SORT_OPTIONS, build_sort_props


def find_storagefabric(cmd_ctx, client, stofab_name):
    """
    Find a storage fabric by name and return its resource object.
    """
    console = client.consoles.console
    try:
        stofab = console.storage_fabrics.find(name=stofab_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return stofab


@cli.group('storagefabric', options_metavar=COMMAND_OPTIONS_METAVAR)
def storagefabric_group():
    """
    Command group for managing storage fabrics.

    A storage fabric is a collection of interconnected storage switches in the
    FICON storage configuration associated with a DPM-enabled CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@storagefabric_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--cpc', type=str, required=False,
              help='Filter storage fabrics to those associated with the '
              'specified CPC.')
@add_options(LIST_OPTIONS)
@add_options(FILTER_OPTIONS)
@add_options(SORT_OPTIONS)
@click.pass_obj
def storagefabric_list(cmd_ctx, **options):
    """
    List the storage fabrics defined in the HMC.

    The optional --cpc option filters the list to those storage fabrics
    associated with the specified CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_storagefabric_list(cmd_ctx, options))


@storagefabric_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGEFABRIC', type=str, metavar='STORAGEFABRIC')
@click.pass_obj
def storagefabric_show(cmd_ctx, storagefabric):
    """
    Show the details of a storage fabric.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagefabric_show(cmd_ctx, storagefabric))


@storagefabric_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--name', type=str, required=True,
              help='The name of the new storage fabric.')
@click.option('--cpc', type=str, required=True,
              help='The name of the CPC associated with the new storage '
              'fabric.')
@click.option('--description', type=str, required=False,
              help='The description of the new storage fabric. '
              'Default: Empty.')
@click.option('--high-integrity', type=bool, required=False,
              help='Indicates whether the storage fabric is a high-integrity '
              'fabric. Default: False.')
@click.pass_obj
def storagefabric_create(cmd_ctx, **options):
    """
    Create a storage fabric.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_storagefabric_create(cmd_ctx, options))


@storagefabric_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGEFABRIC', type=str, metavar='STORAGEFABRIC')
@click.option('--name', type=str, required=False,
              help='The new name of the storage fabric.')
@click.option('--description', type=str, required=False,
              help='The new description of the storage fabric.')
@click.option('--high-integrity', type=bool, required=False,
              help='Indicates whether the storage fabric is a high-integrity '
              'fabric.')
@click.pass_obj
def storagefabric_update(cmd_ctx, storagefabric, **options):
    """
    Update the properties of a storage fabric.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagefabric_update(cmd_ctx, storagefabric, options))


@storagefabric_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGEFABRIC', type=str, metavar='STORAGEFABRIC')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the storage fabric.',
              prompt='Are you sure you want to delete this storage fabric ?')
@click.pass_obj
def storagefabric_delete(cmd_ctx, storagefabric, **options):
    """
    Delete a storage fabric.

    The storage fabric must be empty (no storage switches) before it can be
    deleted.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagefabric_delete(cmd_ctx, storagefabric, options))


def cmd_storagefabric_list(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    filter_args = build_filter_args(cmd_ctx, options['filter'])

    cpc_name = options.get('cpc')
    if cpc_name:
        cpc = find_cpc(cmd_ctx, client, cpc_name)
        if filter_args is None:
            filter_args = {}
        filter_args['cpc-uri'] = cpc.uri

    try:
        stofabs = console.storage_fabrics.list(filter_args=filter_args)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    show_list = [
        'name',
    ]
    if not options['names_only']:
        show_list.extend([
            'high-integrity',
            'description',
        ])
    if options['uri']:
        show_list.extend([
            'object-uri',
        ])

    sort_props = build_sort_props(cmd_ctx, options['sort'], default=['name'])
    try:
        print_resources(cmd_ctx, stofabs, cmd_ctx.output_format, show_list,
                        None, all=options['all'], sort_props=sort_props)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_storagefabric_show(cmd_ctx, stofab_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    stofab = find_storagefabric(cmd_ctx, client, stofab_name)

    try:
        stofab.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(stofab.properties)

    # Add artificial property 'parent-name'
    properties['parent-name'] = console.name

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def cmd_storagefabric_create(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    name_map = {
        # The following options are handled in this function:
        'cpc': None,
    }
    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    cpc_name = org_options['cpc']
    cpc = find_cpc(cmd_ctx, client, cpc_name)
    properties['cpc-uri'] = cpc.uri

    try:
        new_stofab = console.storage_fabrics.create(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("New storage fabric '{sf}' has been created.".
               format(sf=new_stofab.properties['name']))


def cmd_storagefabric_update(cmd_ctx, stofab_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stofab = find_storagefabric(cmd_ctx, client, stofab_name)

    org_options = original_options(options)
    properties = options_to_properties(org_options, {})

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating storage fabric "
                   "'{sf}'.".format(sf=stofab_name))
        return

    try:
        stofab.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    if 'name' in properties and properties['name'] != stofab_name:
        click.echo("Storage fabric '{sf}' has been renamed to '{sfn}' and "
                   "was updated.".
                   format(sf=stofab_name, sfn=properties['name']))
    else:
        click.echo("Storage fabric '{sf}' has been updated.".
                   format(sf=stofab_name))


def cmd_storagefabric_delete(cmd_ctx, stofab_name, options):
    # pylint: disable=missing-function-docstring,unused-argument

    client = zhmcclient.Client(cmd_ctx.session)
    stofab = find_storagefabric(cmd_ctx, client, stofab_name)

    try:
        stofab.delete()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Storage fabric '{sf}' has been deleted.".
               format(sf=stofab_name))
