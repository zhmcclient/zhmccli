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
Commands for NICs.
"""

from __future__ import absolute_import

import click

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS
from ._cmd_partition import find_partition


# Defaults for NIC creation
SSC_IP_ADDRESS_TYPES = ['ipv4', 'ipv6', 'linklocal', 'dhcp']


def find_nic(cmd_ctx, client, cpc_or_name, partition_name, nic_name):
    """
    Find a NIC by name and return its resource object.
    """
    partition = find_partition(cmd_ctx, client, cpc_or_name, partition_name)
    try:
        nic = partition.nics.find(name=nic_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return nic


@cli.group('nic', options_metavar=COMMAND_OPTIONS_METAVAR)
def nic_group():
    """
    Command group for managing NICs (DPM mode only).

    The commands in this group work only on CPCs that are in DPM mode.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@nic_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.option('--type', is_flag=True, required=False, hidden=True)
@add_options(LIST_OPTIONS)
@click.pass_obj
def nic_list(cmd_ctx, cpc, partition, **options):
    """
    List the NICs in a partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_nic_list(cmd_ctx, cpc, partition, options))


@nic_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.argument('NIC', type=str, metavar='NIC')
@click.pass_obj
def nic_show(cmd_ctx, cpc, partition, nic):
    """
    Show the details of a NIC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_nic_show(cmd_ctx, cpc, partition, nic))


@nic_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.option('--name', type=str, required=True,
              help='The name of the new NIC.')
@click.option('--description', type=str, required=False,
              help='The description of the new NIC. '
              'Default: empty')
@click.option('--adapter', type=str, required=False,
              help='The name of the network adapter with the port backing the '
              'new NIC. Required.')
@click.option('--port', type=str, required=False,
              help='The name or index of the network port backing the new NIC. '
              'Required.')
@click.option('--virtual-switch', type=str, required=False,
              help='Deprecated: The name of the virtual switch of the network '
              'port backing the new NIC. Use --adapter and --port instead.')
@click.option('--device-number', type=str, required=False,
              help='The device number to be used for the new NIC. '
              'Default: auto-generated')
@click.option('--ssc-management-nic', type=bool, required=False,
              help='Indicates that this NIC should be used as a management '
              'NIC for Secure Service Container to access the web interface. '
              'Only applicable to NICs of ssc type partitions. '
              'Default: False')
@click.option('--ssc-ip-address-type', type=click.Choice(SSC_IP_ADDRESS_TYPES),
              required=False,
              help='Secure Service Container IP address type. '
              'Only applicable to and required for NICs of '
              'ssc type partitions.')
@click.option('--ssc-ip-address', type=str, required=False,
              help='IP Address of the SSC management web interface. '
              'Only applicable to and required for NICs of ssc type '
              'partitions when ssc-ip-address-type is ipv4 or ipv6.')
@click.option('--ssc-mask-prefix', type=str, required=False,
              help='Network Mask of the SSC management NIC. '
              'Only applicable to and required for NICs of ssc type '
              'partitions when ssc-ip-address-type is ipv4 or ipv6.')
@click.option('--vlan-id', type=str, required=False,
              help='VLAN ID of the SSC management NIC. '
              'Empty string sets no VLAN ID. '
              'Only applicable to NICs of ssc type partitions. '
              'Default: No VLAN ID')
@click.pass_obj
def nic_create(cmd_ctx, cpc, partition, **options):
    """
    Create a NIC in a partition.

    The NIC is backed by a port (jack) on an adapter. For all types of network
    adapters, the backing adapter and port can be specified with the --adapter
    and --port options. The --virtual-switch option is deprecated but still
    supported for compatibility; it can be used only for OSA and HiperSocket
    adapters.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_nic_create(cmd_ctx, cpc, partition,
                                               options))


@nic_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.argument('NIC', type=str, metavar='NIC')
@click.option('--name', type=str, required=False,
              help='The new name of the NIC.')
@click.option('--description', type=str, required=False,
              help='The new description of the NIC.')
@click.option('--adapter', type=str, required=False,
              help='The name of the network adapter with the port backing the '
              'NIC. Required.')
@click.option('--port', type=str, required=False,
              help='The name or index of the network port backing the NIC. '
              'Required.')
@click.option('--virtual-switch', type=str, required=False,
              help='Deprecated: The name of the virtual switch of the network '
              'port backing the NIC. Use --adapter and --port instead.')
@click.option('--device-number', type=str, required=False,
              help='The new device number to be used for the NIC.')
@click.option('--ssc-management-nic', type=bool, required=False,
              help='Indicates that this NIC should be used as a management '
              'NIC for Secure Service Container to access the web interface. '
              'Only applicable to NICs of ssc type partitions. ')
@click.option('--ssc-ip-address-type', type=click.Choice(SSC_IP_ADDRESS_TYPES),
              required=False,
              help='Secure Service Container IP address type. '
              'Only applicable to NICs of ssc type partitions.')
@click.option('--ssc-ip-address', type=str, required=False,
              help='IP Address of the SSC management web interface. '
              'Only applicable to NICs of ssc type partitions.')
@click.option('--ssc-mask-prefix', type=str, required=False,
              help='Network Mask of the SSC management NIC. '
              'Only applicable to NICs of ssc type partitions.')
@click.option('--vlan-id', type=str, required=False,
              help='VLAN ID of the SSC management NIC. '
              'Empty string sets no VLAN ID. '
              'Only applicable to NICs of ssc type partitions.')
@click.pass_obj
def nic_update(cmd_ctx, cpc, partition, nic, **options):
    """
    Update the properties of a NIC.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_nic_update(cmd_ctx, cpc, partition, nic,
                                               options))


@nic_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.argument('NIC', type=str, metavar='NIC')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the NIC.',
              prompt='Are you sure you want to delete this NIC ?')
@click.pass_obj
def nic_delete(cmd_ctx, cpc, partition, nic):
    """
    Delete a NIC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_nic_delete(cmd_ctx, cpc, partition, nic))


def backing_uri(cmd_ctx, cpc, org_options, required=False):
    """
    Determine the backing adapter port or vswitch to be used from the
    --adapter, --port, and --virtual-switch options, and return a dict with the
    correct property for the URI of the backing port or vswitch to be used for
    the "Create NIC" operation.

    Returns:
      dict with the backing URI property set, if backing object specified
      None, if no backing object specified and not required

    Raises:
      click exception for various error situations.
    """

    if org_options['virtual-switch']:
        # This option is deprecated, but it is still supported for
        # backwards compatibility.

        if org_options['adapter'] or org_options['port']:
            raise click_exception(
                "The (deprecated) --virtual-switch option must not be "
                "specified together with any of the --adapter or --port "
                "options.",
                cmd_ctx.error_format)

        vswitch_name = org_options['virtual-switch']
        try:
            vswitch = cpc.virtual_switches.find(name=vswitch_name)
        except zhmcclient.NotFound:
            raise click_exception(
                "Could not find virtual switch '{s}' in CPC '{c}'.".
                format(s=vswitch_name, c=cpc.name),
                cmd_ctx.error_format)
        return {'virtual-switch-uri': vswitch.uri}

    if bool(org_options['adapter']) != bool(org_options['port']):
        raise click_exception(
            "The --adapter and --port options must be specified both or none.",
            cmd_ctx.error_format)

    if org_options['adapter']:
        adapter_name = org_options['adapter']
    else:
        if required:
            raise click_exception(
                "Required --adapter option is not specified",
                cmd_ctx.error_format)
        return None

    if org_options['port']:
        port_name = org_options['port']
    else:
        if required:
            raise click_exception(
                "Required --port option is not specified",
                cmd_ctx.error_format)
        return None

    try:
        adapter = cpc.adapters.find(name=adapter_name)
    except zhmcclient.NotFound:
        raise click_exception(
            "Could not find adapter '{a}' in CPC '{c}'.".
            format(a=adapter_name, c=cpc.name),
            cmd_ctx.error_format)

    try:
        port = adapter.ports.find(name=port_name)
    except zhmcclient.NotFound:
        # Try interpreting the --port value as a port index
        try:
            port_index = int(port_name)
        except ValueError:
            raise click_exception(
                "Could not find port with name '{p}' on "
                "adapter '{a}' in CPC '{c}'.".
                format(p=port_name, a=adapter_name, c=cpc.name),
                cmd_ctx.error_format)
        try:
            port = adapter.ports.find(index=port_index)
        except zhmcclient.NotFound:
            raise click_exception(
                "Could not find port with name or index '{p}' on "
                "adapter '{a}' in CPC '{c}'.".
                format(p=port_name, a=adapter_name, c=cpc.name),
                cmd_ctx.error_format)

    adapter_type = adapter.get_property('type')
    if adapter_type in ('roce', 'cna'):
        return {'network-adapter-port-uri': port.uri}

    if adapter_type in ('osd', 'hipersockets'):
        port_index = port.get_property('index')
        filter_args = {
            'backing-adapter-uri': adapter.uri,
            'port': port_index,
        }
        try:
            vswitch = cpc.virtual_switches.find(**filter_args)
        except zhmcclient.NotFound:
            raise click_exception(
                "Could not find virtual switch with backing adapter '{a}' "
                "and port index '{p}' in CPC '{c}'.".
                format(a=adapter.name, p=port_index, c=cpc.name),
                cmd_ctx.error_format)
        return {'virtual-switch-uri': vswitch.uri}

    raise click_exception(
        "Adapter '{a}' on CPC '{c}' has unsupported type {t} for "
        "being a backing adapter of a NIC.".
        format(a=adapter_name, c=cpc.name, t=adapter_type),
        cmd_ctx.error_format)


def cmd_nic_list(cmd_ctx, cpc_name, partition_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    try:
        nics = partition.nics.list()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    if options['type']:
        click.echo("The --type option is deprecated and type information "
                   "is now always shown.")

    show_list = [
        'name',
        'cpc',
        'partition',
    ]
    if not options['names_only']:
        show_list.extend([
            'type',
        ])
    if options['uri']:
        show_list.extend([
            'element-uri',
        ])

    cpc_additions = {}
    partition_additions = {}
    for nic in nics:
        cpc_additions[nic.uri] = cpc_name
        partition_additions[nic.uri] = partition_name
    additions = {
        'cpc': cpc_additions,
        'partition': partition_additions,
    }

    try:
        print_resources(cmd_ctx, nics, cmd_ctx.output_format, show_list,
                        additions, all=options['all'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_nic_show(cmd_ctx, cpc_name, partition_name, nic_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    nic = find_nic(cmd_ctx, client, cpc_name, partition_name, nic_name)

    try:
        nic.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    print_properties(cmd_ctx, nic.properties, cmd_ctx.output_format)


def cmd_nic_create(cmd_ctx, cpc_name, partition_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    name_map = {
        # The following options are handled in this function:
        'adapter': None,
        'port': None,
        'virtual-switch': None,
    }
    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    set_vlan_id(cmd_ctx, properties, org_options)

    properties.update(backing_uri(
        cmd_ctx, partition.manager.cpc, org_options, required=True))

    try:
        new_nic = partition.nics.create(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("New NIC '{n}' has been created.".
               format(n=new_nic.properties['name']))


def cmd_nic_update(cmd_ctx, cpc_name, partition_name, nic_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    nic = find_nic(cmd_ctx, client, cpc_name, partition_name, nic_name)

    name_map = {
        # The following options are handled in this function:
        'adapter': None,
        'port': None,
        'virtual-switch': None,
    }
    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    set_vlan_id(cmd_ctx, properties, org_options)

    uri_prop = backing_uri(
        cmd_ctx, nic.manager.partition.manager.cpc, org_options)
    if uri_prop:
        properties.update(uri_prop)

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating NIC '{n}'.".
                   format(n=nic_name))
        return

    try:
        nic.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    if 'name' in properties and properties['name'] != nic_name:
        click.echo("NIC '{n}' has been renamed to '{nn}' and was updated.".
                   format(n=nic_name, nn=properties['name']))
    else:
        click.echo("NIC '{n}' has been updated.".format(n=nic_name))


def cmd_nic_delete(cmd_ctx, cpc_name, partition_name, nic_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    nic = find_nic(cmd_ctx, client, cpc_name, partition_name, nic_name)

    try:
        nic.delete()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("NIC '{n}' has been deleted.".format(n=nic_name))


def set_vlan_id(cmd_ctx, properties, org_options):
    """
    Set the 'vlan-id' property from the options.
    """
    vlan_id = org_options['vlan-id']
    if vlan_id == '':
        properties['vlan-id'] = None
    else:
        try:
            properties['vlan-id'] = int(vlan_id)
        except ValueError:
            raise click_exception(
                "Invalid value for '--vlan-id': {} is not a valid integer".
                format(vlan_id), cmd_ctx.error_format)
