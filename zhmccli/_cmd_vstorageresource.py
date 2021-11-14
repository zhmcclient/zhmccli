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
Commands for virtual storage resources on CPCs in DPM mode.
"""

from __future__ import absolute_import
from __future__ import print_function

import re
import click

import zhmcclient
from .zhmccli import cli
from ._cmd_port import find_port
from ._cmd_storagegroup import find_storagegroup
from ._helper import print_properties, print_resources, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS


def find_vstorageresource(cmd_ctx, client, stogrp_name, vsr_name):
    """
    Find a virtual storage resource by name and return its resource object.
    """
    console = client.consoles.console
    try:
        stogrp = console.storage_groups.find(name=stogrp_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    try:
        vsr = stogrp.virtual_storage_resources.find(name=vsr_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return vsr


@cli.group('vstorageresource', options_metavar=COMMAND_OPTIONS_METAVAR)
def vstorageresource_group():
    """
    Command group for managing virtual storage resources (DPM mode only).

    Virtual storage resources are automatically created resources that
    represent paths to storage volumes. They are contained in storage groups.

    The commands in this group work only on z14 and later CPCs that are in DPM
    mode.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@vstorageresource_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGEGROUP', type=str, metavar='STORAGEGROUP')
@add_options(LIST_OPTIONS)
@click.pass_obj
def vstorageresource_list(cmd_ctx, storagegroup, **options):
    """
    List the virtual storage resources of a storage group.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_vstorageresource_list(cmd_ctx, storagegroup, options))


@vstorageresource_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGEGROUP', type=str, metavar='STORAGEGROUP')
@click.argument('VSTORAGERESOURCE', type=str, metavar='VSTORAGERESOURCE')
@click.pass_obj
def vstorageresource_show(cmd_ctx, storagegroup, vstorageresource):
    """
    Show the details of a virtual storage resource.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_vstorageresource_show(cmd_ctx, storagegroup,
                                          vstorageresource))


@vstorageresource_group.command('update',
                                options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGEGROUP', type=str, metavar='STORAGEGROUP')
@click.argument('VSTORAGERESOURCE', type=str, metavar='VSTORAGERESOURCE')
@click.option('--name', type=str, required=False,
              help='The new name of the virtual storage resource.')
@click.option('--description', type=str, required=False,
              help='The new description of the virtual storage resource. '
              'Default: Empty')
@click.option('--adapter', type=str, metavar='NAME', required=False,
              help='The name of the storage adapter with the new port to which '
              'the virtual storage resource will be associated.')
@click.option('--port', type=str, metavar='NAME', required=False,
              help='The name of the new storage adapter port to which the '
              'virtual storage resource will be associated.')
@click.option('--device-number', type=str, required=False,
              help='A four-byte lower case hexadecimal string defining the '
              'new device number used for the volume when the FICON '
              'storage group containing this virtual storage resource is '
              'attached to partitions.')
@click.pass_obj
def vstorageresource_update(cmd_ctx, storagegroup, vstorageresource, **options):
    """
    Update the properties of a virtual storage resource.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_vstorageresource_update(cmd_ctx, storagegroup,
                                            vstorageresource, options))


def cmd_vstorageresource_list(cmd_ctx, stogrp_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stogrp = find_storagegroup(cmd_ctx, client, stogrp_name)
    cpc = stogrp.cpc

    try:
        vsrs = stogrp.virtual_storage_resources.list()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    show_list = [
        'name',
        'storagegroup',
    ]
    if not options['names_only']:
        show_list.extend([
            'device-number',
            'partition',
            'adapter',
            'port',
            'wwpn',
            'wwpn-status',
        ])
    if options['uri']:
        show_list.extend([
            'element-uri',
        ])

    sg_additions = {}
    partition_additions = {}
    adapter_additions = {}
    port_additions = {}
    wwpn_additions = {}
    wwpn_status_additions = {}
    for vsr in vsrs:
        try:
            sg_additions[vsr.uri] = stogrp_name
            partition_uri = vsr.prop('partition-uri')
            partition = cpc.partitions.find(**{'object-uri': partition_uri})
            partition_additions[vsr.uri] = partition.name
            port_uri = vsr.prop('adapter-port-uri')
            adapter_uri = re.match(r'^(.*)/storage-ports/.*$', port_uri). \
                group(1)
            adapter = cpc.adapters.find(**{'object-uri': adapter_uri})
            port = adapter.ports.find(**{'element-uri': port_uri})
            adapter_additions[vsr.uri] = adapter.name
            port_additions[vsr.uri] = port.name
            wwpn_info = vsr.prop('world-wide-port-name-info')
            wwpn_additions[vsr.uri] = wwpn_info['world-wide-port-name']
            wwpn_status_additions[vsr.uri] = wwpn_info['status']
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)

    additions = {
        'storagegroup': sg_additions,
        'partition': partition_additions,
        'adapter': adapter_additions,
        'port': port_additions,
        'wwpn': wwpn_additions,
        'wwpn-status': wwpn_status_additions,
    }

    try:
        print_resources(cmd_ctx, vsrs, cmd_ctx.output_format, show_list,
                        additions, all=options['all'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_vstorageresource_show(cmd_ctx, stogrp_name, vsr_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    vsr = find_vstorageresource(cmd_ctx, client, stogrp_name, vsr_name)

    try:
        vsr.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    print_properties(cmd_ctx, vsr.properties, cmd_ctx.output_format)


def cmd_vstorageresource_update(cmd_ctx, stogrp_name, vsr_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    vsr = find_vstorageresource(cmd_ctx, client, stogrp_name, vsr_name)
    cpc = vsr.manager.parent.cpc

    name_map = {
        # The following options are handled in this function:
        'adapter': None,
        'port': None,
    }
    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    adapter_name = org_options['adapter']
    port_name = org_options['port']
    if bool(adapter_name) != bool(port_name):
        raise click_exception(
            "The --adapter and --port options must be specified together.",
            cmd_ctx.error_format)
    if adapter_name:
        port = find_port(cmd_ctx, client, cpc, adapter_name, port_name)
        properties['adapter-port-uri'] = port.uri

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating virtual storage "
                   "resource '{vsr}'.".format(vsr=vsr_name))
        return

    try:
        vsr.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    if 'name' in properties and properties['name'] != vsr_name:
        click.echo("Virtual storage resource '{vsr}' has been renamed to "
                   "'{vsrn}' and was updated.".
                   format(vsr=vsr_name, vsrn=properties['name']))
    else:
        click.echo("Virtual storage resource '{vsr}' has been updated.".
                   format(vsr=vsr_name))
