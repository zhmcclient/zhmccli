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
Commands for storage switches in the FICON storage configuration.
"""


import click

import zhmcclient
from .zhmccli import cli
from ._cmd_storagesite import find_storagesite
from ._cmd_storagefabric import find_storagefabric
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS, FILTER_OPTIONS, \
    build_filter_args, SORT_OPTIONS, build_sort_props


def find_storageswitch(cmd_ctx, client, stosw_name):
    """
    Find a storage switch by name and return its resource object.
    """
    console = client.consoles.console
    try:
        stosw = console.storage_switches.find(name=stosw_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return stosw


@cli.group('storageswitch', options_metavar=COMMAND_OPTIONS_METAVAR)
def storageswitch_group():
    """
    Command group for managing storage switches.

    A storage switch is a physical FICON storage switch belonging to one
    storage site and one storage fabric in the FICON storage configuration of
    a DPM-enabled CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@storageswitch_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@add_options(LIST_OPTIONS)
@add_options(FILTER_OPTIONS)
@add_options(SORT_OPTIONS)
@click.pass_obj
def storageswitch_list(cmd_ctx, **options):
    """
    List the storage switches defined in the HMC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_storageswitch_list(cmd_ctx, options))


@storageswitch_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGESWITCH', type=str, metavar='STORAGESWITCH')
@click.pass_obj
def storageswitch_show(cmd_ctx, storageswitch):
    """
    Show the details of a storage switch.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storageswitch_show(cmd_ctx, storageswitch))


@storageswitch_group.command('define', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--domain-id', type=str, required=True,
              help='The FICON domain ID (two-char hex) identifying this switch '
              'within its storage fabric.')
@click.option('--storage-fabric', type=str, required=True,
              help='The name of the storage fabric to which this switch '
              'belongs.')
@click.option('--storage-site', type=str, required=True,
              help='The name of the storage site at which this switch is '
              'located.')
@click.option('--name', type=str, required=False,
              help='The name of the new storage switch. '
              'Default: Auto-assigned.')
@click.option('--description', type=str, required=False,
              help='The description of the new storage switch. Default: Empty.')
@click.option('--port-count', type=int, required=False,
              help='The number of physical ports on the storage switch.')
@click.pass_obj
def storageswitch_define(cmd_ctx, **options):
    """
    Define a new storage switch.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_storageswitch_define(cmd_ctx, options))


@storageswitch_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGESWITCH', type=str, metavar='STORAGESWITCH')
@click.option('--name', type=str, required=False,
              help='The new name of the storage switch.')
@click.option('--description', type=str, required=False,
              help='The new description of the storage switch.')
@click.option('--domain-id', type=str, required=False,
              help='The new FICON domain ID (two-char hex).')
@click.option('--port-count', type=int, required=False,
              help='The new number of physical ports on the storage switch.')
@click.pass_obj
def storageswitch_update(cmd_ctx, storageswitch, **options):
    """
    Update the properties of a storage switch.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storageswitch_update(cmd_ctx, storageswitch, options))


@storageswitch_group.command('undefine',
                             options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGESWITCH', type=str, metavar='STORAGESWITCH')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm undefining of the storage switch.',
              prompt='Are you sure you want to undefine this storage switch ?')
@click.pass_obj
def storageswitch_undefine(cmd_ctx, storageswitch, **options):
    """
    Undefine (delete) a storage switch.

    If the storage switch has switch ports, they are removed as well.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storageswitch_undefine(cmd_ctx, storageswitch, options))


@storageswitch_group.command('move-to-storage-site',
                             options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGESWITCH', type=str, metavar='STORAGESWITCH')
@click.option('--storage-site', type=str, required=True,
              help='The name of the target storage site.')
@click.pass_obj
def storageswitch_move_to_storage_site(cmd_ctx, storageswitch, **options):
    """
    Move a storage switch to a different storage site.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storageswitch_move_to_storage_site(
            cmd_ctx, storageswitch, options))


@storageswitch_group.command('move-to-storage-fabric',
                             options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGESWITCH', type=str, metavar='STORAGESWITCH')
@click.option('--storage-fabric', type=str, required=True,
              help='The name of the target storage fabric.')
@click.pass_obj
def storageswitch_move_to_storage_fabric(cmd_ctx, storageswitch, **options):
    """
    Move a storage switch to a different storage fabric.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storageswitch_move_to_storage_fabric(
            cmd_ctx, storageswitch, options))


def cmd_storageswitch_list(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    filter_args = build_filter_args(cmd_ctx, options['filter'])

    try:
        stosws = console.storage_switches.list(filter_args=filter_args)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    show_list = [
        'name',
    ]
    if not options['names_only']:
        show_list.extend([
            'domain-id',
            'description',
        ])
    if options['uri']:
        show_list.extend([
            'object-uri',
        ])

    sort_props = build_sort_props(cmd_ctx, options['sort'], default=['name'])
    try:
        print_resources(cmd_ctx, stosws, cmd_ctx.output_format, show_list,
                        None, all=options['all'], sort_props=sort_props)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_storageswitch_show(cmd_ctx, stosw_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    stosw = find_storageswitch(cmd_ctx, client, stosw_name)

    try:
        stosw.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(stosw.properties)

    # Add artificial property 'parent-name'
    properties['parent-name'] = console.name

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def cmd_storageswitch_define(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    name_map = {
        # The following options are handled in this function:
        'storage-fabric': None,
        'storage-site': None,
    }
    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    stofab_name = org_options['storage-fabric']
    stofab = find_storagefabric(cmd_ctx, client, stofab_name)
    properties['storage-fabric-uri'] = stofab.uri

    stosite_name = org_options['storage-site']
    stosite = find_storagesite(cmd_ctx, client, stosite_name)
    properties['storage-site-uri'] = stosite.uri

    try:
        new_stosw = console.storage_switches.define(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("New storage switch '{sw}' has been defined.".
               format(sw=new_stosw.properties.get('name', new_stosw.uri)))


def cmd_storageswitch_update(cmd_ctx, stosw_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stosw = find_storageswitch(cmd_ctx, client, stosw_name)

    org_options = original_options(options)
    properties = options_to_properties(org_options, {})

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating storage switch "
                   "'{sw}'.".format(sw=stosw_name))
        return

    try:
        stosw.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    if 'name' in properties and properties['name'] != stosw_name:
        click.echo("Storage switch '{sw}' has been renamed to '{swn}' and "
                   "was updated.".
                   format(sw=stosw_name, swn=properties['name']))
    else:
        click.echo("Storage switch '{sw}' has been updated.".
                   format(sw=stosw_name))


def cmd_storageswitch_undefine(cmd_ctx, stosw_name, options):
    # pylint: disable=missing-function-docstring,unused-argument

    client = zhmcclient.Client(cmd_ctx.session)
    stosw = find_storageswitch(cmd_ctx, client, stosw_name)

    try:
        stosw.undefine()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Storage switch '{sw}' has been undefined.".
               format(sw=stosw_name))


def cmd_storageswitch_move_to_storage_site(cmd_ctx, stosw_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stosw = find_storageswitch(cmd_ctx, client, stosw_name)

    stosite_name = options['storage_site']
    stosite = find_storagesite(cmd_ctx, client, stosite_name)

    try:
        stosw.move_to_storage_site(stosite.uri)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Storage switch '{sw}' has been moved to storage site '{ss}'.".
               format(sw=stosw_name, ss=stosite_name))


def cmd_storageswitch_move_to_storage_fabric(cmd_ctx, stosw_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stosw = find_storageswitch(cmd_ctx, client, stosw_name)

    stofab_name = options['storage_fabric']
    stofab = find_storagefabric(cmd_ctx, client, stofab_name)

    try:
        stosw.move_to_storage_fabric(stofab.uri)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Storage switch '{sw}' has been moved to storage fabric "
               "'{sf}'.".format(sw=stosw_name, sf=stofab_name))
