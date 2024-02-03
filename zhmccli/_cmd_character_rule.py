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
Commands for management of character rules within HMC character rule.
"""

from __future__ import absolute_import
from __future__ import print_function

import click

import zhmcclient
from ._helper import print_properties, print_dicts, options_to_properties, \
    original_options, COMMAND_OPTIONS_METAVAR, click_exception
from ._cmd_password_rule import password_rule_group, find_password_rule


@password_rule_group.group('characterrule',
                           options_metavar=COMMAND_OPTIONS_METAVAR)
def character_rule_group():
    """
    Command group for managing character rules within HMC password rules.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@character_rule_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('PASSWORD_RULE', type=str, metavar='PASSWORD_RULE')
@click.pass_obj
def character_rule_list(cmd_ctx, password_rule):
    """
    List the character rules within an HMC password rule.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_character_rule_list(cmd_ctx, password_rule))


@character_rule_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('PASSWORD_RULE', type=str, metavar='PASSWORD_RULE')
@click.argument('INDEX', type=str, metavar='INDEX')
@click.pass_obj
def character_rule_show(cmd_ctx, password_rule, index):
    """
    Show the details of a character rule at an index within an HMC password
    rule.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_character_rule_show(
        cmd_ctx, password_rule, index))


@character_rule_group.command('add', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('PASSWORD_RULE', type=str, metavar='PASSWORD_RULE')
@click.option('--before', type=int, required=False,
              help='Add the character rule before the rule at this 0-based '
              'index.')
@click.option('--after', type=int, required=False,
              help='Add the character rule after the rule at this 0-based '
              'index.')
@click.option('--last', is_flag=True, required=False,
              help='Add the character rule after the last rule (default).')
@click.option('--min', type=int, required=True,
              help='The minimum number of characters in this part of the '
              'password.')
@click.option('--max', type=int, required=True,
              help='The maximum number of characters in this part of the '
              'password.')
@click.option('--alphabetic',
              type=click.Choice(['allowed', 'not-allowed', 'required']),
              required=True,
              help='The control for the inclusion of alphabetic characters in '
              'this part of the password.')
@click.option('--numeric',
              type=click.Choice(['allowed', 'not-allowed', 'required']),
              required=True,
              help='The control for the inclusion of numeric characters in '
              'this part of the password.')
@click.option('--special',
              type=click.Choice(['allowed', 'not-allowed', 'required']),
              required=True,
              help='The control for the inclusion of special characters '
              '(!?@#$%&^~_+-*/=\\|.,:`";\'(){}[]<>) '
              'in this part of the password.')
@click.option('--custom', nargs=2, metavar='CHARS CONTROL', multiple=True,
              required=False,
              help='The control for the inclusion of special characters '
              '(!?@#$%&^~_+-*/=\\|.,:`";\'(){}[]<>) '
              'in this part of the password.')
@click.pass_obj
def character_rule_add(cmd_ctx, password_rule, **options):
    """
    Add a character rule before/after an index within an HMC password rule.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_character_rule_add(
        cmd_ctx, password_rule, options))


@character_rule_group.command('replace',
                              options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('PASSWORD_RULE', type=str, metavar='PASSWORD_RULE')
@click.argument('INDEX', type=str, metavar='INDEX')
@click.option('--min', type=int, required=True,
              help='The minimum number of characters in this part of the '
              'password.')
@click.option('--max', type=int, required=True,
              help='The maximum number of characters in this part of the '
              'password.')
@click.option('--alphabetic',
              type=click.Choice(['allowed', 'not-allowed', 'required']),
              required=True,
              help='The control for the inclusion of alphabetic characters in '
              'this part of the password.')
@click.option('--numeric',
              type=click.Choice(['allowed', 'not-allowed', 'required']),
              required=True,
              help='The control for the inclusion of numeric characters in '
              'this part of the password.')
@click.option('--special',
              type=click.Choice(['allowed', 'not-allowed', 'required']),
              required=True,
              help='The control for the inclusion of special characters '
              '(!?@#$%&^~_+-*/=\\|.,:`";\'(){}[]<>) '
              'in this part of the password.')
@click.option('--custom', nargs=2, metavar='CHARS CONTROL', multiple=True,
              required=False,
              help='The control for the inclusion of special characters '
              '(!?@#$%&^~_+-*/=\\|.,:`";\'(){}[]<>) '
              'in this part of the password.')
@click.pass_obj
def character_rule_replace(cmd_ctx, password_rule, index, **options):
    """
    Replace a character rule at an index within an HMC password rule.

    All properties of the character rule will be updated. If the option for
    a property is not specified, it will be updated to its default value.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_character_rule_replace(
        cmd_ctx, password_rule, index, options))


@character_rule_group.command('remove', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('PASSWORD_RULE', type=str, metavar='PASSWORD_RULE')
@click.argument('INDEX', type=str, metavar='INDEX')
@click.pass_obj
def character_rule_remove(cmd_ctx, password_rule, index):
    """
    Remove a character rule at an index within an HMC password rule.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_character_rule_remove(
        cmd_ctx, password_rule, index))


def cmd_character_rule_list(cmd_ctx, password_rule_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    show_list = [
        'index',
        'min-characters',
        'max-characters',
        'alphabetic',
        'numeric',
        'special',
        'custom-character-sets',
    ]

    additions = {}
    additions['index'] = {}

    password_rule = find_password_rule(cmd_ctx, console, password_rule_name)
    character_rules = password_rule.get_property('character-rules')

    # Add artificial property 'index'
    for i, _ in enumerate(character_rules):
        additions['index'][i] = i

    try:
        print_dicts(cmd_ctx, character_rules, cmd_ctx.output_format,
                    show_list, additions, all=False)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_character_rule_show(cmd_ctx, password_rule_name, index):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    password_rule = find_password_rule(cmd_ctx, console, password_rule_name)
    character_rules = password_rule.get_property('character-rules')

    try:
        index = int(index)
        character_rule = character_rules[index]
    except (ValueError, IndexError):
        raise click.ClickException(
            "Invalid index {i} for character rules of password rule '{r}'".
            format(i=index, r=password_rule_name))

    properties = dict(character_rule)

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def cmd_character_rule_add(cmd_ctx, password_rule_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    password_rule = find_password_rule(cmd_ctx, console, password_rule_name)
    character_rules = password_rule.get_property('character-rules')
    size = len(character_rules)

    before = options.pop('before')
    after = options.pop('after')
    last = options.pop('last')
    if (bool(before is not None) + bool(after is not None) + last) > 1:
        raise click.ClickException(
            "Only one of --before, --after and --last can be specified.")

    name_map = {
        'min': 'min-characters',
        'max': 'max-characters',
        'custom': None,
    }

    org_options = original_options(options)
    cr_properties = options_to_properties(org_options, name_map)

    # Add custom-character-sets array
    custom_char_sets = []
    for chars, control in options['custom']:
        custom_char_set = {
            'character-set': chars,
            'inclusion': control,
        }
        custom_char_sets.append(custom_char_set)
    cr_properties['custom-character-sets'] = custom_char_sets

    new_character_rules = list(character_rules)
    if before is not None:
        if before < 0 or before >= max(size, 1):
            raise click.ClickException(
                "Invalid --before index {i} for character rules of password "
                "rule '{r}'".
                format(i=before, r=password_rule_name))
        new_character_rules.insert(before, cr_properties)
    elif after is not None:
        if after < 0 or after >= max(size, 1):
            raise click.ClickException(
                "Invalid --after index {i} for character rules of password "
                "rule '{r}'".
                format(i=after, r=password_rule_name))
        new_character_rules.insert(after + 1, cr_properties)
    else:  # last = default
        new_character_rules.insert(size, cr_properties)

    properties = {'character-rules': new_character_rules}

    try:
        password_rule.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    where = 'after' if after is not None else 'before'
    index = after if after is not None else before
    click.echo("Password rule '{r}' has been updated to add character rule "
               "{w} index {i}.".
               format(r=password_rule_name, w=where, i=index))


def cmd_character_rule_replace(cmd_ctx, password_rule_name, index, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    password_rule = find_password_rule(cmd_ctx, console, password_rule_name)
    character_rules = password_rule.get_property('character-rules')

    try:
        index = int(index)
        _ = character_rules[index]
    except (ValueError, IndexError):
        raise click.ClickException(
            "Invalid index {i} for character rules of password rule '{r}'".
            format(i=index, r=password_rule_name))

    name_map = {
        'min': 'min-characters',
        'max': 'max-characters',
        'custom': None,
    }

    org_options = original_options(options)
    cr_properties = options_to_properties(org_options, name_map)

    # Add custom-character-sets array
    custom_char_sets = []
    for chars, control in options['custom']:
        custom_char_set = {
            'character-set': chars,
            'inclusion': control,
        }
        custom_char_sets.append(custom_char_set)
    cr_properties['custom-character-sets'] = custom_char_sets

    new_character_rules = list(character_rules)
    new_character_rules[index] = cr_properties

    properties = {'character-rules': new_character_rules}

    try:
        password_rule.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Password rule '{r}' has been updated to replace character rule "
               "at index {i}.".
               format(r=password_rule_name, i=index))


def cmd_character_rule_remove(cmd_ctx, password_rule_name, index):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    password_rule = find_password_rule(cmd_ctx, console, password_rule_name)
    character_rules = password_rule.get_property('character-rules')

    try:
        index = int(index)
        _ = character_rules[index]
    except (ValueError, IndexError):
        raise click.ClickException(
            "Invalid index {i} for character rules of password rule '{r}'".
            format(i=index, r=password_rule_name))

    new_character_rules = list(character_rules)
    del new_character_rules[index]

    properties = {'character-rules': new_character_rules}

    try:
        password_rule.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Password rule '{r}' has been updated to remove character rule "
               "at index {i}.".
               format(r=password_rule_name, i=index))
