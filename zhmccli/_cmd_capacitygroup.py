# Copyright 2021 IBM Corp. All Rights Reserved.
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
Commands for capacity groups.
"""

from __future__ import absolute_import

import click

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS
from ._cmd_cpc import find_cpc
from ._cmd_partition import find_partition


# Default capping values for create
DEFAULT_CP_CAP = 0.0
DEFAULT_IFL_CAP = 0.0

# Limits for capping values
MIN_CAP = 0.0
MAX_CAP = 255.0


def find_capacitygroup(cmd_ctx, client, cpc_or_name, capacitygroup_name):
    """
    Find a capacity group by name and return its resource object.
    """
    if isinstance(cpc_or_name, zhmcclient.Cpc):
        cpc = cpc_or_name
    else:
        cpc = find_cpc(cmd_ctx, client, cpc_or_name)
    # The CPC must be in DPM mode. We don't check that because it would
    # cause a GET to the CPC resource that we otherwise don't need.
    try:
        capacitygroup = cpc.capacity_groups.find(name=capacitygroup_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return capacitygroup


@cli.group('capacitygroup', options_metavar=COMMAND_OPTIONS_METAVAR)
def capacitygroup_group():
    """
    Command group for managing capacity groups.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@capacitygroup_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@add_options(LIST_OPTIONS)
@click.pass_obj
def capacitygroup_list(cmd_ctx, cpc, **options):
    """
    List the capacity groups in a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_capacitygroup_list(cmd_ctx, cpc, options))


@capacitygroup_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('CAPACITYGROUP', type=str, metavar='CAPACITYGROUP')
@click.pass_obj
def capacitygroup_show(cmd_ctx, cpc, capacitygroup):
    """
    Show the details of a capacity group.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_capacitygroup_show(cmd_ctx, cpc, capacitygroup))


@capacitygroup_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('CAPACITYGROUP', type=str, metavar='CAPACITYGROUP')
@click.option('--name', type=str, required=False,
              help='The new name of the capacity group.')
@click.option('--description', type=str, required=False,
              help='The new description of the capacity group.')
@click.option('--enabled/--no-enabled', is_flag=True, required=False,
              default=None,
              help='The new enabled state of the capacity group.')
@click.option('--cp-cap', type=float, required=False, default=None,
              help='The new absolute capping value for CP processors, in '
              'units of processors from {mn} to {mx}.'.
              format(mn=MIN_CAP, mx=MAX_CAP))
@click.option('--ifl-cap', type=float, required=False, default=None,
              help='The new absolute capping value for IFL processors, in '
              'units of processors from {mn} to {mx}.'.
              format(mn=MIN_CAP, mx=MAX_CAP))
@click.pass_obj
def capacitygroup_update(cmd_ctx, cpc, capacitygroup, **options):
    """
    Update the properties of a capacity group.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_capacitygroup_update(cmd_ctx, cpc, capacitygroup, options))


@capacitygroup_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.option('--name', type=str, required=True,
              help='The name of the new capacity group.')
@click.option('--description', type=str, required=False,
              help='The description of the new capacity group. Default: empty')
@click.option('--enabled/--no-enabled', is_flag=True, required=False,
              default=True,
              help='The enabled state of the new capacity group. '
              'Default: Enabled')
@click.option('--cp-cap', type=float, required=False, default=None,
              help='The absolute capping value for CP processors, in units of '
              'processors from {mn} to {mx}. Default: {df}'.
              format(mn=MIN_CAP, mx=MAX_CAP, df=DEFAULT_CP_CAP))
@click.option('--ifl-cap', type=float, required=False, default=None,
              help='The absolute capping value for IFL processors, in units of '
              'processors from {mn} to {mx}. Default: {df}'.
              format(mn=MIN_CAP, mx=MAX_CAP, df=DEFAULT_IFL_CAP))
@click.pass_obj
def capacitygroup_create(cmd_ctx, cpc, **options):
    """
    Create a capacity group in a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_capacitygroup_create(cmd_ctx, cpc, options))


@capacitygroup_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('CAPACITYGROUP', type=str, metavar='CAPACITYGROUP')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the capacity group.',
              prompt='Are you sure you want to delete this capacity group ?')
@click.pass_obj
def capacitygroup_delete(cmd_ctx, cpc, capacitygroup):
    """
    Delete a capacity group.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_capacitygroup_delete(cmd_ctx, cpc, capacitygroup))


@capacitygroup_group.command(
    'add-partition', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('CAPACITYGROUP', type=str, metavar='CAPACITYGROUP')
@click.option('--partition', type=str, metavar='NAME',
              required=False, multiple=True,
              help='The name of the partition to be added to the capacity '
              'group. Can be specified multiple times.')
@click.pass_obj
def capacitygroup_add_partition(cmd_ctx, cpc, capacitygroup, **options):
    """
    Add a partition to a capacity group.

    A partition cannot become a member of more than one capacity group.
    The partition must be defined with shared processors and the
    capacity group must specify nonzero cap values for the processor types
    used by the partition. The partition must be on the same CPC as the
    capacity group and must not yet be a member of this (or any other)
    capacity group.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_capacitygroup_add_partition(
            cmd_ctx, cpc, capacitygroup, options))


@capacitygroup_group.command(
    'remove-partition', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('CAPACITYGROUP', type=str, metavar='CAPACITYGROUP')
@click.option('--partition', type=str, metavar='NAME',
              required=False, multiple=True,
              help='The name of the partition to be removed from the capacity '
              'group. Can be specified multiple times.')
@click.pass_obj
def capacitygroup_remove_partition(cmd_ctx, cpc, capacitygroup, **options):
    """
    Remove a partition from a capacity group.

    The partition must be a member of this capacity group.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_capacitygroup_remove_partition(
            cmd_ctx, cpc, capacitygroup, options))


def cmd_capacitygroup_list(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    try:
        capacitygroups = cpc.capacity_groups.list()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    show_list = [
        'name',
        'cpc',
    ]
    if not options['names_only']:
        show_list.extend([
            'capping-enabled',
            'absolute-general-purpose-proc-cap',
            'absolute-ifl-proc-cap',
            'partitions',
        ])
    if options['uri']:
        show_list.extend([
            'element-uri',
        ])

    cpc_additions = {}
    partitions_additions = {}
    for capacitygroup in capacitygroups:
        cpc_additions[capacitygroup.uri] = cpc_name
        try:
            partition_uris = capacitygroup.prop('partition-uris')
            partition_names = []
            for partition_uri in partition_uris:
                partition = cpc.partitions.find(**{'object-uri': partition_uri})
                partition_names.append(partition.name)
            partitions_additions[capacitygroup.uri] = partition_names
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)
    additions = {
        'cpc': cpc_additions,
        'partitions': partitions_additions,
    }

    try:
        print_resources(cmd_ctx, capacitygroups, cmd_ctx.output_format,
                        show_list, additions, all=options['all'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_capacitygroup_show(cmd_ctx, cpc_name, capacitygroup_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    capacitygroup = find_capacitygroup(
        cmd_ctx, client, cpc_name, capacitygroup_name)

    try:
        capacitygroup.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    print_properties(cmd_ctx, capacitygroup.properties, cmd_ctx.output_format)


def cmd_capacitygroup_update(cmd_ctx, cpc_name, capacitygroup_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    capacitygroup = find_capacitygroup(
        cmd_ctx, client, cpc_name, capacitygroup_name)

    name_map = {
        'enabled': 'capping-enabled',
        'cp-cap': 'absolute-general-purpose-proc-cap',
        'ifl-cap': 'absolute-ifl-proc-cap',
    }
    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating "
                   "capacity group '{cg}'.".
                   format(cg=capacitygroup_name))
        return

    try:
        capacitygroup.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    if 'name' in properties and properties['name'] != capacitygroup_name:
        click.echo("Capacity group '{cg}' has been renamed to '{cgn}' and was "
                   "updated.".
                   format(cg=capacitygroup_name, cgn=properties['name']))
    else:
        click.echo("Capacity group '{cg}' has been updated.".
                   format(cg=capacitygroup_name))


def cmd_capacitygroup_create(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    name_map = {
        'enabled': 'capping-enabled',
        'cp-cap': 'absolute-general-purpose-proc-cap',
        'ifl-cap': 'absolute-ifl-proc-cap',
    }
    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    try:
        new_capacitygroup = cpc.capacity_groups.create(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("New capacity group '{cg}' has been created.".
               format(cg=new_capacitygroup.properties['name']))


def cmd_capacitygroup_delete(cmd_ctx, cpc_name, capacitygroup_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    capacitygroup = find_capacitygroup(
        cmd_ctx, client, cpc_name, capacitygroup_name)

    try:
        capacitygroup.delete()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Capacity group '{cg}' has been deleted.".
               format(cg=capacitygroup_name))


def cmd_capacitygroup_add_partition(
        cmd_ctx, cpc_name, capacitygroup_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    capacitygroup = find_capacitygroup(
        cmd_ctx, client, cpc_name, capacitygroup_name)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    partition_names = options['partition']  # List
    if not partition_names:
        cmd_ctx.spinner.stop()
        click.echo("No partitions specified for adding to "
                   "capacity group '{cg}'.".
                   format(cg=capacitygroup_name))
        return

    for partition_name in partition_names:
        partition = find_partition(cmd_ctx, client, cpc, partition_name)
        try:
            capacitygroup.add_partition(partition)
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("The specified partitions have been added to "
               "capacity group '{cg}'.".
               format(cg=capacitygroup_name))


def cmd_capacitygroup_remove_partition(
        cmd_ctx, cpc_name, capacitygroup_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    capacitygroup = find_capacitygroup(
        cmd_ctx, client, cpc_name, capacitygroup_name)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    partition_names = options['partition']  # List
    if not partition_names:
        cmd_ctx.spinner.stop()
        click.echo("No partitions specified for removing from "
                   "capacity group '{cg}'.".
                   format(cg=capacitygroup_name))
        return

    for partition_name in partition_names:
        partition = find_partition(cmd_ctx, client, cpc, partition_name)
        try:
            capacitygroup.remove_partition(partition)
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("The specified partitions have been removed from "
               "capacity group '{cg}'.".
               format(cg=capacitygroup_name))
