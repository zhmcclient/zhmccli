# Copyright 2024 IBM Corp. All Rights Reserved.
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
Commands for HMC user pattern management.
"""

from __future__ import absolute_import
from __future__ import print_function

import click

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS, parse_yaml_flow_style


# Special default for retention-time when creating
DEFAULT_RETENTION_TIME = 1


def find_user_pattern(cmd_ctx, console, user_pattern_name):
    """
    Find a user pattern by name and return its resource object.
    """
    try:
        user_pattern = console.user_patterns.find(name=user_pattern_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return user_pattern


@cli.group('userpattern', options_metavar=COMMAND_OPTIONS_METAVAR)
def user_pattern_group():
    """
    Command group for managing HMC user patterns.

    User patterns are used when an LDAP user logs on to the HMC. The userid is
    matched against all user patterns, and the matching user pattern identifies
    a user template (i.e. a User object of type template) in one of several
    ways, that is then used to create a pattern-based User object for the
    userid that logs on.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@user_pattern_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@add_options(LIST_OPTIONS)
@click.pass_obj
def user_pattern_list(cmd_ctx, **options):
    """
    List the HMC user patterns.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_user_pattern_list(cmd_ctx, options))


@user_pattern_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('USER_PATTERN', type=str, metavar='USER_PATTERN')
@click.pass_obj
def user_pattern_show(cmd_ctx, user_pattern):
    """
    Show the details of an HMC user pattern.

    The following properties are shown in addition to those returned by the HMC:

    \b
      - 'parent-name' - Name of the parent Console.
      - 'specific-template-name' -
        Name of the user template referenced by
        'specific-template-uri'.
      - 'template-name-override-ldap-server-definition-name' -
        Name of the LDAP Server Definition referenced by
        'template-name-override-ldap-server-definition-uri'.
      - 'template-name-override-default-template-name' -
        Name of the user template referenced by
        'template-name-override-default-template-uri'.
      - 'ldap-group-ldap-server-definition-name' -
        Name of the LDAP Server Definition referenced by
        'ldap-group-ldap-server-definition-uri'.
      - 'ldap-group-default-template-name' -
        Name of the user template referenced by
        'ldap-group-default-template-uri'.
      - 'domain-name-restrictions-ldap-server-definition-name' -
        Name of the LDAP Server Definition referenced by
        'domain-name-restrictions-ldap-server-definition-uri'.

    The following old properties are shown that are set by the HMC to be
    consistent with the preferred new properties:

    \b
      - 'ldap-server-definition-name' -
        Name of the LDAP Server Definition referenced by
        'ldap-server-definition-uri'.
      - 'user-template-name' -
        Name of the specific user template referenced by
        'user-template-uri'.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_user_pattern_show(cmd_ctx, user_pattern))


@user_pattern_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--name', type=str, required=True,
              help='The name of the new user pattern.')
@click.option('--description', type=str, required=False,
              help='The description of the new user pattern.')
@click.option('--pattern', type=str, required=True,
              help='The pattern for matching userids. '
              'The combination of "pattern" and "type" must be unique.')
@click.option('--type', type=click.Choice(['glob-like', 'regular-expression']),
              required=True,
              help='The style in which the pattern is expressed.')
@click.option('--retention-time', type=int, required=False,
              default=DEFAULT_RETENTION_TIME,
              help='The time in days that the pattern-based users created '
              'based on this user pattern will be retained after being '
              'created. '
              'A value of 0 indicates not to retain the users after being '
              'created. '
              'Default: {}'.format(DEFAULT_RETENTION_TIME))
@click.option('--specific-template', type=str, required=False,
              # HMC property: 'specific-template-uri/name'
              help='Direct template identification: '
              'The name of the user template to be used. '
              'Default: This template identification method is not used. '
              'HMC property: specific-template-uri/name')
@click.option('--ldap-template-lsd', type=str, required=False,
              # HMC property: 'template-name-override-ldap-server-definition-
              #   uri/name'
              help='LDAP attribute lookup based template identification: '
              'The name of the LDAP Server Definition object identifying '
              'the LDAP server used for lookup of the attribute that specifies '
              'the name of the user template to be used. '
              'Default: This template identification method is not used. '
              'HMC property: template-name-override-ldap-server-'
              'definition-uri/name')
@click.option('--ldap-template-attr', type=str, required=False,
              # HMC property: 'template-name-override'
              help='LDAP attribute lookup based template identification: '
              'The name of the LDAP attribute on the LDAP server that '
              'specifies the name of the user template to be used. '
              'Default: This template identification method is not used. '
              'HMC property: template-name-override')
@click.option('--ldap-template-default', type=str, required=False,
              # HMC property: 'template-name-override-default-template-uri/name'
              help='LDAP attribute lookup based template identification: '
              'The name of the user template to be used when the LDAP '
              'server did not yield a template name. '
              'If not specified, the logon will fail in that case. '
              'Default: This template identification method is not used. '
              'HMC property: template-name-override-default-template-uri/name')
@click.option('--ldap-group-template-lsd', type=str, required=False,
              # HMC property: 'ldap-group-ldap-server-definition-uri/name'
              help='LDAP group lookup based template identification: '
              'The name of the LDAP Server Definition object identifying '
              'the LDAP server used for LDAP group lookup of the user '
              'template name. '
              'Default: This template identification method is not used. '
              'HMC property: ldap-group-ldap-server-definition-uri/name')
@click.option('--ldap-group-template-mappings', type=str, required=False,
              # HMC property: 'ldap-group-to-template-mappings'
              help='LDAP group lookup based template identification: '
              'The mappings from LDAP group names to HMC user '
              'template names, as a dict in YAML Flow Collection style. '
              'The dict key is the LDAP group name, and the dict value is the '
              'name of the template user. '
              'The specified mapping fully replaces the existing mapping in '
              'the HMC. '
              'Default: This template identification method is not used. '
              'HMC property: ldap-group-to-template-mappings. '
              'Example: --ldap-group-template-mappings "{ldap-group-1: '
              'hmc-user-1}"')
@click.option('--ldap-group-template-default', type=str, required=False,
              # HMC property: 'ldap-group-default-template-uri/name'
              help='LDAP group lookup based template identification: '
              'The name of the user template to be used when the LDAP '
              'server does not yield a template name. '
              'If not specified, the logon will fail in that case. '
              'Default: This template identification method is not used. '
              'HMC property: ldap-group-default-template-uri/name')
@click.option('--domain-name-restrictions-lsd', type=str, required=False,
              # HMC property: 'domain-name-restrictions-ldap-server-definition-
              #   uri/name'
              help='Name of the LDAP Server Definition object that '
              'identifies the LDAP server that is used for lookup of the '
              'domain name restrictions. '
              'Default: There are no such restrictions. '
              'HMC property: domain-name-restrictions-ldap-server-'
              'definition-uri/name')
@click.option('--domain-name-restrictions-attr', type=str, required=False,
              # HMC property: 'domain-name-restrictions'
              help='Name of the LDAP attribute on the LDAP server that '
              'is used for lookup of the domain name restrictions, which '
              'specifies the domain name restrictions (i.e. to which consoles '
              'the pattern-based user may log on to). '
              'Default: There are no such restrictions. '
              'HMC property: domain-name-restrictions')
@click.pass_obj
def user_pattern_create(cmd_ctx, **options):
    """
    Create an HMC user pattern.

    The user template to be used when creating the pattern-based user for
    the LDAP user that logs on must be identified using one of these methods.
    The properties related to the methods that are not used, will be reset:

    \b
    * directly by specifying a user template name (--specific-template option)
    * via LDAP attribute lookup (--ldap-template-... options)
    * via LDAP group lookup (--ldap-group-template-... options)

    For some options, the corresponding HMC properties are different than
    the option names. In such cases, the option descriptions mention the
    corresponding HMC property names.

    There are some old properties that are set by the HMC consistent with
    the preferred new properties. Because of that, the old properties have
    no corresponding options and the options for the new preferred properties
    should be used instead. The old properties are:

    \b
    * ldap-server-definition-uri:
      Name of LDAP Server Definition object used for LDAP attribute lookup for
      specific user template name and domain name restrictions. Use the
      --ldap-template-lsd and --domain-name-restrictions-lsd options instead.
    * user-template-uri:
      Name of the specific user template to be used. Use the
      --specific-template option instead.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_user_pattern_create(cmd_ctx, options))


@user_pattern_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('USER_PATTERN', type=str, metavar='USER_PATTERN')
@click.option('--name', type=str, required=False,
              help='The new name of the user pattern.')
@click.option('--description', type=str, required=False,
              help='The new description of the user pattern.')
@click.option('--pattern', type=str, required=False,
              help='The new pattern for matching userids. '
              'The combination of "pattern" and "type" must be unique.')
@click.option('--type', type=click.Choice(['glob-like', 'regular-expression']),
              required=False,
              help='The new style in which the pattern is expressed.')
@click.option('--retention-time', type=int, required=False,
              help='The new time in days that the pattern-based users created '
              'based on this user pattern will be retained after being '
              'created. '
              'A value of 0 indicates not to retain the users after being '
              'created.')
@click.option('--specific-template', type=str, required=False,
              # HMC property: 'specific-template-uri/name'
              help='Direct template identification: '
              'The new name of the user template to be used. '
              'The empty string disables this template identification method. '
              'HMC property: specific-template-uri/name')
@click.option('--ldap-template-lsd', type=str, required=False,
              # HMC property: 'template-name-override-ldap-server-definition-
              #   uri/name'
              help='LDAP attribute lookup based template identification: '
              'The new name of the LDAP Server Definition object identifying '
              'the LDAP server used for lookup of the attribute that specifies '
              'the name of the user template to be used. '
              'The empty string disables this template identification method. '
              'HMC property: template-name-override-ldap-server-'
              'definition-uri/name')
@click.option('--ldap-template-attr', type=str, required=False,
              # HMC property: 'template-name-override'
              help='LDAP attribute lookup based template identification: '
              'The new name of the LDAP attribute on the LDAP server that '
              'specifies the name of the user template to be used. '
              'The empty string disables this template identification method. '
              'HMC property: template-name-override')
@click.option('--ldap-template-default', type=str, required=False,
              # HMC property: 'template-name-override-default-template-uri/name'
              help='LDAP attribute lookup based template identification: '
              'The new name of the user template to be used when the LDAP '
              'server did not yield a template name. '
              'If not specified, the logon will fail in that case. '
              'The empty string disables this template identification method. '
              'HMC property: template-name-override-default-template-uri/name')
@click.option('--ldap-group-template-lsd', type=str, required=False,
              # HMC property: 'ldap-group-ldap-server-definition-uri/name'
              help='LDAP group lookup based template identification: '
              'The new name of the LDAP Server Definition object identifying '
              'the LDAP server used for LDAP group lookup of the user '
              'template name. '
              'The empty string disables this template identification method. '
              'HMC property: ldap-group-ldap-server-definition-uri/name')
@click.option('--ldap-group-template-mappings', type=str, required=False,
              # HMC property: 'ldap-group-to-template-mappings'
              help='LDAP group lookup based template identification: '
              'The new mappings from LDAP group names to HMC user '
              'template names, as a dict in YAML Flow Collection style. '
              'The dict key is the LDAP group name, and the dict value is the '
              'name of the template user. '
              'The specified mapping fully replaces the existing mapping in '
              'the HMC. '
              'The empty string disables this template identification method. '
              'HMC property: ldap-group-to-template-mappings. '
              'Example: --ldap-group-template-mappings "{ldap-group-1: '
              'hmc-user-1}"')
@click.option('--ldap-group-template-default', type=str, required=False,
              # HMC property: 'ldap-group-default-template-uri/name'
              help='LDAP group lookup based template identification: '
              'The new name of the user template to be used when the LDAP '
              'server does not yield a template name. '
              'If not specified, the logon will fail in that case. '
              'The empty string disables this template identification method. '
              'HMC property: ldap-group-default-template-uri/name')
@click.option('--domain-name-restrictions-lsd', type=str, required=False,
              # HMC property: 'domain-name-restrictions-ldap-server-definition-
              #   uri/name'
              help='The new name of the LDAP Server Definition object that '
              'identifies the LDAP server that is used for lookup of the '
              'domain name restrictions. '
              'The empty string sets no such restrictions. '
              'HMC property: domain-name-restrictions-ldap-server-'
              'definition-uri/name')
@click.option('--domain-name-restrictions-attr', type=str, required=False,
              # HMC property: 'domain-name-restrictions'
              help='The new name of the LDAP attribute on the LDAP server that '
              'is used for lookup of the domain name restrictions, which '
              'specifies the domain name restrictions (i.e. to which consoles '
              'the pattern-based user may log on to). '
              'The empty string sets no such restrictions. '
              'HMC property: domain-name-restrictions')
@click.pass_obj
def user_pattern_update(cmd_ctx, user_pattern, **options):
    """
    Update the properties of an HMC user pattern.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    The user template to be used when creating the pattern-based user for
    the LDAP user that logs on must be identified using one of these methods.
    The properties related to the methods that are not used, will be reset:

    \b
    * directly by specifying a user template name (--specific-template option)
    * via LDAP attribute lookup (--ldap-template-... options)
    * via LDAP group lookup (--ldap-group-template-... options)

    For some options, the corresponding HMC properties are different than
    the option names. In such cases, the option descriptions mention the
    corresponding HMC property names.

    There are some old properties that are set by the HMC consistent with
    the preferred new properties. Because of that, the old properties have
    no corresponding options and the options for the new preferred properties
    should be used instead. The old properties are:

    \b
    * ldap-server-definition-uri:
      Name of LDAP Server Definition object used for LDAP attribute lookup for
      specific user template name and domain name restrictions. Use the
      --ldap-template-lsd and --domain-name-restrictions-lsd options instead.
    * user-template-uri:
      Name of the specific user template to be used. Use the
      --specific-template option instead.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_user_pattern_update(
        cmd_ctx, user_pattern, options))


@user_pattern_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('USER_PATTERN', type=str, metavar='USER_PATTERN')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the user pattern.',
              prompt='Are you sure you want to delete this user pattern ?')
@click.pass_obj
def user_pattern_delete(cmd_ctx, user_pattern):
    """
    Delete an HMC user pattern.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_user_pattern_delete(
        cmd_ctx, user_pattern))


def cmd_user_pattern_list(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    show_list = [
        'name',
    ]
    if not options['names_only']:
        show_list.extend([
            'type',
            'pattern',
            'description',
        ])
    if options['uri']:
        show_list.extend([
            'element-uri',
        ])

    additions = {}

    try:
        user_patterns = console.user_patterns.list(full_properties=False)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    try:
        print_resources(cmd_ctx, user_patterns, cmd_ctx.output_format,
                        show_list, additions, all=options['all'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_user_pattern_show(cmd_ctx, user_pattern_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    user_pattern = find_user_pattern(cmd_ctx, console, user_pattern_name)

    try:
        user_pattern.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(user_pattern.properties)

    users = console.users.list(filter_args={'type': 'template'})
    lsds = console.ldap_server_definitions.list()

    def _add_user_prop(users, properties, stem):
        uri = properties[stem + 'uri']
        name_prop = stem + 'name'
        if uri:
            objs = [user for user in users if user.uri == uri]
            assert len(objs) == 1
            obj = objs[0]
            properties[name_prop] = obj.name
        else:
            properties[name_prop] = None

    def _add_lsd_prop(lsds, properties, stem):
        uri = properties[stem + 'uri']
        name_prop = stem + 'name'
        if uri:
            objs = [lsd for lsd in lsds if lsd.uri == uri]
            assert len(objs) == 1
            obj = objs[0]
            properties[name_prop] = obj.name
        else:
            properties[name_prop] = None

    properties['parent-name'] = console.name
    _add_user_prop(users, properties, 'specific-template-')
    _add_lsd_prop(lsds, properties,
                  'template-name-override-ldap-server-definition-')
    _add_user_prop(users, properties,
                   'template-name-override-default-template-')
    _add_lsd_prop(lsds, properties, 'ldap-group-ldap-server-definition-')
    _add_user_prop(users, properties, 'ldap-group-default-template-')
    _add_lsd_prop(lsds, properties,
                  'domain-name-restrictions-ldap-server-definition-')
    _add_lsd_prop(lsds, properties, 'ldap-server-definition-')
    _add_user_prop(users, properties, 'user-template-')

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def artificial_properties_name_map():
    """
    Return name_map for options_to_properties() for artificial properties.
    """
    return {
        'specific-template': None,
        'ldap-template-lsd': None,
        'ldap-template-attr': 'template-name-override',
        'ldap-template-default': None,
        'ldap-group-template-lsd': None,
        'ldap-group-template-mappings': None,
        'ldap-group-template-default': None,
        'domain-name-restrictions-lsd': None,
        'domain-name-restrictions-attr': 'domain-name-restrictions',
        'old-ldap-lsd': None,
        'old-user-template': None,
    }


def _add_special_name_option(
        cmd_ctx, mgr, properties, org_options, opt_name, prop_name):
    """
    Add an URI property from a name option.
    """
    if org_options[opt_name] is None:
        pass  # omit -> no change
    elif org_options[opt_name] == '':
        properties[prop_name] = None
    else:
        try:
            user = mgr.find_by_name(org_options[opt_name])
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)
        properties[prop_name] = user.uri


def add_special_options(cmd_ctx, console, properties, org_options):
    """
    Add properties from options that need special handling.
    """
    _add_special_name_option(
        cmd_ctx, console.users, properties, org_options,
        'specific-template',
        'specific-template-uri')
    _add_special_name_option(
        cmd_ctx, console.ldap_server_definitions, properties, org_options,
        'ldap-template-lsd',
        'template-name-override-ldap-server-definition-uri')
    _add_special_name_option(
        cmd_ctx, console.users, properties, org_options,
        'ldap-template-default',
        'template-name-override-default-template-uri')
    _add_special_name_option(
        cmd_ctx, console.ldap_server_definitions, properties, org_options,
        'ldap-group-template-lsd',
        'ldap-group-ldap-server-definition-uri')
    _add_special_name_option(
        cmd_ctx, console.users, properties, org_options,
        'ldap-group-template-default',
        'ldap-group-default-template-uri')
    _add_special_name_option(
        cmd_ctx, console.ldap_server_definitions, properties, org_options,
        'domain-name-restrictions-lsd',
        'domain-name-restrictions-ldap-server-definition-uri')
    _add_special_name_option(
        cmd_ctx, console.ldap_server_definitions, properties, org_options,
        'old-ldap-lsd',
        'ldap-server-definition-uri')
    _add_special_name_option(
        cmd_ctx, console.users, properties, org_options,
        'old-user-template',
        'user-template-uri')

    opt_name = 'ldap-group-template-mappings'
    _opt_name = '--' + opt_name
    prop_name = 'ldap-group-to-template-mappings'
    opt_value = org_options[opt_name]
    if opt_value is None:
        pass  # omit -> no change
    elif opt_value == '':
        properties[prop_name] = None
    else:
        value = parse_yaml_flow_style(cmd_ctx, _opt_name, opt_value)
        if not isinstance(value, dict):
            raise click_exception(
                "Option {} must specify a dictionary, but specified: {!r} "
                "(parsed: {!r})".
                format(_opt_name, opt_value, value), cmd_ctx.error_format)
        prop_value = []
        for ldap_group, template_name in value.items():
            try:
                template = console.users.find_by_name(template_name)
            except zhmcclient.Error as exc:
                raise click_exception(exc, cmd_ctx.error_format)
            prop_value.append({
                'ldap-group-name': ldap_group,
                'template-uri': template.uri,
            })
        properties[prop_name] = prop_value


def cmd_user_pattern_create(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    org_options = original_options(options)

    name_map = artificial_properties_name_map()
    properties = options_to_properties(org_options, name_map)
    add_special_options(cmd_ctx, console, properties, org_options)

    try:
        new_user_pattern = console.user_patterns.create(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("New user pattern '{r}' has been created.".
               format(r=new_user_pattern.properties['name']))


def cmd_user_pattern_update(cmd_ctx, user_pattern_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    user_pattern = find_user_pattern(cmd_ctx, console, user_pattern_name)

    org_options = original_options(options)
    name_map = artificial_properties_name_map()
    properties = options_to_properties(org_options, name_map)
    add_special_options(cmd_ctx, console, properties, org_options)

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating user pattern '{r}'.".
                   format(r=user_pattern_name))
        return

    try:
        user_pattern.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("User pattern '{r}' has been updated.".
               format(r=user_pattern_name))


def cmd_user_pattern_delete(cmd_ctx, user_pattern_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    user_pattern = find_user_pattern(cmd_ctx, console, user_pattern_name)

    try:
        user_pattern.delete()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("User pattern '{r}' has been deleted.".
               format(r=user_pattern_name))
