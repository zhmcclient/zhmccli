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
Commands for unmanaged CPCs.
"""

from __future__ import absolute_import

import click

import zhmcclient
from .zhmccli import cli
from ._helper import print_resources, click_exception, COMMAND_OPTIONS_METAVAR


def find_unmanaged_cpc(cmd_ctx, console, cpc_name):
    """
    Find an unmanaged CPC by name and return its resource object.
    """
    try:
        ucpc = console.unmanaged_cpcs.find(name=cpc_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return ucpc


@cli.group('unmanaged_cpc', options_metavar=COMMAND_OPTIONS_METAVAR)
def ucpc_group():
    """
    Command group for unmanaged CPCs.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@ucpc_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--uri', is_flag=True, required=False,
              help='Add the resource URI to the properties shown')
@click.pass_obj
def ucpc_list(cmd_ctx, **options):
    """
    List the unmanaged CPCs of the HMC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_ucpc_list(cmd_ctx, options))


def cmd_ucpc_list(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    try:
        ucpcs = console.unmanaged_cpcs.list()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    show_list = [
        'name',
    ]
    if options['uri']:
        show_list.extend([
            'object-uri',
        ])

    try:
        print_resources(cmd_ctx, ucpcs, cmd_ctx.output_format, show_list,
                        all=False)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
