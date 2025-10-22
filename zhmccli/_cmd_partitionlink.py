# Copyright 2025 IBM Corp. All Rights Reserved.
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
Commands for partition links in DPM mode.
"""


import click
from click_option_group import optgroup

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS, FILTER_OPTIONS, \
    build_filter_args, SORT_OPTIONS, build_sort_props, ALL_PARTITION_STATUSES
from ._cmd_cpc import find_cpc, find_cpc_by_uri
from ._cmd_adapter import find_adapter_by_uri


# Defaults for partition link creation
PARTITIONLINK_TYPES = ['hipersockets', 'smc-d']  # 'ctc' is not yet supported
DEFAULT_PARTITIONLINK_TYPE = 'hipersockets'
DEFAULT_SMCD_STARTING_FID = 4096
DEFAULT_HS_STARTING_DEVNO = 7400
DEFAULT_HS_MTU_SIZE = 8
# DEFAULT_CTC_DEVICES_PER_PATH = 4


def find_partitionlink(cmd_ctx, client, partitionlink_name):
    """
    Find a partition link by name and return its resource object.
    """
    console = client.consoles.console
    try:
        partitionlink = console.partition_links.find(name=partitionlink_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    return partitionlink


@cli.group('partitionlink', options_metavar=COMMAND_OPTIONS_METAVAR)
def partitionlink_group():
    """
    Command group for managing partition links (DPM mode only).

    The commands in this group work only on CPCs that are in DPM mode.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@partitionlink_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='[CPC]', required=False)
@add_options(LIST_OPTIONS)
@add_options(FILTER_OPTIONS)
@add_options(SORT_OPTIONS)
@click.pass_obj
def partitionlink_list(cmd_ctx, cpc, **options):
    """
    List the partition links associated with a CPC, or all partition links.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_partitionlink_list(cmd_ctx, cpc, options))


@partitionlink_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('PARTITIONLINK', type=str, metavar='PARTITIONLINK')
@click.pass_obj
def partitionlink_show(cmd_ctx, partitionlink):
    # pylint: disable=line-too-long
    """
    Show the details of a partition link.

    The following properties are shown in addition to those returned by the HMC:

    \b
      - 'adapter-name' - Name of the backing adapter, for SMC-D and Hipersocket.
      - 'bus-connections.nics.nic-name' - Names of the NICs, for SMC-D and Hipersocket.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """  # noqa: E501
    cmd_ctx.execute_cmd(
        lambda: cmd_partitionlink_show(cmd_ctx, partitionlink))


@partitionlink_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@optgroup.group('General options')
@optgroup.option('--name', type=str, required=True,
                 help='The name of the new partition link.')
@optgroup.option('--type', type=click.Choice(PARTITIONLINK_TYPES),
                 required=False, default=DEFAULT_PARTITIONLINK_TYPE,
                 help='The type of the new partition link. Default: {d}'.
                 format(d=DEFAULT_PARTITIONLINK_TYPE))
@optgroup.option('--description', type=str, required=False,
                 help='The description of the new partition link.')
@optgroup.group('For type=hipersockets')
@optgroup.option('--starting-devno', type=str, required=False,
                 help='The starting number for the device number assignment, '
                 'acting as a default. If no device number for a NIC is '
                 'provided when adding a partition, the next available '
                 'device number starting from this value will be used. '
                 'Default: {d}'.format(d=DEFAULT_HS_STARTING_DEVNO))
@optgroup.option('--mtu-size', type=int, required=False,
                 help='The maximum transmission unit (MTU) size of the '
                 'Hipersockets adapter that will be created. The maximum frame '
                 'size is implied by this value. Valid values are: '
                 '8 - 8 KB MTU size and 16 KB maximum frame size; '
                 '16 - 16 KB MTU size and 24 KB maximum frame size; '
                 '32 - 32 KB MTU size and 40 KB maximum frame size; '
                 '56 - 56 KB MTU size and 64 KB maximum frame size. '
                 'Default: {d}'.format(d=DEFAULT_HS_MTU_SIZE))
@optgroup.group('For type=smc-d')
@optgroup.option('--starting-fid', type=int, required=False,
                 help='The starting number for the Functional ID (FID) '
                 'assignment, acting as a default. If no FID for a NIC is '
                 'provided when adding a partition, the next available FID '
                 'starting from this value will be used. '
                 'Default: {d}'.format(d=DEFAULT_SMCD_STARTING_FID))
# @optgroup.group('For type=ctc')
# @optgroup.option('--devices-per-path', type=int, required=False,
#                  help='The number of devices to be created per path when '
#                  'adding a partition. '
#                  'Default: {d}'.format(d=DEFAULT_CTC_DEVICES_PER_PATH))
@click.pass_obj
def partitionlink_create(cmd_ctx, cpc, **options):
    """
    Create a partition link associated with a CPC.

    This command cannot be used to have partitions attached to the new
    partition link.

    This command supports only the creation of partitions links of type SMC-D
    and Hipersockets; type CTC is not supported.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_partitionlink_create(cmd_ctx, cpc, options))


@partitionlink_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('PARTITIONLINK', type=str, metavar='PARTITIONLINK')
@optgroup.group('General options')
@optgroup.option('--name', type=str, required=False,
                 help='The new name of the partition link.')
@optgroup.option('--description', type=str, required=False,
                 help='The new description of the partition link.')
@optgroup.group('For type=hipersockets')
@optgroup.option('--starting-devno', type=str, required=False,
                 help='The new starting number for the device number '
                 'assignment, acting as a default. If no device number for a '
                 'NIC is provided when adding a partition, the next available '
                 'device number starting from this value will be used.')
@optgroup.option('--mtu-size', type=int, required=False,
                 help='The new maximum transmission unit (MTU) size for the '
                 'Hipersockets adapter. The maximum frame '
                 'size is implied by this value. Valid values are: '
                 '8 - 8 KB MTU size and 16 KB maximum frame size; '
                 '16 - 16 KB MTU size and 24 KB maximum frame size; '
                 '32 - 32 KB MTU size and 40 KB maximum frame size; '
                 '56 - 56 KB MTU size and 64 KB maximum frame size.')
@optgroup.group('For type=smc-d')
@optgroup.option('--starting-fid', type=int, required=False,
                 help='The new starting number for the Functional ID (FID) '
                 'assignment, acting as a default. If no FID for a NIC is '
                 'provided when adding a partition, the next available FID '
                 'starting from this value will be used.')
# @optgroup.group('For type=ctc')
# @optgroup.option('--devices-per-path', type=int, required=False,
#                  help='Number of devices to be created per path when adding '
#                  'a partition. '
#                  'Default: {d}'.format(d=DEFAULT_CTC_DEVICES_PER_PATH))
@click.pass_obj
def partitionlink_update(cmd_ctx, partitionlink, **options):
    """
    Update the properties of a partition link.

    This command cannot be used to attach or detach partitions to or from
    a partition link.

    The partition link type and the associated CPC cannot be changed once a
    partition link has been created.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_partitionlink_update(cmd_ctx, partitionlink, options))


@partitionlink_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('PARTITIONLINK', type=str, metavar='PARTITIONLINK')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the partition link.',
              prompt='Are you sure you want to delete this partition link ?')
@click.pass_obj
def partitionlink_delete(cmd_ctx, partitionlink):
    """
    Delete a partition link.

    For Hipersocket partition links, this will cause the NICs that belong to
    the partition link to be deleted in the linked partitions.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_partitionlink_delete(cmd_ctx, partitionlink))


@partitionlink_group.command(
    'list-partitions', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('PARTITIONLINK', type=str, metavar='PARTITIONLINK')
@add_options(LIST_OPTIONS)
@click.option('--name', type=str, required=False,
              help="Regular expression filter to limit the returned partitions "
              "to those with a matching name.")
@click.option('--status', type=str, required=False,
              help="Filter to limit the returned partitions to those with a "
              "matching status. Valid status values are: {sv}.".
              format(sv=', '.join(ALL_PARTITION_STATUSES)))
@add_options(SORT_OPTIONS)
@click.pass_obj
def partitionlink_list_partitions(cmd_ctx, partitionlink, **options):
    """
    List the partitions attached to a partition link.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_partitionlink_list_partitions(
            cmd_ctx, partitionlink, options))


@partitionlink_group.command(
    'attach-partition', options_metavar=COMMAND_OPTIONS_METAVAR,
    hidden=True)  # TODO: Implement in zhmcclient
@click.argument('PARTITIONLINK', type=str, metavar='PARTITIONLINK')
@click.option('--partition', type=str, required=True,
              help='The name of the partition.')
@click.pass_obj
def partitionlink_attach_partition(cmd_ctx, partitionlink, **options):
    """
    Attach a partition to a partition link.

    For Hipersocket partition links, this will cause one or more NICs to be
    created in the attached partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_partitionlink_attach_partition(
            cmd_ctx, partitionlink, options))


@partitionlink_group.command(
    'detach-partition', options_metavar=COMMAND_OPTIONS_METAVAR,
    hidden=True)  # TODO: Implement in zhmcclient
@click.argument('PARTITIONLINK', type=str, metavar='PARTITIONLINK')
@click.option('--partition', type=str, required=True,
              help='The name of the partition.')
@click.pass_obj
def partitionlink_detach_partition(cmd_ctx, partitionlink, **options):
    """
    Detach a partition from a partition link.

    For Hipersocket partition links, this will cause the NICs that belong to
    the partition link to be deleted in the detached partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_partitionlink_detach_partition(
            cmd_ctx, partitionlink, options))


def cmd_partitionlink_list(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    show_list = [
        'cpc',
        'name',
    ]
    if not options['names_only']:
        show_list.extend([
            'type',
            'state',
            'description',
        ])
    if options['uri']:
        show_list.extend([
            'object-uri',
        ])
    # TODO: Add adapter-name in case of --all
    # if options['all']:
    #     show_list.extend([
    #         'adapter-name',
    #     ])

    # Make sure to include only properties in additional properties
    # that are known resource properties and are not included in the
    # default set of properties for a list operation.
    standard_props = ['cpc', 'name', 'type', 'state', 'object-uri']
    additional_props = [p for p in show_list if p not in standard_props]

    filter_args = build_filter_args(cmd_ctx, options['filter'])

    if cpc_name:  # None if not specified
        cpc = find_cpc(cmd_ctx, client, cpc_name)
        if filter_args is None:
            filter_args = {}
        filter_args['cpc-uri'] = cpc.uri

    try:
        partitionlinks = console.partition_links.list(
            additional_properties=additional_props, filter_args=filter_args)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    # Prepare the additions dict of dicts. It contains additional
    # (=non-resource) property values by property name and by resource URI.
    additions = {}
    updates = {}

    # Add artificial property 'cpc':
    additions['cpc'] = {}
    for pl in partitionlinks:
        cpc_uri = pl.get_property('cpc-uri')
        cpc = find_cpc_by_uri(cmd_ctx, client, cpc_uri)
        additions['cpc'][pl.uri] = cpc.name

    if options['all']:
        additions['adapter-name'] = {}
        updates['bus-connections'] = {}
        for pl in partitionlinks:

            # Add artificial property 'adapter-name':
            adapter_uri = pl.prop('adapter-uri', None)
            if adapter_uri:  # Exists only for SMC-D and Hipersocket type
                cpc_uri = pl.get_property('cpc-uri')
                cpc = find_cpc_by_uri(cmd_ctx, client, cpc_uri)
                adapter = find_adapter_by_uri(cmd_ctx, cpc, adapter_uri)
                additions['adapter-name'][pl.uri] = adapter.name

            # Add artificial property 'nic-name' in 'bus-connections.nics':
            bc_list = pl.prop('bus-connections', None)
            if bc_list:  # Exists only for SMC-D and Hipersocket type
                updates_bc_list = []
                for bc_item in bc_list:
                    nic_items = bc_item['nics']
                    updates_nics = []
                    for nic_item in nic_items:
                        nic_uri = nic_item['nic-uri']
                        nic_props = client.session.get(nic_uri)
                        updates_nics.append({'nic-name': nic_props['name']})
                    updates_bc_list.append({'nics': updates_nics})
                updates['bus-connections'][pl.uri] = updates_bc_list

    sort_props = build_sort_props(cmd_ctx, options['sort'],
                                  default=['cpc', 'name'])

    try:
        print_resources(
            cmd_ctx, partitionlinks, cmd_ctx.output_format, show_list,
            additions, all=options['all'], sort_props=sort_props,
            updates=updates)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_partitionlink_show(cmd_ctx, partitionlink_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    partitionlink = find_partitionlink(cmd_ctx, client, partitionlink_name)

    try:
        partitionlink.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(partitionlink.properties)

    # Add artificial property 'adapter-name':
    adapter_uri = properties.get('adapter-uri', None)
    if adapter_uri:  # Exists only for SMC-D and Hipersocket type
        cpc_uri = properties['cpc-uri']
        cpc = find_cpc_by_uri(cmd_ctx, client, cpc_uri)
        adapter = find_adapter_by_uri(cmd_ctx, cpc, adapter_uri)
        properties['adapter-name'] = adapter.name

    # Add artificial property 'nic-name' in 'bus-connections.nics':
    bc_list = properties.get('bus-connections', None)
    if bc_list:  # Exists only for SMC-D and Hipersocket type
        for bc_item in bc_list:
            nic_items = bc_item['nics']
            for nic_item in nic_items:
                nic_uri = nic_item['nic-uri']
                nic_props = client.session.get(nic_uri)
                nic_item['nic-name'] = nic_props['name']

    # # Hide some long or deeply nested properties in table output formats.
    # if not options['all'] and cmd_ctx.output_format in TABLE_FORMATS:
    #     hide_property(properties, 'xxxxxxxxx')

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def cmd_partitionlink_create(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    name_map = {
        'starting-devno': 'starting-device-number',
        'mtu-size': 'maximum-transmission-unit-size',
    }

    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    properties['cpc-uri'] = cpc.uri

    try:
        new_partitionlink = console.partition_links.create(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("New partition link '{p}' has been created.".
               format(p=new_partitionlink.properties['name']))


def cmd_partitionlink_update(cmd_ctx, partitionlink_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    partitionlink = find_partitionlink(cmd_ctx, client, partitionlink_name)

    name_map = {
        'starting-devno': 'starting-device-number',
        'mtu-size': 'maximum-transmission-unit-size',
    }

    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating partition link '{p}'.".
                   format(p=partitionlink_name))
        return

    try:
        partitionlink.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    if 'name' in properties and properties['name'] != partitionlink_name:
        click.echo("Partition link '{pl}' has been renamed to '{pln}' and was "
                   "updated.".
                   format(pl=partitionlink_name, pln=properties['name']))
    else:
        click.echo(f"Partition link '{partitionlink_name}' has been updated.")


def cmd_partitionlink_delete(cmd_ctx, partitionlink_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    partitionlink = find_partitionlink(cmd_ctx, client, partitionlink_name)

    try:
        partitionlink.delete()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo(f"Partition link '{partitionlink_name}' has been deleted.")


def cmd_partitionlink_list_partitions(cmd_ctx, partitionlink_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    partitionlink = find_partitionlink(cmd_ctx, client, partitionlink_name)

    show_list = [
        'cpc',
        'name',
    ]
    if not options['names_only']:
        show_list.extend([
            'type',
            'status',
            'description',
            'nics',
        ])
    if options['uri']:
        show_list.extend([
            'object-uri',
        ])

    name_filter = options['name']
    status_filter = options['status']
    try:
        partitions = partitionlink.list_attached_partitions(
            name=name_filter, status=status_filter)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    # Prepare the additions dict of dicts. It contains additional
    # (=non-resource) property values by property name and by resource URI.
    additions = {}

    # Add artificial property 'cpc':
    additions['cpc'] = {}
    for p in partitions:
        cpc = p.manager.parent
        additions['cpc'][p.uri] = cpc.name

    if partitionlink.get_property('type') in ('smc-d', 'hipersockets'):
        # Add artificial property 'nics':
        additions['nics'] = {}
        for p in partitions:
            bc_list = partitionlink.get_property('bus-connections')
            for bc_item in bc_list:
                if bc_item['partition-name'] == p.name:
                    nic_items = bc_item['nics']
                    additions['nics'][p.uri] = []
                    for nic_item in nic_items:
                        nic_uri = nic_item['nic-uri']
                        nic_props = client.session.get(nic_uri)
                        additions['nics'][p.uri].append(nic_props['name'])

    sort_props = build_sort_props(cmd_ctx, options['sort'],
                                  default=['cpc', 'name'])

    try:
        print_resources(
            cmd_ctx, partitions, cmd_ctx.output_format, show_list,
            additions, all=options['all'], sort_props=sort_props)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_partitionlink_attach_partition(cmd_ctx, partitionlink_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    partitionlink = find_partitionlink(cmd_ctx, client, partitionlink_name)

    cpc_uri = partitionlink.get_property('cpc-uri')
    cpc = client.cpcs.find(**{'object-uri': cpc_uri})

    partition_name = options['partition']  # Required
    try:
        partition = cpc.partitions.find(name=partition_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    try:
        partitionlink.attach_partition(partition)  # TODO: Implement
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Partition '{p}' was attached to partition link '{pl}'.".
               format(p=partition_name, pl=partitionlink.name))


def cmd_partitionlink_detach_partition(cmd_ctx, partitionlink_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    partitionlink = find_partitionlink(cmd_ctx, client, partitionlink_name)

    cpc_uri = partitionlink.get_property('cpc-uri')
    cpc = client.cpcs.find(**{'object-uri': cpc_uri})

    partition_name = options['partition']  # Required
    try:
        partition = cpc.partitions.find(name=partition_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    try:
        partitionlink.detach_partition(partition)  # TODO: Implement
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Partition '{p}' was detached from partition link '{pl}'.".
               format(p=partition_name, pl=partitionlink.name))
