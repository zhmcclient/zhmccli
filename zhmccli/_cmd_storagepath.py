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
Commands for storage paths within storage control units.
"""


import click

import zhmcclient
from .zhmccli import cli
from ._cmd_storagecontrolunit import find_storagecontrolunit
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS, FILTER_OPTIONS, \
    build_filter_args, SORT_OPTIONS, build_sort_props


@cli.group('storagepath', options_metavar=COMMAND_OPTIONS_METAVAR)
def storagepath_group():
    """
    Command group for managing storage paths.

    A storage path defines a communication path from a storage control unit
    to a storage adapter, optionally through one or two storage switches.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@storagepath_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGECONTROLUNIT', type=str, metavar='STORAGECONTROLUNIT')
@add_options(LIST_OPTIONS)
@add_options(FILTER_OPTIONS)
@add_options(SORT_OPTIONS)
@click.pass_obj
def storagepath_list(cmd_ctx, storagecontrolunit, **options):
    """
    List the storage paths of a storage control unit.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagepath_list(cmd_ctx, storagecontrolunit, options))


@storagepath_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGECONTROLUNIT', type=str, metavar='STORAGECONTROLUNIT')
@click.argument('STORAGEPATH', type=str, metavar='STORAGEPATH')
@click.pass_obj
def storagepath_show(cmd_ctx, storagecontrolunit, storagepath):
    """
    Show the details of a storage path.

    STORAGEPATH is the element-uri of the storage path.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagepath_show(
            cmd_ctx, storagecontrolunit, storagepath))


@storagepath_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGECONTROLUNIT', type=str, metavar='STORAGECONTROLUNIT')
@click.option('--adapter-port-uri', type=str, required=True,
              help='The URI of the adapter port for this storage path.')
@click.option('--exit-switch-uri', type=str, required=False,
              help='The URI of the exit storage switch for this path.')
@click.option('--exit-port', type=str, required=False,
              help='A two-character lowercase hex port ID on the exit storage '
              'switch.')
@click.pass_obj
def storagepath_create(cmd_ctx, storagecontrolunit, **options):
    """
    Create a new storage path in a storage control unit.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagepath_create(
            cmd_ctx, storagecontrolunit, options))


@storagepath_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGECONTROLUNIT', type=str, metavar='STORAGECONTROLUNIT')
@click.argument('STORAGEPATH', type=str, metavar='STORAGEPATH')
@click.option('--adapter-port-uri', type=str, required=False,
              help='The new URI of the adapter port for this storage path.')
@click.option('--exit-switch-uri', type=str, required=False,
              help='The new URI of the exit storage switch for this path.')
@click.option('--exit-port', type=str, required=False,
              help='A two-character lowercase hex port ID on the exit storage '
              'switch.')
@click.pass_obj
def storagepath_update(cmd_ctx, storagecontrolunit, storagepath, **options):
    """
    Update the properties of a storage path.

    STORAGEPATH is the element-uri of the storage path.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagepath_update(
            cmd_ctx, storagecontrolunit, storagepath, options))


@storagepath_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGECONTROLUNIT', type=str, metavar='STORAGECONTROLUNIT')
@click.argument('STORAGEPATH', type=str, metavar='STORAGEPATH')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the storage path.',
              prompt='Are you sure you want to delete this storage path ?')
@click.pass_obj
def storagepath_delete(cmd_ctx, storagecontrolunit, storagepath, **options):
    """
    Delete a storage path from a storage control unit.

    STORAGEPATH is the element-uri of the storage path.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagepath_delete(
            cmd_ctx, storagecontrolunit, storagepath, options))


def cmd_storagepath_list(cmd_ctx, stocu_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stocu = find_storagecontrolunit(cmd_ctx, client, stocu_name)

    filter_args = build_filter_args(cmd_ctx, options['filter'])

    try:
        stopaths = stocu.storage_paths.list(filter_args=filter_args)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    show_list = [
        'element-uri',
    ]
    if not options['names_only']:
        show_list.extend([
            'adapter-port-uri',
        ])

    sort_props = build_sort_props(
        cmd_ctx, options['sort'], default=['element-uri'])
    try:
        print_resources(cmd_ctx, stopaths, cmd_ctx.output_format, show_list,
                        None, all=options['all'], sort_props=sort_props)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_storagepath_show(cmd_ctx, stocu_name, stopath_id):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stocu = find_storagecontrolunit(cmd_ctx, client, stocu_name)

    try:
        stopath = stocu.storage_paths.find(**{'element-uri': stopath_id})
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    try:
        stopath.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(stopath.properties)

    # Add artificial property 'parent-name'
    properties['parent-name'] = stocu_name

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def cmd_storagepath_create(cmd_ctx, stocu_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stocu = find_storagecontrolunit(cmd_ctx, client, stocu_name)

    org_options = original_options(options)
    properties = options_to_properties(org_options, {})

    try:
        new_stopath = stocu.storage_paths.create(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("New storage path '{sp}' has been created in storage control "
               "unit '{cu}'.".
               format(sp=new_stopath.uri, cu=stocu_name))


def cmd_storagepath_update(cmd_ctx, stocu_name, stopath_id, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stocu = find_storagecontrolunit(cmd_ctx, client, stocu_name)

    try:
        stopath = stocu.storage_paths.find(**{'element-uri': stopath_id})
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    org_options = original_options(options)
    properties = options_to_properties(org_options, {})

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating storage path '{sp}'.".
                   format(sp=stopath_id))
        return

    try:
        stopath.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Storage path '{sp}' has been updated.".
               format(sp=stopath_id))


def cmd_storagepath_delete(cmd_ctx, stocu_name, stopath_id, options):
    # pylint: disable=missing-function-docstring,unused-argument

    client = zhmcclient.Client(cmd_ctx.session)
    stocu = find_storagecontrolunit(cmd_ctx, client, stocu_name)

    try:
        stopath = stocu.storage_paths.find(**{'element-uri': stopath_id})
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    try:
        stopath.delete()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Storage path '{sp}' has been deleted from storage control "
               "unit '{cu}'.".
               format(sp=stopath_id, cu=stocu_name))
