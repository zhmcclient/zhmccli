# Copyright 2020 IBM Corp. All Rights Reserved.
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
Commands for storage groups on CPCs in DPM mode.
"""

from __future__ import absolute_import
from __future__ import print_function

import click

import zhmcclient
from .zhmccli import cli
from ._cmd_cpc import find_cpc
from ._cmd_port import find_port
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS, EMAIL_OPTIONS, \
    ASYNC_TIMEOUT_OPTIONS


ALL_TYPES = ['fcp', 'fc']
ALL_PARTITION_STATUSES = [
    "communications-not-active",
    "status-check",
    "stopped",
    "terminated",
    "starting",
    "active",
    "stopping",
    "degraded",
    "reservation-error",
    "paused",
]

# Defaults for storage group creation unless created from storage template
DEFAULT_TYPE = 'fcp'
DEFAULT_CONNECTIVITY = 2
DEFAULT_SHARED = True
DEFAULT_MAX_PARTITIONS = 2
DEFAULT_DIRECT_CONNECTION_COUNT = 0


def find_storagegroup(cmd_ctx, client, stogrp_name):
    """
    Find a storage group by name and return its resource object.
    """
    console = client.consoles.console
    try:
        stogrp = console.storage_groups.find(name=stogrp_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return stogrp


@cli.group('storagegroup', options_metavar=COMMAND_OPTIONS_METAVAR)
def storagegroup_group():
    """
    Command group for managing storage groups (DPM mode only).

    Storage groups are definitions in the HMC that simplify the management of
    storage attached to partitions.

    The commands in this group work only on z14 and later CPCs that are in DPM
    mode.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@storagegroup_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@add_options(LIST_OPTIONS)
@click.pass_obj
def storagegroup_list(cmd_ctx, **options):
    """
    List the storage groups defined in the HMC.

    Storage groups for which the authenticated user does not have
    object-access permission will not be included.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_storagegroup_list(cmd_ctx, options))


@storagegroup_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGEGROUP', type=str, metavar='STORAGEGROUP')
@click.pass_obj
def storagegroup_show(cmd_ctx, storagegroup):
    """
    Show the details of a storage group.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_storagegroup_show(cmd_ctx, storagegroup))


@storagegroup_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--name', type=str, required=True,
              help='The name of the new storage group.')
@click.option('--cpc', type=str, required=True,
              help='The name of the CPC associated with the new storage group.')
@click.option('--type', type=click.Choice(ALL_TYPES),
              required=False, default=DEFAULT_TYPE,
              help='The type of the new storage group. '
              'Mutually exclusive with --template; one of them is required.')
@click.option('--template', type=str, required=False,
              help='The name of the storage template on which the new storage '
              'group is to be based. '
              'Mutually exclusive with --type; one of them is required.')
@click.option('--description', type=str, required=False,
              help='The description of the new storage group. '
              'Default: Empty, or from template')
@click.option('--shared', type=bool, required=False,
              help='Indicates whether the storage group can be attached to '
              'more than one partition. '
              'Default: {d}, or from template'.
              format(d=DEFAULT_SHARED))
@click.option('--connectivity', type=int, required=False,
              help='The number of adapters to utilize for the new storage '
              'group. '
              'Default: {d}, or from template'.
              format(d=DEFAULT_CONNECTIVITY))
@click.option('--max-partitions', type=int, required=False,
              help='The maximum number of partitions to which the new storage '
              'group can be attached. '
              'Default: {d}, or from template'.
              format(d=DEFAULT_MAX_PARTITIONS))
@click.option('--direct-connection-count', type=int, required=False,
              help='The number of additional virtual storage resource '
              'connections for the host that can be directly assigned to a '
              'guest virtual machine. A value of 0 indicates this feature is '
              'disabled. '
              'Default: {d}, or from template'.
              format(d=DEFAULT_DIRECT_CONNECTION_COUNT))
@add_options(EMAIL_OPTIONS)
@click.pass_obj
def storagegroup_create(cmd_ctx, **options):
    """
    Create a storage group.

    When created using --type, the new storage group will have no storage
    volumes. Storage volumes can be created and added to the storage group
    with the 'storagevolume' command.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_storagegroup_create(cmd_ctx, options))


@storagegroup_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGEGROUP', type=str, metavar='STORAGEGROUP')
@click.option('--name', type=str, required=False,
              help='The new name of the storage group.')
@click.option('--description', type=str, required=False,
              help='The new description of the storage group.')
@click.option('--shared', type=bool, required=False,
              help='Indicates whether the storage group can be attached to '
              'more than one partition.')
@click.option('--connectivity', type=int, required=False,
              help='The number of adapters to utilize for the new storage '
              'group.')
@click.option('--max-partitions', type=int, required=False,
              help='The maximum number of partitions to which the new storage '
              'group can be attached.')
@click.option('--direct-connection-count', type=int, required=False,
              help='The number of additional virtual storage resource '
              'connections for the host that can be directly assigned to a '
              'guest virtual machine. A value of 0 indicates this feature is '
              'disabled.')
@add_options(EMAIL_OPTIONS)
@click.pass_obj
def storagegroup_update(cmd_ctx, storagegroup, **options):
    """
    Update the properties of a storage group.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagegroup_update(cmd_ctx, storagegroup, options))


@storagegroup_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGEGROUP', type=str, metavar='STORAGEGROUP')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the storage group.',
              prompt='Are you sure you want to delete this storage group ?')
@add_options(EMAIL_OPTIONS)
@click.pass_obj
def storagegroup_delete(cmd_ctx, storagegroup, **options):
    """
    Delete a storage group.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagegroup_delete(cmd_ctx, storagegroup, options))


@storagegroup_group.command('list-partitions',
                            options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGEGROUP', type=str, metavar='STORAGEGROUP')
@click.option('--name', type=str, required=False,
              help='Regular expression filter to limit the returned partitions '
              'to those with a matching name.')
@click.option('--status', type=str, required=False,
              help='Filter to limit the returned partitions to those with a '
              'matching status. Valid status values are: {sv}.'.
              format(sv=', '.join(ALL_PARTITION_STATUSES)))
@click.pass_obj
def storagegroup_list_partitions(cmd_ctx, storagegroup, **options):
    """
    List the partitions to which a storage group is attached.

    Partitions for which the authenticated user does not have object-access
    permission will not be included.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagegroup_list_partitions(cmd_ctx, storagegroup,
                                                 options))


@storagegroup_group.command('list-ports',
                            options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGEGROUP', type=str, metavar='STORAGEGROUP')
@click.pass_obj
def storagegroup_list_ports(cmd_ctx, storagegroup):
    """
    List the candidate adapter ports of a storage group.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagegroup_list_ports(cmd_ctx, storagegroup))


@storagegroup_group.command('add-ports',
                            options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGEGROUP', type=str, metavar='STORAGEGROUP')
@click.option('--adapter', type=str, metavar='NAME',
              required=False, multiple=True,
              help='The name of the storage adapter with the new port to be '
              'added. '
              'The --adapter and --port options can be specified multiple '
              'times and correspond to each other via their order.')
@click.option('--port', type=str, metavar='NAME',
              required=False, multiple=True,
              help='The name of the storage adapter port to be added. '
              'The --adapter and --port options can be specified multiple '
              'times and correspond to each other via their order.')
@click.pass_obj
def storagegroup_add_ports(cmd_ctx, storagegroup, **options):
    """
    Add storage adapter ports to the candidate adapter port list of a storage
    group.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagegroup_add_ports(cmd_ctx, storagegroup, options))


@storagegroup_group.command('remove-ports',
                            options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGEGROUP', type=str, metavar='STORAGEGROUP')
@click.option('--adapter', type=str, metavar='NAME',
              required=False, multiple=True,
              help='The name of the storage adapter with the new port to be '
              'added. '
              'The --adapter and --port options can be specified multiple '
              'times and correspond to each other via their order.')
@click.option('--port', type=str, metavar='NAME',
              required=False, multiple=True,
              help='The name of the storage adapter port to be added. '
              'The --adapter and --port options can be specified multiple '
              'times and correspond to each other via their order.')
@click.pass_obj
def storagegroup_remove_ports(cmd_ctx, storagegroup, **options):
    """
    Remove ports from the candidate adapter port list of a storage group.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagegroup_remove_ports(cmd_ctx, storagegroup, options))


@storagegroup_group.command('discover-fcp',
                            options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGEGROUP', type=str, metavar='STORAGEGROUP')
@click.option('--force-restart', type=bool, required=False, default=False,
              help='Indicates if there is an in-progress discovery operation '
              'for the specified storage group, it should be terminated and '
              'started again.')
@add_options(ASYNC_TIMEOUT_OPTIONS)
@click.pass_obj
def storagegroup_discover_fcp(cmd_ctx, storagegroup, **options):
    """
    Perform Logical Unit Number (LUN) discovery for an FCP storage group.

    This command only applies to storage groups of type "fcp".

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagegroup_discover_fcp(cmd_ctx, storagegroup, options))


def cmd_storagegroup_list(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    try:
        stogrps = console.storage_groups.list()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    show_list = [
        'name',
    ]
    if not options['names_only']:
        show_list.extend([
            'device-number',
            'type',
            'shared',
            'fulfillment-state',
            'cpc',  # CPC name, as additional property
        ])
    if options['uri']:
        show_list.extend([
            'object-uri',
        ])

    cpc_additions = {}
    for sg in stogrps:
        try:
            cpc_uri = sg.prop('cpc-uri')
            cpc = client.cpcs.find(**{'object-uri': cpc_uri})
            cpc_additions[sg.uri] = cpc.name
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)
    additions = {
        'cpc': cpc_additions,
    }

    try:
        print_resources(cmd_ctx, stogrps, cmd_ctx.output_format, show_list,
                        additions, all=options['all'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_storagegroup_show(cmd_ctx, stogrp_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stogrp = find_storagegroup(cmd_ctx, client, stogrp_name)

    try:
        stogrp.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    print_properties(cmd_ctx, stogrp.properties, cmd_ctx.output_format)


def cmd_storagegroup_create(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    name_map = {
        # The following options are handled in this function:
        'cpc': None,
        'email-to-address': None,
        'email-cc-address': None,
    }
    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    cpc_name = org_options['cpc']  # It is required
    cpc = find_cpc(cmd_ctx, client, cpc_name)
    properties['cpc-uri'] = cpc.uri

    email_to_addresses = org_options['email-to-address']
    if email_to_addresses:
        properties['email-to-addresses'] = email_to_addresses

    email_cc_addresses = org_options['email-cc-address']
    if email_cc_addresses:
        properties['email-cc-addresses'] = email_cc_addresses

    try:
        new_stogrp = console.storage_groups.create(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("New storage group '{sg}' has been created.".
               format(sg=new_stogrp.properties['name']))


def cmd_storagegroup_update(cmd_ctx, stogrp_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stogrp = find_storagegroup(cmd_ctx, client, stogrp_name)

    name_map = {
        # The following options are handled in this function:
        'email-to-address': None,
        'email-cc-address': None,
    }
    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    email_to_addresses = org_options['email-to-address']
    if email_to_addresses:
        properties['email-to-addresses'] = email_to_addresses

    email_cc_addresses = org_options['email-cc-address']
    if email_cc_addresses:
        properties['email-cc-addresses'] = email_cc_addresses

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating storage group '{sg}'.".
                   format(sg=stogrp_name))
        return

    try:
        stogrp.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    if 'name' in properties and properties['name'] != stogrp_name:
        click.echo("Storage group '{sg}' has been renamed to '{sgn}' and was "
                   "updated.".
                   format(sg=stogrp_name, sgn=properties['name']))
    else:
        click.echo("Storage group '{sg}' has been updated.".
                   format(sg=stogrp_name))


def cmd_storagegroup_delete(cmd_ctx, stogrp_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stogrp = find_storagegroup(cmd_ctx, client, stogrp_name)

    org_options = original_options(options)

    email_insert = org_options['email-insert']
    email_to_addresses = org_options['email-to-address'] or None
    email_cc_addresses = org_options['email-cc-address'] or None

    try:
        stogrp.delete(email_to_addresses=email_to_addresses,
                      email_cc_addresses=email_cc_addresses,
                      email_insert=email_insert)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Storage group '{sg}' has been deleted.".format(sg=stogrp_name))


def cmd_storagegroup_list_partitions(cmd_ctx, stogrp_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stogrp = find_storagegroup(cmd_ctx, client, stogrp_name)

    filter_name = options['name']
    filter_status = options['status']

    try:
        partitions = stogrp.list_attached_partitions(
            name=filter_name, status=filter_status)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    show_list = [
        'cpc',  # CPC name, as additional property
        'name',
        'type',
        'status',
    ]
    cpc_additions = {}
    for part in partitions:
        cpc = part.manager.parent
        cpc_additions[part.uri] = cpc.name
    additions = {
        'cpc': cpc_additions,
    }

    try:
        print_resources(cmd_ctx, partitions, cmd_ctx.output_format, show_list,
                        additions)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_storagegroup_list_ports(cmd_ctx, stogrp_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stogrp = find_storagegroup(cmd_ctx, client, stogrp_name)

    try:
        ports = stogrp.list_candidate_adapter_ports()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    show_list = [
        'cpc',  # CPC name, as additional property
        'adapter',  # Adapter name, as additional property
        'name',
        'index',
        'fabric-id',
    ]
    cpc_additions = {}
    adapter_additions = {}
    for port in ports:
        adapter = port.manager.parent
        adapter_additions[port.uri] = adapter.name
        cpc = adapter.manager.parent
        cpc_additions[port.uri] = cpc.name
    additions = {
        'cpc': cpc_additions,
        'adapter': adapter_additions,
    }

    try:
        print_resources(cmd_ctx, ports, cmd_ctx.output_format, show_list,
                        additions)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_storagegroup_add_ports(cmd_ctx, stogrp_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stogrp = find_storagegroup(cmd_ctx, client, stogrp_name)
    cpc = stogrp.cpc

    adapter_names = options['adapter']  # List
    port_names = options['port']  # List
    if len(adapter_names) != len(port_names):
        raise click_exception(
            "The --adapter and --port options must be specified the same "
            "number of times, but have been specified {na} and {np} times.".
            format(na=len(adapter_names), np=len(port_names)),
            cmd_ctx.error_format)
    ports = []
    for i, adapter_name in enumerate(adapter_names):
        port_name = port_names[i]
        port = find_port(cmd_ctx, client, cpc, adapter_name, port_name)
        ports.append(port)

    if not ports:
        cmd_ctx.spinner.stop()
        click.echo("No ports specified for adding to the candidate list "
                   "of storage group '{sg}'.".format(sg=stogrp_name))
        return

    try:
        stogrp.add_candidate_adapter_ports(ports)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("The specified ports have been added to the candidate list "
               "of storage group '{sg}'.".format(sg=stogrp_name))


def cmd_storagegroup_remove_ports(cmd_ctx, stogrp_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stogrp = find_storagegroup(cmd_ctx, client, stogrp_name)
    cpc = stogrp.cpc

    adapter_names = options['adapter']  # List
    port_names = options['port']  # List
    if len(adapter_names) != len(port_names):
        raise click_exception(
            "The --adapter and --port options must be specified the same "
            "number of times, but have been specified {na} and {np} times.".
            format(na=len(adapter_names), np=len(port_names)),
            cmd_ctx.error_format)
    ports = []
    for i, adapter_name in enumerate(adapter_names):
        port_name = port_names[i]
        port = find_port(cmd_ctx, client, cpc, adapter_name, port_name)
        ports.append(port)

    if not ports:
        cmd_ctx.spinner.stop()
        click.echo("No ports specified for removing from the candidate list "
                   "of storage group '{sg}'.".format(sg=stogrp_name))
        return

    try:
        stogrp.remove_candidate_adapter_ports(ports)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("The specified ports have been removed from the candidate list "
               "of storage group '{sg}'.".format(sg=stogrp_name))


def cmd_storagegroup_discover_fcp(cmd_ctx, stogrp_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stogrp = find_storagegroup(cmd_ctx, client, stogrp_name)

    force_restart = options['force_restart']

    try:
        stogrp.discover_fcp(
            force_restart=force_restart, wait_for_completion=True,
            operation_timeout=options['operation_timeout'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("LUN discovery has been completed for FCP storage group '{sg}'.".
               format(sg=stogrp_name))
