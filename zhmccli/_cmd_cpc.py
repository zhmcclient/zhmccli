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
Commands for CPCs.
"""

from __future__ import absolute_import

import click
from tabulate import tabulate

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_resources, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS, TABLE_FORMATS, hide_property


POWER_SAVING_TYPES = ['high-performance', 'low-power', 'custom']
DEFAULT_POWER_SAVING_TYPE = 'high-performance'
POWER_CAPPING_STATES = ['disabled', 'enabled', 'custom']


def find_cpc(cmd_ctx, client, cpc_name):
    """
    Find a CPC by name and return its resource object.
    """
    try:
        cpc = client.cpcs.find(name=cpc_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return cpc


@cli.group('cpc', options_metavar=COMMAND_OPTIONS_METAVAR)
def cpc_group():
    """
    Command group for managing CPCs.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@cpc_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--type', is_flag=True, required=False, hidden=True)
@click.option('--mach', is_flag=True, required=False, hidden=True)
@add_options(LIST_OPTIONS)
@click.pass_obj
def cpc_list(cmd_ctx, **options):
    """
    List the CPCs managed by the HMC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_list(cmd_ctx, options))


@cpc_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.option('--all', is_flag=True, required=False,
              help='Show all properties. Default: Hide some properties in '
              'table output formats')
@click.pass_obj
def cpc_show(cmd_ctx, cpc, **options):
    """
    Show details of a CPC.

    \b
    In table output formats, the following properties are hidden by default
    but can be shown by using the --all option:
      - auto-start-list
      - available-features-list
      - cpc-power-saving-state
      - ec-mcl-description
      - network1-ipv6-info
      - network2-ipv6-info
      - stp-configuration

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_show(cmd_ctx, cpc, options))


@cpc_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.option('--description', type=str, required=False,
              help='The new description of the CPC. '
              '(DPM mode only).')
@click.option('--acceptable-status', type=str, required=False,
              help='The new set of acceptable operational status values.')
# TODO: Support multiple values for acceptable-status
@click.option('--next-activation-profile', type=str, required=False,
              help='The name of the new next reset activation profile. '
              '(not in DPM mode).')
@click.option('--processor-time-slice', type=int, required=False,
              help='The new time slice (in ms) for logical processors. '
              'A value of 0 causes the time slice to be dynamically '
              'determined by the system. A positive value causes a constant '
              'time slice to be used. '
              '(not in DPM mode).')
@click.option('--wait-ends-slice/--no-wait-ends-slice', default=None,
              required=False,
              help='The new setting for making logical processors lose their '
              'time slice when they enter a wait state. '
              '(not in DPM mode).')
@click.pass_obj
def cpc_update(cmd_ctx, cpc, **options):
    """
    Update the properties of a CPC.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.

    \b
    Limitations:
      * The --acceptable-status option does not support multiple values.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_update(cmd_ctx, cpc, options))


@cpc_group.command('set-power-save', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.option('--power-saving', type=click.Choice(POWER_SAVING_TYPES),
              required=False, default=DEFAULT_POWER_SAVING_TYPE,
              help='Defines the type of power saving. Default: {pd}'.
              format(pd=DEFAULT_POWER_SAVING_TYPE))
@click.pass_obj
def set_power_save(cmd_ctx, cpc, **options):
    """
    Set the power save settings of a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_set_power_save(cmd_ctx, cpc, options))


@cpc_group.command('set-power-capping',
                   options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.option('--power-capping-state', type=click.Choice(POWER_CAPPING_STATES),
              required=True,
              help='Defines the state of power capping.')
@click.option('--power-cap-current', type=int, required=False,
              help='Specifies the current cap value for the CPC in watts (W). '
              'Required if power capping state is enabled.')
@click.pass_obj
def set_power_capping(cmd_ctx, cpc, **options):
    """
    Set the power capping settings of a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_set_power_capping(cmd_ctx, cpc,
                                                          options))


@cpc_group.command('get-em-data', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.pass_obj
def get_em_data(cmd_ctx, cpc):
    """
    Get all energy management data of a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_get_em_data(cmd_ctx, cpc))


@cpc_group.group('autostart', options_metavar=COMMAND_OPTIONS_METAVAR)
def cpc_autostart_group():
    """
    Command group for managing the auto-start list of a CPC (in DPM mode).

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@cpc_autostart_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.pass_obj
def cpc_autostart_show(cmd_ctx, cpc):
    """
    Show the auto-start list of a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_autostart_show(cmd_ctx, cpc))


@cpc_autostart_group.command('add', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITIONS_DELAY', type=(str, int), metavar='PARTITIONS DELAY')
@click.option('--group', type=str, metavar='GROUP',
              required=False,
              help='Add the partition(s) as a partition group with this name. '
              'Required when adding a group.')
@click.option('--description', type=str, metavar='TEXT',
              required=False,
              help='Description of partition group. '
              'Default: No description.')
@click.option('--before', type=str, metavar='PARTITION_OR_GROUP',
              required=False,
              help='Insert the new partition or group before this '
              'partition/group. '
              'Default: Append new partition or group to the end.')
@click.option('--after', type=str, metavar='PARTITION_OR_GROUP',
              required=False,
              help='Insert the new partition or group after this '
              'partition/group. '
              'Default: Append new partition or group to the end.')
@click.pass_obj
def cpc_autostart_add(cmd_ctx, cpc, partitions_delay, **options):
    """
    Add a partition or group to the auto-start list of a CPC.

    A partition group exists only in context of the auto-start list; it has
    nothing to do with Group objects.

    PARTITIONS is the partition name or a comma-separated list of partition
    names in case of adding a partition group.

    DELAY is the delay afer starting this partition or group, in seconds.

    The updated auto-start list is shown.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_cpc_autostart_add(cmd_ctx, cpc, partitions_delay, options))


@cpc_autostart_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION_OR_GROUP', type=str, metavar='PARTITION_OR_GROUP')
@click.pass_obj
def cpc_autostart_delete(cmd_ctx, cpc, partition_or_group):
    """
    Delete a partition or group from the auto-start list of a CPC.

    The updated auto-start list is shown.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_cpc_autostart_delete(cmd_ctx, cpc, partition_or_group))


@cpc_autostart_group.command('clear', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.pass_obj
def cpc_autostart_clear(cmd_ctx, cpc):
    """
    Clear the auto-start list of a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_cpc_autostart_clear(cmd_ctx, cpc))


def cmd_cpc_list(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)

    try:
        cpcs = client.cpcs.list()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    if options['type']:
        click.echo("The --type option is deprecated and type information "
                   "is now always shown.")
    if options['mach']:
        click.echo("The --mach option is deprecated and machine information "
                   "is now always shown.")

    show_list = [
        'name',
    ]
    if not options['names_only']:
        show_list.extend([
            'status',
            'dpm-enabled',
            'se-version',
            'machine-type',
            'machine-model',
            'machine-serial-number',
        ])
    if options['uri']:
        show_list.extend([
            'object-uri',
        ])

    try:
        print_resources(cmd_ctx, cpcs, cmd_ctx.output_format, show_list,
                        all=options['all'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_cpc_show(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    try:
        cpc.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(cpc.properties)

    # Hide some long or deeply nested properties in table output formats.
    if not options['all'] and cmd_ctx.output_format in TABLE_FORMATS:
        hide_property(properties, 'auto-start-list')
        hide_property(properties, 'available-features-list')
        hide_property(properties, 'cpc-power-saving-state')
        hide_property(properties, 'ec-mcl-description')
        hide_property(properties, 'network1-ipv6-info')
        hide_property(properties, 'network2-ipv6-info')
        hide_property(properties, 'stp-configuration')

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def cmd_cpc_update(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    name_map = {
        'next-activation-profile': 'next-activation-profile-name',
        'processor-time-slice': None,
        'wait-ends-slice': None,
        'no-wait-ends-slice': None,
    }
    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    time_slice = org_options['processor-time-slice']
    if time_slice is None:
        # 'processor-running-time*' properties not changed
        pass
    elif time_slice < 0:
        raise click_exception("Value for processor-time-slice option must "
                              "be >= 0", cmd_ctx.error_format)
    elif time_slice == 0:
        properties['processor-running-time-type'] = 'system-determined'
    else:  # time_slice > 0
        properties['processor-running-time-type'] = 'user-determined'
        properties['processor-running-time'] = time_slice

    if org_options['wait-ends-slice'] is not None:
        properties['does-wait-state-end-time-slice'] = \
            org_options['wait-ends-slice']

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating CPC '{c}'.".
                   format(c=cpc_name))
        return

    try:
        cpc.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()

    # Name changes are not supported for CPCs.
    click.echo("CPC '{c}' has been updated.".format(c=cpc_name))


def cmd_cpc_set_power_save(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    org_options = original_options(options)
    power_saving = org_options['power-saving']
    cpc.set_power_save(power_saving)
    cmd_ctx.spinner.stop()
    click.echo("The power save settings of CPC '{c}' have been set to {s}.".
               format(c=cpc_name, s=power_saving))


def cmd_cpc_set_power_capping(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    org_options = original_options(options)
    power_capping_state = org_options['power-capping-state']
    power_cap_current = None
    if org_options['power-cap-current']:
        power_cap_current = org_options['power-cap-current']
    cpc.set_power_capping(org_options['power-capping-state'], power_cap_current)
    cmd_ctx.spinner.stop()
    click.echo("The power capping settings of CPC '{c}' have been set to {s}.".
               format(c=cpc_name, s=power_capping_state))


def cmd_cpc_get_em_data(cmd_ctx, cpc_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    energy_props = cpc.get_energy_management_properties()
    print_properties(cmd_ctx, energy_props, cmd_ctx.output_format)


def get_auto_start_list(cpc):
    """
    Helper functoin that converts the 'auto-start-list' property of a CPC
    to a list suitable for the zhmcclient.Cpc.set_auto_start_list() method.

    Returns:
        None - if the CPC is in classic mode
        list, with items that are one of:
          - tuple(partition, post_start_delay)
          - tuple(partition_list, name, description, post_start_delay)
    """
    auto_start_list = cpc.prop('auto-start-list', None)
    if auto_start_list is None:
        # CPC is in classic mode
        return None

    as_list = []
    for auto_start_item in auto_start_list:
        if auto_start_item['type'] == 'partition':
            # item is a partition
            uri = auto_start_item['partition-uri']
            delay = auto_start_item['post-start-delay']
            partition = cpc.partitions.resource_object(uri)
            as_item = (partition, delay)
            as_list.append(as_item)
        if auto_start_item['type'] == 'partition-group':
            # item is a partition group
            name = auto_start_item['name']
            description = auto_start_item['description']
            delay = auto_start_item['post-start-delay']
            partitions = []
            for uri in auto_start_item['partition-uris']:
                partition = cpc.partitions.resource_object(uri)
                partitions.append(partition)
            as_item = (partitions, name, description, delay)
            as_list.append(as_item)
    return as_list


def auto_start_table_str(as_list, output_format):
    """
    Return a string with the auto-start list table in the specified output
    format.
    """
    headers = ['Partition/Group', 'Post start delay', 'Partitions in group',
               'Group description']
    table = []
    for as_item in as_list:
        if isinstance(as_item[0], zhmcclient.Partition):
            # item is a partition
            partition, delay = as_item
            row = [partition.name, delay]
            table.append(row)
        else:
            # item is a partition group
            partitions, name, description, delay = as_item
            partition_names = ', '.join([p.name for p in partitions])
            row = [name, delay, partition_names, description]
            table.append(row)
    table_str = tabulate(table, headers, tablefmt=output_format)
    return table_str


def cmd_cpc_autostart_show(cmd_ctx, cpc_name):
    # pylint: disable=missing-function-docstring
    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    as_list = get_auto_start_list(cpc)

    if as_list is None:
        # The HMC WS API book documents that only CPCs in DPM mode have
        # the 'auto-start-list' property.
        cmd_ctx.spinner.stop()
        click.echo("CPC '{c}' is in classic mode and has no auto-start list.".
                   format(c=cpc_name))
        return

    table_str = auto_start_table_str(as_list, cmd_ctx.output_format)
    cmd_ctx.spinner.stop()
    click.echo(table_str)


def cmd_cpc_autostart_add(cmd_ctx, cpc_name, partitions_delay, options):
    # pylint: disable=missing-function-docstring
    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)
    partition_names, delay = partitions_delay

    # pylint: disable=import-outside-toplevel,cyclic-import
    from ._cmd_partition import find_partition

    as_list = get_auto_start_list(cpc)

    if as_list is None:
        # The HMC WS API book documents that only CPCs in DPM mode have
        # the 'auto-start-list' property.
        cmd_ctx.spinner.stop()
        click.echo("CPC '{c}' is in classic mode and has no auto-start list.".
                   format(c=cpc_name))
        return

    group_name = options['group']
    if group_name:
        # A partition group is added (with one or more partitions)
        partition_names = partition_names.split(',')
        partitions = []
        for partition_name in partition_names:
            partition = find_partition(cmd_ctx, client, cpc, partition_name)
            partitions.append(partition)
        description = options['description']
        new_as_item = (partitions, group_name, description, delay)
    else:
        # A partition is added
        partition_name = partition_names
        partition = find_partition(cmd_ctx, client, cpc, partition_name)
        new_as_item = (partition, delay)

    # TODO: Add support for --before and --after
    as_list.append(new_as_item)
    try:
        cpc.set_auto_start_list(as_list)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    table_str = auto_start_table_str(as_list, cmd_ctx.output_format)
    cmd_ctx.spinner.stop()
    click.echo(table_str)


def cmd_cpc_autostart_delete(cmd_ctx, cpc_name, partition_or_group):
    # pylint: disable=missing-function-docstring
    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    as_list = get_auto_start_list(cpc)

    if as_list is None:
        # The HMC WS API book documents that only CPCs in DPM mode have
        # the 'auto-start-list' property.
        cmd_ctx.spinner.stop()
        click.echo("CPC '{c}' is in classic mode and has no auto-start list.".
                   format(c=cpc_name))
        return

    as_item_idx = None
    for i, as_item in enumerate(as_list):
        if isinstance(as_item[0], zhmcclient.Partition):
            # item is a partition
            partition = as_item[0]
            if partition.name == partition_or_group:
                as_item_idx = i
                break
        else:
            # item is a partition group
            name = as_item[1]
            if name == partition_or_group:
                as_item_idx = i
                break

    if as_item_idx is None:
        raise click_exception(
            "Could not find partition or group '{p}' in CPC '{c}'.'".
            format(p=partition_or_group, c=cpc_name),
            cmd_ctx.error_format)

    del as_list[as_item_idx]
    try:
        cpc.set_auto_start_list(as_list)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    table_str = auto_start_table_str(as_list, cmd_ctx.output_format)
    cmd_ctx.spinner.stop()
    click.echo(table_str)


def cmd_cpc_autostart_clear(cmd_ctx, cpc_name):
    # pylint: disable=missing-function-docstring
    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    as_list = []
    try:
        cpc.set_auto_start_list(as_list)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Auto-start list for CPC '{c}' has been cleared.".
               format(c=cpc_name))
