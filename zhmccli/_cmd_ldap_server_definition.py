# Copyright 2023 IBM Corp. All Rights Reserved.
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
Commands for LDAP server definition management.
"""

from __future__ import absolute_import
from __future__ import print_function

import click

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS


def find_ldapdef(cmd_ctx, console, ldapdef_name):
    """
    Find a LDAP server definition by name and return its resource object.
    """
    try:
        ldapdef = console.ldap_server_definitions.find(
            name=ldapdef_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return ldapdef


@cli.group('ldap', options_metavar=COMMAND_OPTIONS_METAVAR)
def ldapdef_group():
    """
    Command group for managing LDAP server definitions.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@ldapdef_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@add_options(LIST_OPTIONS)
@click.pass_obj
def ldapdef_list(cmd_ctx, **options):
    """
    List the LDAP server definitions.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_ldapdef_list(cmd_ctx, options))


@ldapdef_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('LDAPSD', type=str, metavar='LDAP_SERVER_DEFINITION')
@click.pass_obj
def ldapdef_show(cmd_ctx, ldapsd):
    """
    Show the details of an LDAP server definition.

    The following properties are shown in addition to those returned by the HMC:

    \b
      - 'parent-name' - Name of the parent Console.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_ldapdef_show(cmd_ctx, ldapsd))


@ldapdef_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--name', type=str, required=True,
              help='The name of the new LDAP server definition.')
@click.option('--description', type=str, required=False,
              help='The description of the new LDAP server definition.')
@click.option('--primary-server', type=str, required=True,
              help='The host name or IP address of the primary LDAP server.')
@click.option('--port', type=int, required=False,
              help='The TCP port number of the LDAP servers. Specify 0 to set '
              'to the default of null, which causes the HMC to use the '
              'standard LDAP ports 636 for SSL and 389 for non-SSL.')
@click.option('--backup-server', type=str, required=False,
              help='The host name or IP address of the backup LDAP '
              'server. Specify the empty string to unset the backup '
              'LDAP server. Default: No backup LDAP server.')
@click.option('--use-ssl', type=bool, required=False,
              help='The indicator whether the LDAP servers use SSL. '
              'Default: False')
@click.option('--tolerate-untrusted-certificates', type=bool, required=False,
              help='The indicator whether the LDAP servers should '
              'tolerate self-signed or otherwise untrusted certificates. '
              'Default: False')
@click.option('--bind-distinguished-name', type=str, required=False,
              help='The distinguished name to bind to on the LDAP servers, '
              'or the empty string for anonymous bind. '
              'Default: Anonymous bind.')
@click.option('--bind-password', type=str, required=False,
              help='The password to be used when binding to a '
              'distinguished name on the LDAP servers. Specify the empty '
              'string for anonymous bind. '
              'Default: Anonymous bind.')
@click.option('--location-method', type=click.Choice(['pattern', 'subtree']),
              required=False,
              help='The method the LDAP servers use to locate a user\'s '
              'directory entry. '
              'Default: "pattern"')
@click.option('--search-distinguished-name', type=str, required=True,
              help='The distinguished name to use when searching for a '
              'user\'s directory entry. Use depends on location method.')
@click.option('--search-scope', type=click.Choice(['all', 'one-level']),
              required=False,
              help='The indicator how much of the subtree should be '
              'searched when searching for a user\'s directory entry in a '
              'subtree. Only for location method "subtree". '
              'Default: "all".')
@click.option('--search-filter', type=str, required=False,
              help='The LDAP search filter to use when searching for a '
              'user\'s directory entry in a subtree. Required for location '
              'method "subtree".')
@click.pass_obj
def ldapdef_create(cmd_ctx, **options):
    """
    Create a user-defined LDAP server definition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_ldapdef_create(cmd_ctx, options))


@ldapdef_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('LDAPSD', type=str, metavar='LDAP_SERVER_DEFINITION')
@click.option('--description', type=str, required=False,
              help='The new description of the LDAP server definition.')
@click.option('--primary-server', type=str, required=False,
              help='The new host name or IP address of the primary LDAP '
              'server.')
@click.option('--port', type=int, required=False,
              help='The new TCP port number of the LDAP servers. Specify 0 to '
              'set to the default of null, which causes the HMC to use the '
              'standard LDAP ports 636 for SSL and 389 for non-SSL.')
@click.option('--backup-server', type=str, required=False,
              help='The new host name or IP address of the backup LDAP '
              'server. Specify the empty string to unset the backup LDAP '
              'server.')
@click.option('--use-ssl', type=bool, required=False,
              help='The new indicator whether the LDAP server uses SSL.')
@click.option('--tolerate-untrusted-certificates', type=bool, required=False,
              help='The new indicator whether the LDAP servers should '
              'tolerate self-signed or otherwise untrusted certificates.')
@click.option('--bind-distinguished-name', type=str, required=False,
              help='The new distinguished name to bind to on the LDAP servers, '
              'or the empty string for anonymous bind.')
@click.option('--bind-password', type=str, required=False,
              help='The new password to be used when binding to a '
              'distinguished name on the LDAP servers. Specify the empty '
              'string for anonymous bind.')
@click.option('--location-method', type=click.Choice(['pattern', 'subtree']),
              required=False,
              help='The new method the LDAP servers use to locate a user\'s '
              'directory entry.')
@click.option('--search-distinguished-name', type=str, required=False,
              help='The new distinguished name to use when searching for a '
              'user\'s directory entry. Use depends on location method.')
@click.option('--search-scope', type=click.Choice(['all', 'one-level']),
              required=False,
              help='The new indicator how much of the subtree should be '
              'searched when searching for a user\'s directory entry in a '
              'subtree. Only for location method "subtree".')
@click.option('--search-filter', type=str, required=False,
              help='The new LDAP search filter to use when searching for a '
              'user\'s directory entry in a subtree. Only for location method '
              '"subtree".')
@click.pass_obj
def ldapdef_update(cmd_ctx, ldapsd, **options):
    """
    Update the properties of an LDAP server definition.

    Note that LDAP server definitions cannot be renamed.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_ldapdef_update(cmd_ctx, ldapsd, options))


@ldapdef_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('LDAPSD', type=str, metavar='LDAP_SERVER_DEFINITION')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the LDAP server '
              'definition.',
              prompt='Are you sure you want to delete this LDAP server '
              'definition ?')
@click.pass_obj
def ldapdef_delete(cmd_ctx, ldapsd):
    """
    Delete a user-defined LDAP server definition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_ldapdef_delete(cmd_ctx, ldapsd))


def cmd_ldapdef_list(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    show_list = [
        'name',
    ]
    if not options['names_only']:
        show_list.extend([
            'description',
            'location-method',
            'description',
        ])
    if options['uri']:
        show_list.extend([
            'element-uri',
        ])

    additions = {}

    try:
        ldapdefs = console.ldap_server_definitions.list(
            full_properties=False)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    try:
        print_resources(cmd_ctx, ldapdefs, cmd_ctx.output_format,
                        show_list, additions, all=options['all'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_ldapdef_show(cmd_ctx, ldapdef_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    ldapdef = find_ldapdef(cmd_ctx, console, ldapdef_name)

    try:
        ldapdef.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(ldapdef.properties)

    # Add artificial property 'parent-name'
    properties['parent-name'] = console.name

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def cmd_ldapdef_create(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    name_map = {
        'primary-server': 'primary-hostname-ipaddr',
        'backup-server': 'backup-hostname-ipaddr',
        'port': 'connection-port',
    }
    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    # Handle special values
    for prop in ('connection-port',):
        if prop in properties and properties[prop] == 0:
            properties[prop] = None
    for prop in ('backup-hostname-ipaddr', 'bind-distinguished-name',
                 'bind-password'):
        if prop in properties and properties[prop] == '':
            properties[prop] = None

    try:
        new_ldapdef = console.ldap_server_definitions.create(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("New LDAP server definition '{lsd}' has been created.".
               format(lsd=new_ldapdef.properties['name']))


def cmd_ldapdef_update(cmd_ctx, ldapdef_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    ldapdef = find_ldapdef(cmd_ctx, console, ldapdef_name)

    name_map = {
        'primary-server': 'primary-hostname-ipaddr',
        'backup-server': 'backup-hostname-ipaddr',
        'port': 'connection-port',
    }
    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    # Handle special values
    for prop in ('connection-port',):
        if prop in properties and properties[prop] == 0:
            properties[prop] = None
    for prop in ('backup-hostname-ipaddr', 'bind-distinguished-name',
                 'bind-password'):
        if prop in properties and properties[prop] == '':
            properties[prop] = None

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating LDAP server "
                   "definition '{lsd}'.".
                   format(lsd=ldapdef_name))
        return

    try:
        ldapdef.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("LDAP server definition '{lsd}' has been updated.".
               format(lsd=ldapdef_name))


def cmd_ldapdef_delete(cmd_ctx, ldapdef_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    ldapdef = find_ldapdef(cmd_ctx, console, ldapdef_name)

    try:
        ldapdef.delete()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("LDAP server definition '{lsd}' has been deleted.".
               format(lsd=ldapdef_name))
