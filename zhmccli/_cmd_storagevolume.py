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
Commands for storage volumes on CPCs in DPM mode.
"""

from __future__ import absolute_import
from __future__ import print_function

import click

import zhmcclient
from .zhmccli import cli
from ._cmd_port import find_port
from ._cmd_storagegroup import find_storagegroup
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS, EMAIL_OPTIONS


ALL_USAGES = ['boot', 'data']
ALL_MODELS = [
    '1',  # Model 1
    '2',  # Model 2
    '3',  # Model 3
    '9',  # Model 9
    '27',  # Model 27
    '54',  # Model 54
    'EAV',  # Extended Address Volume
]

# Defaults for storage volume creation unless created from storage template
DEFAULT_USAGE = 'data'


def find_storagevolume(cmd_ctx, client, stogrp_name, stovol_name):
    """
    Find a storage volume by name and return its resource object.
    """
    console = client.consoles.console
    try:
        stogrp = console.storage_groups.find(name=stogrp_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    try:
        stovol = stogrp.storage_volumes.find(name=stovol_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return stovol


@cli.group('storagevolume', options_metavar=COMMAND_OPTIONS_METAVAR)
def storagevolume_group():
    """
    Command group for managing storage volumes (DPM mode only).

    Storage volumes are definitions in the HMC with knowledge about actual
    storage volumes. They are contained in storage groups.

    The commands in this group work only on z14 and later CPCs that are in DPM
    mode.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@storagevolume_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGEGROUP', type=str, metavar='STORAGEGROUP')
@add_options(LIST_OPTIONS)
@click.pass_obj
def storagevolume_list(cmd_ctx, storagegroup, **options):
    """
    List the storage volumes of a storage group.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagevolume_list(cmd_ctx, storagegroup, options))


@storagevolume_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGEGROUP', type=str, metavar='STORAGEGROUP')
@click.argument('STORAGEVOLUME', type=str, metavar='STORAGEVOLUME')
@click.pass_obj
def storagevolume_show(cmd_ctx, storagegroup, storagevolume):
    """
    Show the details of a storage volume.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagevolume_show(cmd_ctx, storagegroup, storagevolume))


@storagevolume_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGEGROUP', type=str, metavar='STORAGEGROUP')
@click.option('--name', type=str, required=True,
              help='The name of the new storage volume.')
@click.option('--description', type=str, required=False,
              help='The description of the new storage volume. '
              'Default: Empty')
@click.option('--size', type=float, required=False,
              help='The size in GiB for the volume. '
              'For FCP-type storage groups: Required. '
              'For FC-type storage groups: Mutually exclusive with '
              '--cylinders; one of them is required.')
@click.option('--usage', type=click.Choice(ALL_USAGES),
              required=False, default=DEFAULT_USAGE,
              help='The usage of the storage volume. '
              'Default: {d}'.
              format(d=DEFAULT_USAGE))
@click.option('--model', type=click.Choice(ALL_MODELS), required=False,
              help='The model of the storage volume. '
              'Only for FC-type storage groups and required.')
@click.option('--cylinders', type=float, required=False,
              help='The size in cylinders for the volume. '
              'Only for FC-type storage groups and mutually exclusive with '
              '--size; one of them is required.')
@click.option('--device-number', type=str, required=False,
              help='A four-byte lower case hexadecimal string defining the '
              'device number used for the new volume when the FICON '
              'storage group containing this storage volume is attached to '
              'partitions. '
              'Only for FC-type storage groups. '
              'Default: Auto-assigned')
@add_options(EMAIL_OPTIONS)
@click.pass_obj
def storagevolume_create(cmd_ctx, storagegroup, **options):
    """
    Create a storage volume in a storage group and optionally request its
    fulfillment.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagevolume_create(cmd_ctx, storagegroup, options))


@storagevolume_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGEGROUP', type=str, metavar='STORAGEGROUP')
@click.argument('STORAGEVOLUME', type=str, metavar='STORAGEVOLUME')
@click.option('--name', type=str, required=False,
              help='The new name of the storage volume.')
@click.option('--description', type=str, required=False,
              help='The new description of the storage volume. '
              'Default: Empty')
@click.option('--size', type=float, required=False,
              help='The new size in GiB for the volume. '
              'Can only be increased. '
              'For FCP-type storage groups: Required. '
              'For FC-type storage groups: Mutually exclusive with '
              '--cylinders; one of them is required.')
@click.option('--usage', type=click.Choice(ALL_USAGES), required=False,
              help='The new usage of the storage volume.')
@click.option('--model', type=click.Choice(ALL_MODELS), required=False,
              help='The new model of the storage volume. '
              'Only for FC-type storage groups and required.')
@click.option('--cylinders', type=float, required=False,
              help='The new size in cylinders for the volume. '
              'Can only be increased. '
              'Only for FC-type storage groups and mutually exclusive with '
              '--size; one of them is required.')
@click.option('--device-number', type=str, required=False,
              help='A four-byte lower case hexadecimal string defining the '
              'new device number used for the volume when the FICON '
              'storage group containing this storage volume is attached to '
              'partitions. '
              'Only for FC-type storage groups.')
@add_options(EMAIL_OPTIONS)
@click.pass_obj
def storagevolume_update(cmd_ctx, storagegroup, storagevolume, **options):
    """
    Update the properties of a storage volume and optionally request its
    fulfillment.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagevolume_update(cmd_ctx, storagegroup, storagevolume,
                                         options))


@storagevolume_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGEGROUP', type=str, metavar='STORAGEGROUP')
@click.argument('STORAGEVOLUME', type=str, metavar='STORAGEVOLUME')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the storage volume.',
              prompt='Are you sure you want to delete this storage volume ?')
@add_options(EMAIL_OPTIONS)
@click.pass_obj
def storagevolume_delete(cmd_ctx, storagegroup, storagevolume, **options):
    """
    Delete a storage volume and optionally request its fulfillment.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagevolume_delete(cmd_ctx, storagegroup, storagevolume,
                                         options))


@storagevolume_group.command('fulfill-fcp',
                             options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGEGROUP', type=str, metavar='STORAGEGROUP')
@click.argument('STORAGEVOLUME', type=str, metavar='STORAGEVOLUME')
@click.option('--wwpn', type=str, required=True,
              help='A 16-character lower case hexadecimal string that '
              'specifies the world wide port name (WWPN) of the FCP storage '
              'controller containing the boot volume.')
@click.option('--lun', type=str, required=True,
              help='A 16-character lower case hexadecimal string that '
              'specifies the logical unit name (LUN) of the FCP storage '
              'controller containing the boot volume.')
@click.option('--adapter', type=str, metavar='NAME', required=True,
              help='The name of the storage adapter that has the port used to '
              'boot from the storage volume.')
@click.option('--port', type=str, metavar='NAME', required=True,
              help='The name of the storage adapter port used to boot from the '
              'storage volume.')
@click.pass_obj
def storagevolume_fulfill_fcp(cmd_ctx, storagegroup, storagevolume, **options):
    """
    Manually indicate fulfillment of creation of an FCP boot volume.

    The CPC automatically discovers FCP volumes (including boot volumes) and
    sets their fulfillment status to complete. Manually indicating fulfillment
    of an FCP boot volume is only needed to speed up the process.
    Note that manually indicating fulfillment is only possible as long as
    FCP discovery is not yet complete, as indicated by a "validated" status
    on at least of the parent storage group's WWPNs.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagevolume_fulfill_fcp(cmd_ctx, storagegroup,
                                              storagevolume, options))


def cmd_storagevolume_list(cmd_ctx, stogrp_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stogrp = find_storagegroup(cmd_ctx, client, stogrp_name)

    try:
        stovols = stogrp.storage_volumes.list()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    show_list = [
        'name',
        'storagegroup',
    ]
    if not options['names_only']:
        show_list.extend([
            'uuid',
            'fulfillment-state',
            'usage',
            'size',
        ])
    if options['uri']:
        show_list.extend([
            'element-uri',
        ])

    sg_additions = {}
    for stovol in stovols:
        sg_additions[stovol.uri] = stogrp_name
    additions = {
        'storagegroup': sg_additions,
    }

    try:
        print_resources(cmd_ctx, stovols, cmd_ctx.output_format, show_list,
                        additions, all=options['all'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_storagevolume_show(cmd_ctx, stogrp_name, stovol_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stovol = find_storagevolume(cmd_ctx, client, stogrp_name, stovol_name)

    try:
        stovol.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    print_properties(cmd_ctx, stovol.properties, cmd_ctx.output_format)


def cmd_storagevolume_create(cmd_ctx, stogrp_name, options):
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

    try:
        new_stovol = stogrp.storage_volumes.create(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("New storage volume '{sv}' has been created.".
               format(sv=new_stovol.properties['name']))


def cmd_storagevolume_update(cmd_ctx, stogrp_name, stovol_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stovol = find_storagevolume(cmd_ctx, client, stogrp_name, stovol_name)

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
        click.echo("No properties specified for updating "
                   "storage volume '{sv}'.".
                   format(sv=stovol_name))
        return

    try:
        stovol.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    if 'name' in properties and properties['name'] != stovol_name:
        click.echo("Storage volume '{sv}' has been renamed to '{svn}' and was "
                   "updated.".
                   format(sv=stovol_name, svn=properties['name']))
    else:
        click.echo("Storage volume '{sv}' has been updated.".
                   format(sv=stovol_name))


def cmd_storagevolume_delete(cmd_ctx, stogrp_name, stovol_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stovol = find_storagevolume(cmd_ctx, client, stogrp_name, stovol_name)
    org_options = original_options(options)

    email_insert = org_options['email-insert']
    email_to_addresses = org_options['email-to-address'] or None
    email_cc_addresses = org_options['email-cc-address'] or None

    try:
        stovol.delete(email_to_addresses=email_to_addresses,
                      email_cc_addresses=email_cc_addresses,
                      email_insert=email_insert)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Storage volume '{sv}' has been deleted.".format(sv=stovol_name))


def cmd_storagevolume_fulfill_fcp(cmd_ctx, stogrp_name, stovol_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stovol = find_storagevolume(cmd_ctx, client, stogrp_name, stovol_name)
    cpc = stovol.manager.parent.cpc

    wwpn = options['wwpn']
    lun = options['lun']
    adapter_name = options['adapter']
    port_name = options['port']

    port = find_port(cmd_ctx, client, cpc, adapter_name, port_name)

    try:
        stovol.indicate_fulfillment_fcp(wwpn, lun, port)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Storage boot volume '{sv}' has been indicated as fulfilled.".
               format(sv=stovol_name))
