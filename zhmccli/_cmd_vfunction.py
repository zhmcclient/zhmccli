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
Commands for virtual functions.
"""

from __future__ import absolute_import

import click

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS

from ._cmd_partition import find_partition


def find_vfunction(
        cmd_ctx, client, cpc_or_name, partition_name, vfunction_name):
    """
    Find a virtual function by name and return its resource object.
    """
    partition = find_partition(cmd_ctx, client, cpc_or_name, partition_name)
    try:
        vfunction = partition.virtual_functions.find(name=vfunction_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return vfunction


@cli.group('vfunction', options_metavar=COMMAND_OPTIONS_METAVAR)
def vfunction_group():
    """
    Command group for managing virtual functions (DPM mode only).

    The only virtual functions that can be managed with the commands in this
    group are those of the zEDC accelerator adapter, and only on CPCs that are
    in DPM mode.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@vfunction_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@add_options(LIST_OPTIONS)
@click.pass_obj
def vfunction_list(cmd_ctx, cpc, partition, **options):
    """
    List the virtual functions in a partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_vfunction_list(cmd_ctx, cpc, partition,
                                                   options))


@vfunction_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.argument('VFUNCTION', type=str, metavar='VFUNCTION')
@click.pass_obj
def vfunction_show(cmd_ctx, cpc, partition, vfunction):
    """
    Show the details of a virtual function.

    The following properties are shown in addition to those returned by the HMC:

    \b
      - 'parent-name' - Name of the parent Partition.
      - 'adapter-name' - Name of the Adapter referenced by 'adapter-uri'.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_vfunction_show(cmd_ctx, cpc, partition,
                                                   vfunction))


@vfunction_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.option('--name', type=str, required=True,
              help='The name of the new virtual function. Must be unique '
              'within the virtual functions of the partition')
@click.option('--description', type=str, required=False,
              help='The description of the new virtual function. '
              'Default: empty')
@click.option('--adapter', type=str, required=True,
              help='The name of the adapter backing the virtual function.')
@click.option('--device-number', type=str, required=False,
              help='The device number to be used for the new virtual '
              'function. Default: auto-generated')
@click.pass_obj
def vfunction_create(cmd_ctx, cpc, partition, **options):
    """
    Create a virtual function in a partition.

    This assigns a virtual function of an adapter to a partition, creating
    a named virtual function resource within that partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_vfunction_create(cmd_ctx, cpc, partition,
                                                     options))


@vfunction_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.argument('VFUNCTION', type=str, metavar='VFUNCTION')
@click.option('--name', type=str, required=False,
              help='The new name of the virtual function. Must be unique '
              'within the virtual functions of the partition.')
@click.option('--description', type=str, required=False,
              help='The new description of the virtual function.')
@click.option('--adapter', type=str, required=False,
              help='The name of the new adapter (in the same CPC) that will '
              'back the virtual function.')
@click.option('--device-number', type=str, required=False,
              help='The new device number to be used for the virtual '
              'function.')
@click.pass_obj
def vfunction_update(cmd_ctx, cpc, partition, vfunction, **options):
    """
    Update the properties of a virtual function.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_vfunction_update(cmd_ctx, cpc, partition,
                                                     vfunction, options))


@vfunction_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.argument('VFUNCTION', type=str, metavar='VFUNCTION')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the virtual function.',
              prompt='Are you sure you want to delete this virtual function ?')
@click.pass_obj
def vfunction_delete(cmd_ctx, cpc, partition, vfunction):
    """
    Delete a virtual function.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_vfunction_delete(cmd_ctx, cpc, partition,
                                                     vfunction))


def cmd_vfunction_list(cmd_ctx, cpc_name, partition_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    try:
        vfunctions = partition.virtual_functions.list()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    show_list = [
        'name',
        'cpc',
        'partition',
    ]
    if not options['names_only']:
        show_list.extend([
            'description',
        ])
    if options['uri']:
        show_list.extend([
            'element-uri',
        ])

    cpc_additions = {}
    partition_additions = {}
    for vfunction in vfunctions:
        cpc_additions[vfunction.uri] = cpc_name
        partition_additions[vfunction.uri] = partition_name
    additions = {
        'cpc': cpc_additions,
        'partition': partition_additions,
    }

    try:
        print_resources(cmd_ctx, vfunctions, cmd_ctx.output_format, show_list,
                        additions, all=options['all'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_vfunction_show(cmd_ctx, cpc_name, partition_name, vfunction_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    vfunction = find_vfunction(cmd_ctx, client, cpc_name, partition_name,
                               vfunction_name)

    try:
        vfunction.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(vfunction.properties)

    # Add artificial property 'parent-name'
    properties['parent-name'] = partition_name

    # Add artificial property 'adapter-name'
    adapter_uri = vfunction.get_property('adapter-uri')
    adapter_props = client.session.get(adapter_uri)
    adapter_name = adapter_props['name']
    properties['adapter-name'] = adapter_name

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def cmd_vfunction_create(cmd_ctx, cpc_name, partition_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    name_map = {
        # The following options are handled in this function:
        'adapter': None,
    }
    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    adapter_name = org_options['adapter']
    try:
        adapter = partition.manager.cpc.adapters.find(name=adapter_name)
    except zhmcclient.NotFound:
        raise click_exception("Could not find adapter '{a}' in CPC '{c}'.".
                              format(a=adapter_name, c=cpc_name),
                              cmd_ctx.error_format)
    properties['adapter-uri'] = adapter.uri

    try:
        new_vfunction = partition.virtual_functions.create(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("New virtual function '{f}' has been created.".
               format(f=new_vfunction.properties['name']))


def cmd_vfunction_update(cmd_ctx, cpc_name, partition_name, vfunction_name,
                         options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    vfunction = find_vfunction(cmd_ctx, client, cpc_name, partition_name,
                               vfunction_name)

    name_map = {
        # The following options are handled in this function:
        'adapter': None,
    }
    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    if org_options['adapter'] is not None:
        adapter_name = org_options['adapter']
        try:
            adapter = vfunction.manager.partition.manager.cpc.adapters.find(
                name=adapter_name)
        except zhmcclient.NotFound:
            raise click_exception("Could not find adapter '{a}' in CPC '{c}'.".
                                  format(a=adapter_name, c=cpc_name),
                                  cmd_ctx.error_format)
        properties['adapter-uri'] = adapter.uri

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating virtual function "
                   "{f}.".format(f=vfunction_name))
        return

    try:
        vfunction.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    if 'name' in properties and properties['name'] != vfunction_name:
        click.echo("Virtual function '{f}' has been renamed to '{fn}' and was "
                   "updated.".format(f=vfunction_name, fn=properties['name']))
    else:
        click.echo("Virtual function '{f}' has been updated.".
                   format(f=vfunction_name))


def cmd_vfunction_delete(cmd_ctx, cpc_name, partition_name, vfunction_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    vfunction = find_vfunction(cmd_ctx, client, cpc_name, partition_name,
                               vfunction_name)

    try:
        vfunction.delete()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Virtual function '{f}' has been deleted.".
               format(f=vfunction_name))
