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
Commands for adapters.
"""

from __future__ import absolute_import

import time
import re
from datetime import datetime
import click

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS
from ._cmd_cpc import find_cpc


# Mapping of --crypto-type option values to crypto-type adapter property values
CRYPTO_TYPE_PROPERTIES = {
    'acc': 'accelerator',
    'cca': 'cca-coprocessor',
    'ep11': 'ep11-coprocessor',
}

# List of --crypto-type option values
CRYPTO_TYPE_OPTIONS = sorted(list(CRYPTO_TYPE_PROPERTIES.keys()))

# Default crypto adapter name patterns
CRYPTO_DEFAULT_NAMES = re.compile(
    r"^(Accel|CCA|EP11) [0-9A-F]{4} [0-9A-F]{4}-[0-9]{2}$")

# Mapping of --storage-type option values to type adapter property values
STORAGE_TYPE_PROPERTIES = {
    'fcp': 'fcp',
    'fc': 'fc',
    'not-configured': 'not-configured',
}

# List of --storage-type option values
STORAGE_TYPE_OPTIONS = sorted(list(STORAGE_TYPE_PROPERTIES.keys()))


def find_adapter(cmd_ctx, client, cpc_or_name, adapter_name):
    """
    Find an adapter by name and return its resource object.
    """
    if isinstance(cpc_or_name, zhmcclient.Cpc):
        cpc = cpc_or_name
    else:
        cpc = find_cpc(cmd_ctx, client, cpc_or_name)
    # The CPC must be in DPM mode. We don't check that because it would
    # cause a GET to the CPC resource that we otherwise don't need.
    try:
        adapter = cpc.adapters.find(name=adapter_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return adapter


@cli.group('adapter', options_metavar=COMMAND_OPTIONS_METAVAR)
def adapter_group():
    """
    Command group for managing adapters (DPM mode only).

    Physical adapters (e.g. OSA, FICON) are auto-discovered and cannot be
    created. Logical adapters (HiperSockets) can be created and deleted.

    The commands in this group work only on CPCs in DPM mode.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@adapter_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.option('--type', is_flag=True, required=False, hidden=True)
@add_options(LIST_OPTIONS)
@click.pass_obj
def adapter_list(cmd_ctx, cpc, **options):
    """
    List the adapters in a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_adapter_list(cmd_ctx, cpc, options))


@adapter_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('ADAPTER', type=str, metavar='ADAPTER')
@click.pass_obj
def adapter_show(cmd_ctx, cpc, adapter):
    """
    Show the details of an adapter.

    The following properties are shown in addition to those returned by the HMC:

    \b
      - 'parent-name' - Name of the parent CPC.
      - 'network-port-names' - Names of the Adapter Ports referenced by
        'network-port-uris' if present (for network adapters, index-correlated).
      - 'network-port-indexes' - Indexes of the Adapter Ports referenced by
        'network-port-uris' if present (for network adapters, index-correlated).
      - 'storage-port-names' - Names of the Adapter Ports referenced by
        'storage-port-uris' if present (for storage adapters, index-correlated).
      - 'storage-port-indexes' - Indexes of the Adapter Ports referenced by
        'storage-port-uris' if present (for storage adapters, index-correlated).

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_adapter_show(cmd_ctx, cpc, adapter))


@adapter_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('ADAPTER', type=str, metavar='ADAPTER')
@click.option('--name', type=str, required=False,
              help='The new name of the adapter.')
@click.option('--description', type=str, required=False,
              help='The new description of the adapter.')
@click.option('--port-description', type=str, required=False,
              help='The new description of the single port of the adapter.')
@click.option('--mtu-size', type=click.Choice(['8', '16', '32', '56']),
              required=False,
              help='The new MTU size of the adapter in KiB. '
              '(HiperSockets only).')
@click.option('--allowed-capacity', type=int, required=False,
              help='The new maximum number of HBAs per partition. '
              '(only certain adapter types).')
@click.option('--chpid', type=str, required=False,
              help='The new channel path ID (CHPID, 2 hex chars) used by the '
              'adapter\'s partition. (OSA, FICON, HiperSockets only; Adapter '
              'must not be used by any partition).')
@click.option('--crypto-tke/--no-crypto-tke', default=None, required=False,
              help='The new setting whether TKE commands are permitted on the '
              'crypto adapter. (Crypto only).')
@click.option('--crypto-type', default=None, required=False,
              type=click.Choice(CRYPTO_TYPE_OPTIONS),
              help='The new crypto type (Crypto only; Adapter must be '
              'offline).')
@click.option('--storage-type', default=None, required=False,
              type=click.Choice(STORAGE_TYPE_OPTIONS),
              help='The new ficon type (FICON only; Adapter must be '
              'offline).')
@click.option('--dont-zeroize', is_flag=True, default=False, required=False,
              help='Do not zeroize when changing crypto type to '
              'accelerator. (Crypto only; Default is to zeroize).')
@click.pass_obj
def adapter_update(cmd_ctx, cpc, adapter, **options):
    """
    Update the properties of an adapter.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    The adapter may be a physical adapter (e.g. a discovered OSA card) or a
    logical adapter (e.g. HiperSockets).

    For Crypto Express adapters, the crypto type can be changed.

    For FICON Express adapters, the ficon type can be changed.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_adapter_update(cmd_ctx, cpc, adapter,
                                                   options))


@adapter_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.option('--name', type=str, required=True,
              help='The name of the new adapter.')
@click.option('--description', type=str, required=False,
              help='The description of the new adapter. Default: empty')
@click.option('--port-description', type=str, required=False,
              help='The description of the (single) port of the new adapter. '
              'Default: empty')
@click.option('--mtu-size', type=click.Choice(['8', '16', '32', '56']),
              required=False,
              help='The MTU size of the new adapter in KiB. Default: 8')
@click.pass_obj
def adapter_create_hipersocket(cmd_ctx, cpc, **options):
    """
    Create a HiperSockets adapter in a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.

    Some more properties of the new HiperSockets adapter can be set via
    adapter update.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_adapter_create_hipersocket(cmd_ctx, cpc, options))


@adapter_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('ADAPTER', type=str, metavar='ADAPTER')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the adapter.',
              prompt='Are you sure you want to delete this adapter ?')
@click.pass_obj
def adapter_delete_hipersocket(cmd_ctx, cpc, adapter):
    """
    Delete a HiperSockets adapter.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_adapter_delete_hipersocket(cmd_ctx, cpc, adapter))


@adapter_group.command('list-nics', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('ADAPTER', type=str, metavar='ADAPTER')
@add_options(LIST_OPTIONS)
@click.pass_obj
def adapter_list_nics(cmd_ctx, cpc, adapter, **options):
    """
    List the NICs backed by a network adapter in a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_adapter_list_nics(cmd_ctx, cpc, adapter, options))


def cmd_adapter_list(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    try:
        adapters = cpc.adapters.list()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    if options['type']:
        click.echo("The --type option is deprecated and type information "
                   "is now always shown.")

    show_list = [
        'name',
        'cpc',
    ]
    if not options['names_only']:
        show_list.extend([
            'adapter-id',
            'status',
            'state',
            'physical-channel-status',
            'type',
            'detected-card-type',
            'crypto-type',
            'card-location',
            'description',
        ])
    if options['uri']:
        show_list.extend([
            'object-uri',
        ])

    cpc_additions = {}
    for adapter in adapters:
        cpc_additions[adapter.uri] = cpc_name
    additions = {
        'cpc': cpc_additions,
    }

    try:
        print_resources(cmd_ctx, adapters, cmd_ctx.output_format, show_list,
                        additions, all=options['all'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_adapter_show(cmd_ctx, cpc_name, adapter_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    adapter = find_adapter(cmd_ctx, client, cpc_name, adapter_name)

    try:
        adapter.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(adapter.properties)

    # Add artificial property 'parent-name'
    properties['parent-name'] = cpc_name

    # Add artificial properties 'network-port-names', 'network-port-indexes'
    try:
        netport_uris = adapter.properties['network-port-uris']
    except KeyError:
        pass
    else:
        # It is a network adapter
        netport_names = []
        netport_indexes = []
        for netport_uri in netport_uris:
            netport_props = client.session.get(netport_uri)
            netport_names.append(netport_props['name'])
            netport_indexes.append(netport_props['index'])
        properties['network-port-names'] = netport_names
        properties['network-port-indexes'] = netport_indexes

    # Add artificial properties 'storage-port-names', 'storage-port-indexes'
    try:
        stoport_uris = adapter.properties['storage-port-uris']
    except KeyError:
        pass
    else:
        # It is a storage adapter
        stoport_names = []
        stoport_indexes = []
        for stoport_uri in stoport_uris:
            # For unconfigurd FICON adapters, the 'storage-port-uris' property
            # is set, but Get Adapter Properties fails with 404,4
            try:
                stoport_props = client.session.get(stoport_uri)
            except zhmcclient.HTTPError as exc:
                if exc.http_status == 404 and exc.reason == 4:
                    # Unconfigured FICON adapter
                    pass
                else:
                    raise
            else:
                stoport_names.append(stoport_props['name'])
                stoport_indexes.append(stoport_props['index'])
        properties['storage-port-names'] = stoport_names
        properties['storage-port-indexes'] = stoport_indexes

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def cmd_adapter_update(cmd_ctx, cpc_name, adapter_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    adapter = find_adapter(cmd_ctx, client, cpc_name, adapter_name)
    new_name = None  # New name if adapter name has changed

    name_map = {
        'mtu-size': 'maximum-transmission-unit-size',
        'chpid': 'channel-path-id',
        'crypto-tke': 'tke-commands-enabled',
        'crypto-type': None,
        'dont-zeroize': None,
        'storage-type': None,
    }
    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)
    crypto_type_option = options['crypto_type']
    storage_type_option = options['storage_type']

    if not properties and not crypto_type_option and not storage_type_option:
        cmd_ctx.spinner.stop()
        click.echo("No changes specified for updating adapter '{a}'.".
                   format(a=adapter_name))
        return

    if 'name' in properties and properties['name'] != adapter_name:
        new_name = properties['name']
    try:
        adapter.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    if crypto_type_option:
        crypto_type_prop = CRYPTO_TYPE_PROPERTIES[crypto_type_option]
        if crypto_type_option == 'acc':
            zeroize = not options['dont_zeroize']
        else:
            if options['dont_zeroize']:
                cmd_ctx.spinner.stop()
                click.echo("Ignoring --dont-zeroize option for adapter '{a}'.".
                           format(a=adapter_name))
            zeroize = None
        try:
            adapter.change_crypto_type(crypto_type_prop, zeroize)
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)

        # Changing the crypto type triggers a change of the adapter name,
        # if the current name is the default name (e.g. 'CCA 0104 A14B-03')
        # The new name will be visible at the API only after about 2 seconds.
        if CRYPTO_DEFAULT_NAMES.match(adapter.name):

            # This debug code can be used to test whether the behavior of
            # changing the adapter name has changed.
            DEBUG_CRYPTO_NAME_CHANGE = False

            if DEBUG_CRYPTO_NAME_CHANGE:
                t1 = datetime.now()
                cmd_ctx.spinner.stop()
                for _ in range(0, 20):
                    adapter.pull_full_properties()
                    dt = datetime.now() - t1
                    print("Debug: Adapter name after {}: {!r}".
                          format(dt, adapter.name))
            else:
                time.sleep(4)
                adapter.pull_full_properties()

            if adapter.name != adapter_name:
                new_name = adapter.name

    if storage_type_option:
        storage_type_prop = STORAGE_TYPE_PROPERTIES[storage_type_option]
        try:
            adapter.change_adapter_type(storage_type_prop)
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)
        sibling_adapters = adapter.list_sibling_adapters()
        sibling_adapter_names = ', '.join(
            ["'{}'".format(a.name) for a in sibling_adapters])
        cmd_ctx.spinner.stop()
        click.echo("FICON adapter {a} and its sibling adapter {s} have "
                   "been changed to type '{t}'.".
                   format(a=adapter.name, s=sibling_adapter_names,
                          t=storage_type_option))

    cmd_ctx.spinner.stop()
    if new_name:
        click.echo("Adapter '{a}' has been renamed to '{n}' and was updated.".
                   format(a=adapter_name, n=new_name))
    else:
        click.echo("Adapter '{a}' has been updated.".format(a=adapter_name))


def cmd_adapter_create_hipersocket(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    name_map = {
        'mtu-size': 'maximum-transmission-unit-size',
    }
    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    try:
        new_adapter = cpc.adapters.create_hipersocket(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("New HiperSockets adapter '{a}' has been created.".
               format(a=new_adapter.properties['name']))


def cmd_adapter_delete_hipersocket(cmd_ctx, cpc_name, adapter_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    adapter = find_adapter(cmd_ctx, client, cpc_name, adapter_name)

    try:
        adapter.delete()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("HiperSockets adapter '{a}' has been deleted.".
               format(a=adapter_name))


def cmd_adapter_list_nics(cmd_ctx, cpc_name, adapter_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    adapter = find_adapter(cmd_ctx, client, cpc_name, adapter_name)

    adapter_family = adapter.get_property('adapter-family')
    adapter_type = adapter.get_property('type')

    if adapter_family not in ('hipersockets', 'osa', 'roce', 'cna'):
        raise click_exception(
            "Adapter {f!r} on CPC {c} is not a network adapter".
            format(f=adapter.name, c=cpc_name), cmd_ctx.error_format)

    if adapter_type == 'osm':
        raise click_exception(
            "Adapter {f!r} on CPC {c} is an OSM adapter and cannot be "
            "assigned to partitions".
            format(f=adapter.name, c=cpc_name), cmd_ctx.error_format)

    results = []  # tuple(partition, nic, port_index)
    partitions = adapter.list_assigned_partitions()
    for part in partitions:
        nics = part.nics.list()
        for nic in nics:
            try:
                vswitch_uri = nic.get_property('virtual-switch-uri')
            except KeyError:
                pass
            else:
                vswitch_props = client.session.get(vswitch_uri)
                backing_adapter_uri = vswitch_props['backing-adapter-uri']
                backing_port_index = vswitch_props['port']
            try:
                port_uri = nic.get_property('network-adapter-port-uri')
            except KeyError:
                pass
            else:
                port_props = client.session.get(port_uri)
                backing_adapter_uri = port_props['parent']
                backing_port_index = port_props['index']

            if backing_adapter_uri == adapter.uri:
                results.append((part, nic, backing_port_index))

    show_list = [
        'name',
        'partition',
    ]
    if not options['names_only']:
        show_list.extend([
            'type',
            'port-index',
        ])
    if options['uri']:
        show_list.extend([
            'element-uri',
        ])

    partition_additions = {}
    port_index_additions = {}
    for part, nic, port_index in results:
        partition_additions[nic.uri] = part.name
        port_index_additions[nic.uri] = port_index
    additions = {
        'partition': partition_additions,
        'port-index': port_index_additions,
    }

    nics = [nic for _, nic, _ in results]
    try:
        print_resources(cmd_ctx, nics, cmd_ctx.output_format, show_list,
                        additions, all=options['all'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
