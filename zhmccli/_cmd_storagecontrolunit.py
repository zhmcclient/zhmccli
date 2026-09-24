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
Commands for storage control units in the FICON storage configuration.
"""


import click

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS, FILTER_OPTIONS, \
    build_filter_args, SORT_OPTIONS, build_sort_props


ALL_VOLUME_TYPES = ['base', 'alias']
DEFAULT_VOLUME_TYPE = 'base'


def find_storagecontrolunit(cmd_ctx, client, stocu_name):
    """
    Find a storage control unit by name and return its resource object.
    """
    console = client.consoles.console
    try:
        stocu = console.storage_control_units.find(name=stocu_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return stocu


@cli.group('storagecontrolunit', options_metavar=COMMAND_OPTIONS_METAVAR)
def storagecontrolunit_group():
    """
    Command group for managing storage control units.

    A storage control unit belongs to one storage subsystem and can have up
    to 8 storage paths and a set of volume ranges in the FICON storage
    configuration of a DPM-enabled CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@storagecontrolunit_group.command('list',
                                  options_metavar=COMMAND_OPTIONS_METAVAR)
@add_options(LIST_OPTIONS)
@add_options(FILTER_OPTIONS)
@add_options(SORT_OPTIONS)
@click.pass_obj
def storagecontrolunit_list(cmd_ctx, **options):
    """
    List the storage control units defined in the HMC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagecontrolunit_list(cmd_ctx, options))


@storagecontrolunit_group.command('show',
                                  options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGECONTROLUNIT', type=str, metavar='STORAGECONTROLUNIT')
@click.pass_obj
def storagecontrolunit_show(cmd_ctx, storagecontrolunit):
    """
    Show the details of a storage control unit.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagecontrolunit_show(cmd_ctx, storagecontrolunit))


@storagecontrolunit_group.command('update',
                                  options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGECONTROLUNIT', type=str, metavar='STORAGECONTROLUNIT')
@click.option('--name', type=str, required=False,
              help='The new name of the storage control unit.')
@click.option('--description', type=str, required=False,
              help='The new description of the storage control unit.')
@click.option('--logical-address', type=str, required=False,
              help='The new logical address (two-char hex) of the storage '
              'control unit within its subsystem.')
@click.pass_obj
def storagecontrolunit_update(cmd_ctx, storagecontrolunit, **options):
    """
    Update the properties of a storage control unit.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagecontrolunit_update(
            cmd_ctx, storagecontrolunit, options))


@storagecontrolunit_group.command('undefine',
                                  options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGECONTROLUNIT', type=str, metavar='STORAGECONTROLUNIT')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm undefining of the storage control '
              'unit.',
              prompt='Are you sure you want to undefine this storage control '
              'unit ?')
@click.pass_obj
def storagecontrolunit_undefine(cmd_ctx, storagecontrolunit, **options):
    """
    Undefine (delete) a storage control unit.

    Any storage paths and volume ranges belonging to this control unit are
    also removed.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagecontrolunit_undefine(
            cmd_ctx, storagecontrolunit, options))


@storagecontrolunit_group.command('add-volume-range',
                                  options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGECONTROLUNIT', type=str, metavar='STORAGECONTROLUNIT')
@click.option('--starting-volume', type=str, required=True,
              help='A two-character lowercase hex unit address for the first '
              'volume in the range.')
@click.option('--ending-volume', type=str, required=False,
              help='A two-character lowercase hex unit address for the last '
              'volume in the range. Defaults to --starting-volume (single '
              'volume).')
@click.option('--volume-type',
              type=click.Choice(ALL_VOLUME_TYPES),
              required=False, default=DEFAULT_VOLUME_TYPE,
              help='The volume type. Default: {d}.'.
              format(d=DEFAULT_VOLUME_TYPE))
@click.pass_obj
def storagecontrolunit_add_volume_range(cmd_ctx, storagecontrolunit,
                                        **options):
    """
    Add a volume range to a storage control unit.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagecontrolunit_add_volume_range(
            cmd_ctx, storagecontrolunit, options))


@storagecontrolunit_group.command('remove-volume-range',
                                  options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGECONTROLUNIT', type=str, metavar='STORAGECONTROLUNIT')
@click.option('--starting-volume', type=str, required=True,
              help='A two-character lowercase hex unit address for the first '
              'volume in the range to remove.')
@click.option('--ending-volume', type=str, required=False,
              help='A two-character lowercase hex unit address for the last '
              'volume in the range. Defaults to --starting-volume (single '
              'volume).')
@click.option('--volume-type',
              type=click.Choice(ALL_VOLUME_TYPES),
              required=False, default=DEFAULT_VOLUME_TYPE,
              help='The volume type. Default: {d}.'.
              format(d=DEFAULT_VOLUME_TYPE))
@click.pass_obj
def storagecontrolunit_remove_volume_range(cmd_ctx, storagecontrolunit,
                                           **options):
    """
    Remove a volume range from a storage control unit.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagecontrolunit_remove_volume_range(
            cmd_ctx, storagecontrolunit, options))


def cmd_storagecontrolunit_list(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    filter_args = build_filter_args(cmd_ctx, options['filter'])

    try:
        stocus = console.storage_control_units.list(filter_args=filter_args)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    show_list = [
        'name',
    ]
    if not options['names_only']:
        show_list.extend([
            'logical-address',
            'description',
        ])
    if options['uri']:
        show_list.extend([
            'object-uri',
        ])

    sort_props = build_sort_props(cmd_ctx, options['sort'], default=['name'])
    try:
        print_resources(cmd_ctx, stocus, cmd_ctx.output_format, show_list,
                        None, all=options['all'], sort_props=sort_props)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_storagecontrolunit_show(cmd_ctx, stocu_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    stocu = find_storagecontrolunit(cmd_ctx, client, stocu_name)

    try:
        stocu.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(stocu.properties)

    # Add artificial property 'parent-name'
    properties['parent-name'] = console.name

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def cmd_storagecontrolunit_update(cmd_ctx, stocu_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stocu = find_storagecontrolunit(cmd_ctx, client, stocu_name)

    org_options = original_options(options)
    properties = options_to_properties(org_options, {})

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating storage control unit "
                   "'{cu}'.".format(cu=stocu_name))
        return

    try:
        stocu.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    if 'name' in properties and properties['name'] != stocu_name:
        click.echo("Storage control unit '{cu}' has been renamed to '{cun}' "
                   "and was updated.".
                   format(cu=stocu_name, cun=properties['name']))
    else:
        click.echo("Storage control unit '{cu}' has been updated.".
                   format(cu=stocu_name))


def cmd_storagecontrolunit_undefine(cmd_ctx, stocu_name, options):
    # pylint: disable=missing-function-docstring,unused-argument

    client = zhmcclient.Client(cmd_ctx.session)
    stocu = find_storagecontrolunit(cmd_ctx, client, stocu_name)

    try:
        stocu.undefine()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Storage control unit '{cu}' has been undefined.".
               format(cu=stocu_name))


def cmd_storagecontrolunit_add_volume_range(cmd_ctx, stocu_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stocu = find_storagecontrolunit(cmd_ctx, client, stocu_name)

    starting_volume = options['starting_volume']
    ending_volume = options.get('ending_volume')
    volume_type = options['volume_type']

    try:
        stocu.add_volume_range(starting_volume, ending_volume, volume_type)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    if ending_volume and ending_volume != starting_volume:
        click.echo("Volume range {s}-{e} ({t}) has been added to storage "
                   "control unit '{cu}'.".
                   format(s=starting_volume, e=ending_volume,
                          t=volume_type, cu=stocu_name))
    else:
        click.echo("Volume {v} ({t}) has been added to storage control unit "
                   "'{cu}'.".
                   format(v=starting_volume, t=volume_type, cu=stocu_name))


def cmd_storagecontrolunit_remove_volume_range(  # pylint: disable=invalid-name
        cmd_ctx, stocu_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stocu = find_storagecontrolunit(cmd_ctx, client, stocu_name)

    starting_volume = options['starting_volume']
    ending_volume = options.get('ending_volume')
    volume_type = options['volume_type']

    try:
        stocu.remove_volume_range(starting_volume, ending_volume, volume_type)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    if ending_volume and ending_volume != starting_volume:
        click.echo("Volume range {s}-{e} ({t}) has been removed from storage "
                   "control unit '{cu}'.".
                   format(s=starting_volume, e=ending_volume,
                          t=volume_type, cu=stocu_name))
    else:
        click.echo("Volume {v} ({t}) has been removed from storage control "
                   "unit '{cu}'.".
                   format(v=starting_volume, t=volume_type, cu=stocu_name))
