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
Commands for HMC password rule management.
"""

from __future__ import absolute_import
from __future__ import print_function

import click

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS


def find_password_rule(cmd_ctx, console, password_rule_name):
    """
    Find a password rule by name and return its resource object.
    """
    try:
        password_rule = console.password_rules.find(name=password_rule_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return password_rule


@cli.group('passwordrule', options_metavar=COMMAND_OPTIONS_METAVAR)
def password_rule_group():
    """
    Command group for managing HMC password rules.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@password_rule_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@add_options(LIST_OPTIONS)
@click.pass_obj
def password_rule_list(cmd_ctx, **options):
    """
    List the HMC password rules.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_password_rule_list(cmd_ctx, options))


@password_rule_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('PASSWORD_RULE', type=str, metavar='PASSWORD_RULE')
@click.pass_obj
def password_rule_show(cmd_ctx, password_rule):
    """
    Show the details of an HMC password rule.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_password_rule_show(cmd_ctx, password_rule))


@password_rule_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--name', type=str, required=True,
              help='The name of the new password rule.')
@click.option('--description', type=str, required=False,
              help='The description of the new password rule.')
@click.option('--expiration', type=int, required=False,
              help='The total number of days a password is valid before '
              'it expires. '
              '0 indicates that the password never expires. '
              'Default: 0')
@click.option('--min-length', type=int, required=False,
              help='The minimum required length of the password. '
              'Default: 8')
@click.option('--max-length', type=int, required=False,
              help='The maximum allowed length of the password. '
              'Default: 256')
@click.option('--consecutive-characters', type=int, required=False,
              help='The maximum number of characters that are allowed to '
              'be repeated in a row. '
              '0 indicates that there is no such limit. '
              'Default: 0')
@click.option('--similarity-count', type=int, required=False,
              help='The maximum number of consecutive characters in the '
              'current password that can match consecutive characters in '
              'the previous password. '
              '0 indicates that there is no such limit. '
              'Default: 0')
@click.option('--history-count', type=int, required=False,
              help='The number of previous passwords to which a new '
              'password is compared for uniqueness. '
              '0 indicates that there is no such comparison. '
              'Default: 0')
@click.option('--case-sensitive', type=bool, required=False,
              help='The indicator whether the password is case sensitive. '
              'Default: False')
@click.pass_obj
def password_rule_create(cmd_ctx, **options):
    """
    Create a user-defined HMC password rule.

    Note that the characters rules of password rules can be managed via the
    'characterrule' command group.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_password_rule_create(cmd_ctx, options))


@password_rule_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('PASSWORD_RULE', type=str, metavar='PASSWORD_RULE')
@click.option('--description', type=str, required=False,
              help='The new description of the password rule.')
@click.option('--expiration', type=int, required=False,
              help='The new total number of days a password is valid before '
              'it expires. '
              '0 indicates that the password never expires.')
@click.option('--min-length', type=int, required=False,
              help='The new minimum required length of the password.')
@click.option('--max-length', type=int, required=False,
              help='The new maximum allowed length of the password.')
@click.option('--consecutive-characters', type=int, required=False,
              help='The new maximum number of characters that are allowed to '
              'be repeated in a row. '
              '0 indicates that there is no such limit.')
@click.option('--similarity-count', type=int, required=False,
              help='The new maximum number of consecutive characters in the '
              'current password that can match consecutive characters in '
              'the previous password. '
              '0 indicates that there is no such limit.')
@click.option('--history-count', type=int, required=False,
              help='The new number of previous passwords to which a new '
              'password is compared for uniqueness. '
              '0 indicates that there is no such comparison.')
@click.option('--case-sensitive', type=int, required=False,
              help='The new indicator whether the password is case sensitive.')
@click.pass_obj
def password_rule_update(cmd_ctx, password_rule, **options):
    """
    Update the properties of an HMC password rule.

    Note that HMC password rules cannot be renamed.

    Note that the characters rules of password rules can be managed via the
    'characterrule' command group.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_password_rule_update(
        cmd_ctx, password_rule, options))


@password_rule_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('PASSWORD_RULE', type=str, metavar='PASSWORD_RULE')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the password rule.',
              prompt='Are you sure you want to delete this password rule ?')
@click.pass_obj
def password_rule_delete(cmd_ctx, password_rule):
    """
    Delete a user-defined HMC password rule.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_password_rule_delete(
        cmd_ctx, password_rule))


def cmd_password_rule_list(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

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
            'element-uri',
        ])

    additions = {}

    try:
        password_rules = console.password_rules.list(full_properties=False)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    try:
        print_resources(cmd_ctx, password_rules, cmd_ctx.output_format,
                        show_list, additions, all=options['all'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_password_rule_show(cmd_ctx, password_rule_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    password_rule = find_password_rule(cmd_ctx, console, password_rule_name)

    try:
        password_rule.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(password_rule.properties)

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def cmd_password_rule_create(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    org_options = original_options(options)
    properties = options_to_properties(org_options, None)

    try:
        new_password_rule = console.password_rules.create(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("New password rule '{r}' has been created.".
               format(r=new_password_rule.properties['name']))


def cmd_password_rule_update(cmd_ctx, password_rule_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    password_rule = find_password_rule(cmd_ctx, console, password_rule_name)

    org_options = original_options(options)
    properties = options_to_properties(org_options, None)

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating password rule '{r}'.".
                   format(r=password_rule_name))
        return

    try:
        password_rule.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Password rule '{r}' has been updated.".
               format(r=password_rule_name))


def cmd_password_rule_delete(cmd_ctx, password_rule_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    password_rule = find_password_rule(cmd_ctx, console, password_rule_name)

    try:
        password_rule.delete()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Password rule '{r}' has been deleted.".
               format(r=password_rule_name))
