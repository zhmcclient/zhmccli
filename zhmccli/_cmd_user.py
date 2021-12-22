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
Commands for HMC user management.
"""

from __future__ import absolute_import
from __future__ import print_function

import click

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS, ObjectByUriCache


def find_user(cmd_ctx, console, user_name):
    """
    Find a user by name and return its resource object.
    """
    try:
        user = console.users.find(name=user_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return user


@cli.group('user', options_metavar=COMMAND_OPTIONS_METAVAR)
def user_group():
    """
    Command group for managing HMC users.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@user_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@add_options(LIST_OPTIONS)
@click.option('--permissions', is_flag=True, required=False,
              help='Show additional properties for user permissions and roles.')
@click.option('--status', is_flag=True, required=False,
              help='Show additional properties for user status.')
@click.pass_obj
def user_list(cmd_ctx, **options):
    """
    List the HMC users.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_user_list(cmd_ctx, options))


@user_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('USER', type=str, metavar='USER')
@click.pass_obj
def user_show(cmd_ctx, user):
    """
    Show the details of an HMC user.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_user_show(cmd_ctx, user))


@user_group.command('password', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('USER', type=str, metavar='USER')
@click.pass_obj
def user_password(cmd_ctx, user):
    """
    Set a new password for an HMC user.

    The new password is prompted for.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_user_password(cmd_ctx, user))


@user_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--name', type=str, required=True,
              help='The name of the new user.')
@click.option('--like', type=str, required=False,
              help='The name of a like user. The properties of the like user '
              'will be used as defaults for the new user, except for the '
              'following properties: name, password, description, '
              'email-address, mfa-userid, mfa-userid-override. These defaults '
              'can be overridden using options.')
@click.option('--type', type=click.Choice(['standard', 'template']),
              required=False, default='standard',
              help='The type of the new user. '
              'Default: standard')
@click.option('--description', type=str, required=False,
              help='The description of the new user.')
@click.option('--email-address', type=str, required=False,
              help='The email address of the new user, or the empty string to '
              'set no email address. '
              'Default: No email address')
@click.option('--disabled', type=bool, required=False,
              help='The disabled state of the new user. '
              'Default: False')
@click.option('--authentication-type', type=click.Choice(['local', 'ldap']),
              required=False, default='local',
              help='The authentication type of the new user. '
              'Default: local')
@click.option('--password-rule', type=str, required=False,
              help='The name of the password rule of the new user. '
              'Only valid and required with authentication type "local".')
@click.option('--password', type=str, required=False,
              help='The logon password for the new user. '
              'Only valid and required with authentication type "local".')
@click.option('--force-password-change', type=bool, required=False,
              help='The force-password-change state of the new user. '
              'Only valid with authentication type "local". '
              'Default: False')
@click.option('--ldap-server-definition', type=str, required=False,
              help='The name of the LDAP server definition of the new user, or '
              'the empty string to set no LDAP server definition. '
              'Only valid and required with authentication type "ldap".')
@click.option('--userid-on-ldap-server', type=str, required=False,
              help='The userid on the LDAP server. '
              'Only valid with authentication type "ldap".')
@click.option('--session-timeout', type=int, required=False,
              help='The session timeout in minutes for the new user. '
              'This is the amount of time for which a user\'s UI session can '
              'run before being prompted for identity verification. '
              '0 indicates no timeout. '
              'Default: 0')
@click.option('--verify-timeout', type=int, required=False,
              help='The verification timeout in minutes for the new user. '
              'This is the amount of time allowed for the user to re-enter '
              'their password when being prompted due to a session timeout. '
              '0 indicates no timeout. '
              'Default: 15')
@click.option('--idle-timeout', type=int, required=False,
              help='The idle timeout in minutes for the new user. '
              'This is the amount of time the user\'s UI session can be idle '
              'before it is disconnected. '
              '0 indicates no timeout. '
              'Default: 0')
@click.option('--min-pw-change-time', type=int, required=False,
              help='The minimum password change time in minutes for the new '
              'user. This is the minimum amount of time that must pass between '
              'changes to the user\'s password. '
              '0 indicates no minimum time. '
              'Only valid with authentication type "local". '
              'Default: 0')
@click.option('--max-failed-logins', type=int, required=False,
              help='The maximum number of consecutive failed login attempts '
              'for the new user. When exceeding this maximum, the user '
              'will be temporarily disabled for the amount of time specified '
              'in the "disable-delay" property. '
              '0 indicates that the user is never disabled due to failed '
              'login attempts. '
              'Default: 3')
@click.option('--disable-delay', type=int, required=False,
              help='The disable-delay time in minutes for the new user. '
              'This is the amount of time the user will be temporarily '
              'disabled after exceeding the maximum number of failed login '
              'attempts. '
              '0 indicates that the user is not disabled for any period of '
              'time after reaching the maximum number of invalid login '
              'attempts. '
              'Default: 1')
@click.option('--inactivity-timeout', type=int, required=False,
              help='The inactivity timeout in days for the new user. '
              'This is the maximum number of consecutive days of with no login '
              'before the user is disabled. '
              '0 indicates no inactivity timeout. '
              'Default: 0')
@click.option('--disruptive-pw-required', type=bool, required=False,
              help='The indicator whether the new user\'s password is required '
              'to perform disruptive actions through the UI. '
              'Default: True')
@click.option('--disruptive-text-required', type=bool, required=False,
              help='The indicator whether text input is required to '
              'perform disruptive actions through the UI. '
              'Default: False')
@click.option('--allow-remote-access', type=bool, required=False,
              help='The indicator whether the new user is allowed to access '
              'the HMC through its remote web server interface. '
              'Default: False')
@click.option('--allow-management-interfaces', type=bool, required=False,
              help='The indicator whether the new user is allowed access to '
              'management interfaces. This includes access to the '
              'Web Services APIs. '
              'Default: False')
@click.option('--max-web-services-api-sessions', type=int, required=False,
              help='The maximum number of simultaneous Web Services API '
              'sessions the new user is permitted to have. '
              'Default: 100')
@click.option('--web-services-api-session-idle-timeout', type=int,
              required=False,
              help='The idle timeout in minutes for Web Services API sessions '
              'created by the new user. This is the amount of time a Web '
              'Services API session can be idle before it is terminated. '
              'Default: 360')
@click.option('--mfa-type', type=click.Choice(['hmc-totp', 'mfa-server', '']),
              required=False,
              help='The MFA type of the new user, or the empty string for '
              'no MFA. '
              'Default: No MFA')
@click.option('--primary-mfa-server-definition', type=str, required=False,
              help='The name of the MFA Server Definition for the primary MFA '
              'server used to authenticate the new user, or the empty string '
              'to set no such server. '
              'Only valid for MFA type "mfa-server". '
              'Default: No such server')
@click.option('--backup-mfa-server-definition', type=str, required=False,
              help='The name of the MFA Server Definition for the backup MFA '
              'server used to authenticate the new user, or the empty string '
              'to set no such server. '
              'Only valid for MFA type "mfa-server". '
              'Default: No such server')
@click.option('--mfa-policy', type=str, required=False,
              help='The name of the MFA policy for the new user, or the empty '
              'string to set no MFA policy. This is for example a RACF policy. '
              'The MFA policy applies to the user when an MFA server '
              'authenticates the user. It must identify a policy whose only '
              'MFA factor is the RSA SecurID factor. '
              'Only valid for MFA type "mfa-server". '
              'Default: No MFA policy')
@click.option('--mfa-userid', type=str, required=False,
              help='The name of the MFA user ID for the new user, or the empty '
              'string to set no MFA user ID. This is a user ID, such as a RACF '
              'user ID, that identifies this user to the MFA server that '
              'authenticates the user. '
              'Only valid for MFA type "mfa-server" and user type not '
              '"template". '
              'Default: No MFA user ID')
@click.option('--mfa-userid-override', type=str, required=False,
              help='The name of the LDAP attribute that contains the MFA '
              'user ID that overrides the mfa-userid during authentication, or '
              'the empty string to set no userid override via LDAP attribute. '
              'Only valid for MFA type "mfa-server" and user type "template". '
              'Default: No userid override')
@click.pass_obj
def user_create(cmd_ctx, **options):
    """
    Create an HMC user.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_user_create(cmd_ctx, options))


@user_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('USER', type=str, metavar='USER')
@click.option('--description', type=str, required=False,
              help='The new description of the user.')
@click.option('--email-address', type=str, required=False,
              help='The new email address of the user or the empty string to '
              'set no email address.')
@click.option('--disabled', type=bool, required=False,
              help='The new disabled state of the user.')
@click.option('--password-rule', type=str, required=False,
              help='The name of the new password rule of the user. '
              'Only valid with authentication type "local".')
@click.option('--password', type=str, required=False,
              help='The new logon password for the user.')
@click.option('--force-password-change', type=bool, required=False,
              help='The new force-password-change state of the user. '
              'Only valid with authentication type "local".')
@click.option('--default-group', type=str, required=False,
              help='The name of the new default group of the user, or the '
              'empty string to set no default group. '
              'Managed objects created by the user automatically become '
              'members of its default group, if set.')
@click.option('--authentication-type', type=click.Choice(['local', 'ldap']),
              required=False,
              help='The new authentication type of the user.')
@click.option('--ldap-server-definition', type=str, required=False,
              help='The name of the new LDAP server definition of the user, or '
              'the empty string to set no LDAP server definition. '
              'Only valid with authentication type "ldap".')
@click.option('--userid-on-ldap-server', type=str, required=False,
              help='The new userid on the LDAP server. '
              'Only valid with authentication type "ldap".')
@click.option('--session-timeout', type=int, required=False,
              help='The new session timeout in minutes for the user. '
              'This is the amount of time for which a user\'s UI session can '
              'run before being prompted for identity verification. '
              '0 indicates no timeout.')
@click.option('--verify-timeout', type=int, required=False,
              help='The new verification timeout in minutes for the user. '
              'This is the amount of time allowed for the user to re-enter '
              'their password when being prompted due to a session timeout. '
              '0 indicates no timeout.')
@click.option('--idle-timeout', type=int, required=False,
              help='The new idle timeout in minutes for the user. '
              'This is the amount of time the user\'s UI session can be idle '
              'before it is disconnected. '
              '0 indicates no timeout.')
@click.option('--min-pw-change-time', type=int, required=False,
              help='The new minimum password change time in minutes for the '
              'user. This is the minimum amount of time that must pass between '
              'changes to the user\'s password. '
              '0 indicates no minimum time. '
              'Only valid with authentication type "local".')
@click.option('--max-failed-logins', type=int, required=False,
              help='The new maximum number of consecutive failed login '
              'attempts for the user. When exceeding this maximum, the user '
              'will be temporarily disabled for the amount of time specified '
              'in the "disable-delay" property. '
              '0 indicates that the user is never disabled due to failed '
              'login attempts.')
@click.option('--disable-delay', type=int, required=False,
              help='The new disable-delay time in minutes for the user. '
              'This is the amount of time the user will be temporarily '
              'disabled after exceeding the maximum number of failed login '
              'attempts. '
              '0 indicates that the user is not disabled for any period of '
              'time after reaching the maximum number of invalid login '
              'attempts.')
@click.option('--inactivity-timeout', type=int, required=False,
              help='The new inactivity timeout in days for the user. '
              'This is the maximum number of consecutive days of with no login '
              'before the user is disabled. '
              '0 indicates no inactivity timeout.')
@click.option('--disruptive-pw-required', type=bool, required=False,
              help='The new indicator whether the user\'s password is required '
              'to perform disruptive actions through the UI.')
@click.option('--disruptive-text-required', type=bool, required=False,
              help='The new indicator whether text input is required to '
              'perform disruptive actions through the UI.')
@click.option('--allow-remote-access', type=bool, required=False,
              help='The new indicator whether the user is allowed to access '
              'the HMC through its remote web server interface.')
@click.option('--allow-management-interfaces', type=bool, required=False,
              help='The new indicator whether the user is allowed access to '
              'management interfaces. This includes access to the '
              'Web Services APIs.')
@click.option('--max-web-services-api-sessions', type=int, required=False,
              help='The new maximum number of simultaneous Web Services API '
              'sessions the user is permitted to have.')
@click.option('--web-services-api-session-idle-timeout', type=int,
              required=False,
              help='The new idle timeout in minutes for Web Services API '
              'sessions created by the user. This is the amount of time a Web '
              'Services API session can be idle before it is terminated.')
@click.option('--mfa-type', type=click.Choice(['hmc-totp', 'mfa-server', '']),
              required=False,
              help='The new MFA type of the user, or the empty string for '
              'no MFA.')
@click.option('--force-shared-secret-key-change', type=bool, required=False,
              help='The new indicator whether the user is required to '
              'establish a new shared secret key during the next logon. The '
              'shared secret key is used to calculate the user\'s current TOTP '
              'multi-factor authentication code.')
@click.option('--primary-mfa-server-definition', type=str, required=False,
              help='The name of the new MFA Server Definition for the primary '
              'MFA server used to authenticate the user, or the empty string '
              'to set no such server. '
              'Only valid for MFA type "mfa-server".')
@click.option('--backup-mfa-server-definition', type=str, required=False,
              help='The name of the new MFA Server Definition for the backup '
              'MFA server used to authenticate the user, or the empty string '
              'to set no such server. '
              'Only valid for MFA type "mfa-server".')
@click.option('--mfa-policy', type=str, required=False,
              help='The name of the new MFA policy for the user, or the empty '
              'string to set no MFA policy. This is for example a RACF policy. '
              'The MFA policy applies to the user when an MFA server '
              'authenticates the user. It must identify a policy whose only '
              'MFA factor is the RSA SecurID factor. '
              'Only valid for MFA type "mfa-server".')
@click.option('--mfa-userid', type=str, required=False,
              help='The name of the new MFA user ID for the user, or the empty '
              'string to set no MFA user ID. This is a user ID, such as a RACF '
              'user ID, that identifies this user to the MFA server that '
              'authenticates the user. '
              'Only valid for MFA type "mfa-server" and user type not '
              '"template".')
@click.option('--mfa-userid-override', type=str, required=False,
              help='The name of the new LDAP attribute that contains the MFA '
              'user ID that overrides the mfa-userid during authentication, or '
              'the empty string to set no userid override via LDAP attribute. '
              'Only valid for MFA type "mfa-server" and user type "template".')
@click.pass_obj
def user_update(cmd_ctx, user, **options):
    """
    Update the properties of an HMC user.

    Note that HMC users cannot be renamed.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_user_update(cmd_ctx, user, options))


@user_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('USER', type=str, metavar='USER')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the user.',
              prompt='Are you sure you want to delete this user ?')
@click.pass_obj
def user_delete(cmd_ctx, user):
    """
    Delete an HMC user.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_user_delete(cmd_ctx, user))


@user_group.command('add-role', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('USER', type=str, metavar='USER')
@click.argument('USER_ROLE', type=str, metavar='USER_ROLE')
@click.pass_obj
def user_add_role(cmd_ctx, user, user_role):
    """
    Add a user role to a user.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_user_add_role(cmd_ctx, user, user_role))


@user_group.command('remove-role', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('USER', type=str, metavar='USER')
@click.argument('USER_ROLE', type=str, metavar='USER_ROLE')
@click.pass_obj
def user_remove_role(cmd_ctx, user, user_role):
    """
    Remove a user role from a user.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_user_remove_role(cmd_ctx, user, user_role))


def cmd_user_list(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    show_list = [
        'name',
    ]
    if not options['names_only']:
        show_list.extend([
            'email-address',
            'description',
            'type',
        ])
    if options['uri']:
        show_list.extend([
            'object-uri',
        ])
    if options['permissions']:
        show_list.extend([
            'allow-management-interfaces',
            'allow-remote-access',
            'roles',  # addition
        ])
    if options['status']:
        show_list.extend([
            'disabled',
            'is-locked',
            'max-failed-logins',
            'password-expires',
            'password-rule',  # addition
            'force-password-change',
            'multi-factor-authentication-required',
            'force-shared-secret-key-change',
        ])

    additions = {}
    additions['roles'] = {}
    additions['password-rule'] = {}

    try:
        users = console.users.list(full_properties=False)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    obj_cache = None

    if options['permissions']:
        if obj_cache is None:
            obj_cache = ObjectByUriCache(cmd_ctx, client)
        for user in users:
            role_names = [obj_cache.user_role_by_uri(role_uri).name
                          for role_uri in user.get_property('user-roles')]
            additions['roles'][user.uri] = role_names

    if options['status']:
        if obj_cache is None:
            obj_cache = ObjectByUriCache(cmd_ctx, client)
        for user in users:
            rule_uri = user.get_property('password-rule-uri')
            if rule_uri:
                rule_name = obj_cache.password_rule_by_uri(rule_uri).name
                additions['password-rule'][user.uri] = rule_name
            else:
                additions['password-rule'][user.uri] = None

    try:
        print_resources(cmd_ctx, users, cmd_ctx.output_format, show_list,
                        additions, all=options['all'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_user_show(cmd_ctx, user_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    user = find_user(cmd_ctx, console, user_name)

    try:
        user.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(user.properties)

    obj_cache = ObjectByUriCache(cmd_ctx, client)

    # Add artificial property 'user-role-names'
    role_names = [obj_cache.user_role_by_uri(role_uri).name
                  for role_uri in user.properties['user-roles']]
    properties['user-role-names'] = role_names

    # Add artificial property 'password-rule-name'
    rule_uri = user.properties['password-rule-uri']
    if rule_uri:
        rule_name = obj_cache.password_rule_by_uri(rule_uri).name
        properties['password-rule-name'] = rule_name
    else:
        properties['password-rule-name'] = None

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def cmd_user_password(cmd_ctx, user_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    user = find_user(cmd_ctx, console, user_name)

    cmd_ctx.spinner.stop()
    password = click.prompt(
        "Enter new password for user '{u}' (at HMC {h})".
        format(u=user_name, h=cmd_ctx.session.host),
        hide_input=True, confirmation_prompt=True, type=str, err=True)
    cmd_ctx.spinner.start()

    properties = {'password': password}
    try:
        user.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Password of user '{u}' has been updated.".format(u=user_name))


def cmd_user_create(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    org_options = original_options(options)

    name_map = {
        'like': None,
        'password-rule': None,
        'ldap-server-definition': None,
        'primary-mfa-server-definition': None,
        'backup-mfa-server-definition': None,
        'mfa-type': None,
    }

    # Set up user properties from like user, if specified

    like_props = {}
    if org_options['like']:
        try:
            like_user = console.users.find_by_name(org_options['like'])
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)

        def _update(props, obj, name):
            try:
                value = obj.get_property(name)
            except KeyError:
                return
            props[name] = value

        # The following properties are taken from the like user. These are
        # the properties that do not contain anything about the identity of the
        # user. The following identifying properties are not used:
        # - name
        # - password
        # - description
        # - email-address
        # - mfa-userid
        # - mfa-userid-override
        like_props = {}
        _update(like_props, like_user, 'type')
        _update(like_props, like_user, 'disabled')
        _update(like_props, like_user, 'authentication-type')
        _update(like_props, like_user, 'password-rule-uri')
        _update(like_props, like_user, 'force-password-change')
        _update(like_props, like_user, 'ldap-server-definition-uri')
        _update(like_props, like_user, 'userid-on-ldap-server')
        _update(like_props, like_user, 'session-timeout')
        _update(like_props, like_user, 'verify-timeout')
        _update(like_props, like_user, 'idle-timeout')
        _update(like_props, like_user, 'min-pw-change-time')
        _update(like_props, like_user, 'max-failed-logins')
        _update(like_props, like_user, 'disable-delay')
        _update(like_props, like_user, 'inactivity-timeout')
        _update(like_props, like_user, 'disruptive-pw-required')
        _update(like_props, like_user, 'disruptive-text-required')
        _update(like_props, like_user, 'allow-remote-access')
        _update(like_props, like_user, 'allow-management-interfaces')
        _update(like_props, like_user, 'max-web-services-api-sessions')
        _update(like_props, like_user, 'web-services-api-session-idle-timeout')
        _update(like_props, like_user, 'multi-factor-authentication-required')
        # The following are only present if mfa required:
        _update(like_props, like_user, 'mfa-types')
        _update(like_props, like_user, 'primary-mfa-server-definition-uri')
        _update(like_props, like_user, 'backup-mfa-server-definition-uri')
        _update(like_props, like_user, 'mfa-policy')

    # Determine user properties from options

    option_props = options_to_properties(org_options, name_map)

    if org_options['password-rule'] in (None, ''):
        pass  # omit -> HMC sets to default
    else:
        try:
            rule = console.password_rules.find_by_name(
                org_options['password-rule'])
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)
        option_props['password-rule-uri'] = rule.uri

    if org_options['ldap-server-definition'] in (None, ''):
        pass  # omit -> HMC sets to default
    else:
        try:
            ldap_def = console.ldap_server_definitions.find_by_name(
                org_options['ldap-server-definition'])
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)
        option_props['ldap-server-definition-uri'] = ldap_def.uri

    if org_options['primary-mfa-server-definition'] in (None, ''):
        pass  # omit -> HMC sets to default
    else:
        raise NotImplementedError
        # TODO: Implement zhmcclient.MfaServerDefinition
        # try:
        #     mfa_def = console.mfa_server_definitions.find_by_name(
        #         org_options['primary-mfa-server-definition'])
        # except zhmcclient.Error as exc:
        #     raise click_exception(exc, cmd_ctx.error_format)
        # option_props['primary-mfa-server-definition-uri'] = mfa_def.uri

    if org_options['backup-mfa-server-definition'] in (None, ''):
        pass  # omit -> HMC sets to default
    else:
        raise NotImplementedError
        # TODO: Implement zhmcclient.MfaServerDefinition
        # try:
        #     mfa_def = console.mfa_server_definitions.find_by_name(
        #         org_options['backup-mfa-server-definition'])
        # except zhmcclient.Error as exc:
        #     raise click_exception(exc, cmd_ctx.error_format)
        # option_props['backup-mfa-server-definition-uri'] = mfa_def.uri

    if org_options['mfa-type'] in (None, ''):
        # 'mfa-types' remains unset in this case
        option_props['multi-factor-authentication-required'] = False
    elif org_options['mfa-type'] == 'hmc-totp':
        option_props['mfa-types'] = ['hmc-totp']
        option_props['multi-factor-authentication-required'] = True
    else:
        assert org_options['mfa-type'] == 'mfa-server'
        option_props['mfa-types'] = ['mfa-server']

    if org_options['email-address'] == '':
        option_props['email-address'] = None

    if org_options['mfa-type'] in (None, ''):
        option_props['mfa-types'] = None
        option_props['multi-factor-authentication-required'] = False
    elif org_options['mfa-type'] == 'hmc-totp':
        option_props['mfa-types'] = ['hmc-totp']
        option_props['multi-factor-authentication-required'] = True
    else:
        assert org_options['mfa-type'] == 'mfa-server'
        option_props['mfa-types'] = ['mfa-server']

    if org_options['email-address'] == '':
        option_props['email-address'] = None

    if org_options['mfa-policy'] == '':
        option_props['mfa-policy'] = None

    if org_options['mfa-userid'] == '':
        option_props['mfa-userid'] = None

    if org_options['mfa-userid-override'] == '':
        option_props['mfa-userid-override'] = None

    properties = like_props
    properties.update(option_props)

    try:
        new_user = console.users.create(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("New user '{u}' has been created.".
               format(u=new_user.properties['name']))


def cmd_user_update(cmd_ctx, user_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    user = find_user(cmd_ctx, console, user_name)

    org_options = original_options(options)

    name_map = {
        'password-rule': None,
        'default-group': None,
        'ldap-server-definition': None,
        'primary-mfa-server-definition': None,
        'backup-mfa-server-definition': None,
        'mfa-type': None,
    }

    properties = options_to_properties(org_options, name_map)

    if org_options['password-rule'] is None:
        pass  # omit -> no change
    elif org_options['password-rule'] == '':
        properties['password-rule-uri'] = None
    else:
        try:
            rule = console.password_rules.find_by_name(
                org_options['password-rule'])
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)
        properties['password-rule-uri'] = rule.uri

    if org_options['default-group'] is None:
        pass  # omit -> no change
    elif org_options['default-group'] == '':
        properties['default-group-uri'] = None
    else:
        raise NotImplementedError
        # TODO: Implement zhmcclient.Group
        # try:
        #     group = client.groups.find_by_name(
        #         org_options['default-group'])
        # except zhmcclient.Error as exc:
        #     raise click_exception(exc, cmd_ctx.error_format)
        # properties['default-group-uri'] = group.uri

    if org_options['ldap-server-definition'] is None:
        pass  # omit -> no change
    elif org_options['ldap-server-definition'] == '':
        properties['ldap-server-definition-uri'] = None
    else:
        try:
            ldap_def = console.ldap_server_definitions.find_by_name(
                org_options['ldap-server-definition'])
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)
        properties['ldap-server-definition-uri'] = ldap_def.uri

    if org_options['primary-mfa-server-definition'] is None:
        pass  # omit -> no change
    elif org_options['primary-mfa-server-definition'] == '':
        properties['primary-mfa-server-definition-uri'] = None
    else:
        raise NotImplementedError
        # TODO: Implement zhmcclient.MfaServerDefinition
        # try:
        #     mfa_def = console.mfa_server_definitions.find_by_name(
        #         org_options['primary-mfa-server-definition'])
        # except zhmcclient.Error as exc:
        #     raise click_exception(exc, cmd_ctx.error_format)
        # properties['primary-mfa-server-definition-uri'] = mfa_def.uri

    if org_options['backup-mfa-server-definition'] is None:
        pass  # omit -> no change
    elif org_options['backup-mfa-server-definition'] == '':
        properties['backup-mfa-server-definition-uri'] = None
    else:
        raise NotImplementedError
        # TODO: Implement zhmcclient.MfaServerDefinition
        # try:
        #     mfa_def = console.mfa_server_definitions.find_by_name(
        #         org_options['backup-mfa-server-definition'])
        # except zhmcclient.Error as exc:
        #     raise click_exception(exc, cmd_ctx.error_format)
        # properties['backup-mfa-server-definition-uri'] = mfa_def.uri

    if org_options['mfa-type'] is None:
        pass  # omit -> no change
    elif org_options['mfa-type'] == '':
        # 'mfa-types' remains unset in this case
        properties['multi-factor-authentication-required'] = False
    elif org_options['mfa-type'] == 'hmc-totp':
        properties['mfa-types'] = ['hmc-totp']
        properties['multi-factor-authentication-required'] = True
    else:
        assert org_options['mfa-type'] == 'mfa-server'
        properties['mfa-types'] = ['mfa-server']

    if org_options['email-address'] == '':
        properties['email-address'] = None

    if org_options['mfa-policy'] == '':
        properties['mfa-policy'] = None

    if org_options['mfa-userid'] == '':
        properties['mfa-userid'] = None

    if org_options['mfa-userid-override'] == '':
        properties['mfa-userid-override'] = None

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating user '{u}'.".
                   format(u=user_name))
        return

    try:
        user.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("User '{u}' has been updated.".format(u=user_name))


def cmd_user_delete(cmd_ctx, user_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    user = find_user(cmd_ctx, console, user_name)

    try:
        user.delete()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("User '{u}' has been deleted.".format(u=user_name))


def cmd_user_add_role(cmd_ctx, user_name, user_role_name):
    # pylint: disable=missing-function-docstring

    # pylint: disable=import-outside-toplevel,cyclic-import
    from ._cmd_user_role import find_user_role

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    user = find_user(cmd_ctx, console, user_name)
    user_role = find_user_role(cmd_ctx, console, user_role_name)

    try:
        user.add_user_role(user_role)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("User role '{r}' has been added to user '{u}'.".
               format(r=user_role_name, u=user_name))


def cmd_user_remove_role(cmd_ctx, user_name, user_role_name):
    # pylint: disable=missing-function-docstring

    # pylint: disable=import-outside-toplevel,cyclic-import
    from ._cmd_user_role import find_user_role

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    user = find_user(cmd_ctx, console, user_name)
    user_role = find_user_role(cmd_ctx, console, user_role_name)

    try:
        user.remove_user_role(user_role)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("User role '{r}' has been removed from user '{u}'.".
               format(r=user_role_name, u=user_name))
