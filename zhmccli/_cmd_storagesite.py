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
Commands for storage sites in the FICON storage configuration.
"""


import click

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS, FILTER_OPTIONS, \
    build_filter_args, SORT_OPTIONS, build_sort_props


def find_storagesite(cmd_ctx, client, stosite_name):
    """
    Find a storage site by name and return its resource object.
    """
    console = client.consoles.console
    try:
        stosite = console.storage_sites.find(name=stosite_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return stosite


@cli.group('storagesite', options_metavar=COMMAND_OPTIONS_METAVAR)
def storagesite_group():
    """
    Command group for managing storage sites.

    A storage site describes a location housing storage switches and storage
    subsystems in the FICON storage configuration of a DPM-enabled CPC. A
    primary site always exists and cannot be deleted.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@storagesite_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@add_options(LIST_OPTIONS)
@add_options(FILTER_OPTIONS)
@add_options(SORT_OPTIONS)
@click.pass_obj
def storagesite_list(cmd_ctx, **options):
    """
    List the storage sites defined in the HMC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_storagesite_list(cmd_ctx, options))


@storagesite_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGESITE', type=str, metavar='STORAGESITE')
@click.pass_obj
def storagesite_show(cmd_ctx, storagesite):
    """
    Show the details of a storage site.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_storagesite_show(cmd_ctx, storagesite))


@storagesite_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--name', type=str, required=True,
              help='The name of the new storage site.')
@click.option('--description', type=str, required=False,
              help='The description of the new storage site. Default: Empty.')
@click.pass_obj
def storagesite_create(cmd_ctx, **options):
    """
    Create an alternate storage site.

    Only alternate storage sites can be created. The primary site always
    exists and cannot be created via this command.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_storagesite_create(cmd_ctx, options))


@storagesite_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGESITE', type=str, metavar='STORAGESITE')
@click.option('--name', type=str, required=False,
              help='The new name of the storage site.')
@click.option('--description', type=str, required=False,
              help='The new description of the storage site.')
@click.pass_obj
def storagesite_update(cmd_ctx, storagesite, **options):
    """
    Update the properties of a storage site.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagesite_update(cmd_ctx, storagesite, options))


@storagesite_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('STORAGESITE', type=str, metavar='STORAGESITE')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the storage site.',
              prompt='Are you sure you want to delete this storage site ?')
@click.pass_obj
def storagesite_delete(cmd_ctx, storagesite, **options):
    """
    Delete an alternate storage site.

    Only alternate storage sites can be deleted. The primary site cannot be
    deleted.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_storagesite_delete(cmd_ctx, storagesite, options))


def cmd_storagesite_list(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    filter_args = build_filter_args(cmd_ctx, options['filter'])

    try:
        stosites = console.storage_sites.list(filter_args=filter_args)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    show_list = [
        'name',
    ]
    if not options['names_only']:
        show_list.extend([
            'type',
            'description',
        ])
    if options['uri']:
        show_list.extend([
            'object-uri',
        ])

    sort_props = build_sort_props(cmd_ctx, options['sort'], default=['name'])
    try:
        print_resources(cmd_ctx, stosites, cmd_ctx.output_format, show_list,
                        None, all=options['all'], sort_props=sort_props)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_storagesite_show(cmd_ctx, stosite_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    stosite = find_storagesite(cmd_ctx, client, stosite_name)

    try:
        stosite.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(stosite.properties)

    # Add artificial property 'parent-name'
    properties['parent-name'] = console.name

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def cmd_storagesite_create(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    org_options = original_options(options)
    properties = options_to_properties(org_options, {})

    try:
        new_stosite = console.storage_sites.create(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("New storage site '{ss}' has been created.".
               format(ss=new_stosite.properties['name']))


def cmd_storagesite_update(cmd_ctx, stosite_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    stosite = find_storagesite(cmd_ctx, client, stosite_name)

    org_options = original_options(options)
    properties = options_to_properties(org_options, {})

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating storage site "
                   "'{ss}'.".format(ss=stosite_name))
        return

    try:
        stosite.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    if 'name' in properties and properties['name'] != stosite_name:
        click.echo("Storage site '{ss}' has been renamed to '{ssn}' and was "
                   "updated.".
                   format(ss=stosite_name, ssn=properties['name']))
    else:
        click.echo("Storage site '{ss}' has been updated.".
                   format(ss=stosite_name))


def cmd_storagesite_delete(cmd_ctx, stosite_name, options):
    # pylint: disable=missing-function-docstring,unused-argument

    client = zhmcclient.Client(cmd_ctx.session)
    stosite = find_storagesite(cmd_ctx, client, stosite_name)

    try:
        stosite.delete()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Storage site '{ss}' has been deleted.".
               format(ss=stosite_name))
