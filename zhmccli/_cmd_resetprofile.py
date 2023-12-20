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
Commands for reset activation profiles for CPCs in classic mode.
"""

from __future__ import absolute_import

import click
from click_option_group import optgroup

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS, str2int, parse_yaml_flow_style
from ._cmd_cpc import find_cpc


def find_resetprofile(cmd_ctx, client, cpc_name, resetprofile_name):
    """
    Find a reset activation profile by name and return its resource object.
    """
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    # The CPC must be in classic mode. We don't check that because it would
    # cause a GET to the CPC resource that we otherwise don't need.
    try:
        resetprofile = cpc.reset_activation_profiles.find(
            name=resetprofile_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    return resetprofile


@cli.group('resetprofile', options_metavar=COMMAND_OPTIONS_METAVAR)
def resetprofile_group():
    """
    Command group for managing reset activation profiles (classic mode only).

    "Reset activation profiles" are used when activating a CPC in classic mode.
    Reset activation profiles have only a small set of properties and mainly
    reference an Input/Output Configuration Data Set (IOCDS) that describes the
    I/O configuration of the CPC. IOCDS data sets are not represented at the
    HMC WS-API and can therefore not be managed by this command.

    The commands in this group work only on CPCs in classic mode.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@resetprofile_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('cpc', type=str, metavar='[CPC]', required=False)
@add_options(LIST_OPTIONS)
@click.pass_obj
def resetprofile_list(cmd_ctx, cpc, **options):
    """
    List the reset activation profiles for a CPC, or if omitted for all
    managed CPCs.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_resetprofile_list(cmd_ctx, cpc, options))


@resetprofile_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('cpc', type=str, metavar='CPC')
@click.argument('resetprofile', type=str, metavar='RESETPROFILE')
@click.pass_obj
def resetprofile_show(cmd_ctx, cpc, resetprofile, **options):
    """
    Show details of a reset activation profile.

    The following properties are shown in addition to those returned by the HMC:

    \b
      - 'parent-name' - Name of the associated (parent) CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_resetprofile_show(cmd_ctx, cpc, resetprofile, options))


@resetprofile_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('cpc', type=str, metavar='CPC')
@click.argument('resetprofile', type=str, metavar='RESETPROFILE')
@optgroup.group('General options')
@optgroup.option('--description', type=str, required=False,
                 help='The new description for the reset activation profile.')
@optgroup.option('--iocds', type=str, required=False,
                 # Property: 'iocds-name'
                 help='The IOCDS name, as a hexadecimal number. An empty '
                 'string indicates that the currently active IOCDS will be '
                 'used for the next CPC activation.')
@optgroup.option('--processor-running-time', type=str, required=False,
                 # Properties: 'processor-running-time' and
                 # 'processor-running-time-type'
                 help='Amount of continuous time, in milliseconds, for which '
                 'shared processors are assigned to a particular LPAR (1-100).'
                 'The special value "system" indicates that the time is '
                 'determined dynamically by the system.')
@optgroup.option('--end-timeslice-on-wait', type=bool, required=False,
                 help='Indicates that for user-determind '
                 'processor-running-time, the LPARs lose their share of '
                 'running time when they enter a wait state. Can only be '
                 'updated for CPCs with SE version 2.13 or older.')
@click.pass_obj
def resetprofile_update(cmd_ctx, cpc, resetprofile, **options):
    """
    Update the properties of a reset activation profile.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_resetprofile_update(cmd_ctx, cpc, resetprofile, options))


@resetprofile_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('cpc', type=str, metavar='CPC')
@optgroup.group('General options')
@optgroup.option('--name', type=str, required=True,
                 # Property: 'profile-name'
                 help='The name for the new reset activation profile. '
                 'The names of reset, image, and load activation profiles are '
                 'all in the same namespace for each CPC and must be unique '
                 'within that namespace.')
@optgroup.option('--copy-name', type=str, required=False,
                 help='The name of an existing reset activation profile whose '
                 'properties act as defaults for options not specified in '
                 'this command. Default: The reset activation profile named '
                 '"DEFAULT".')
@optgroup.option('--description', type=str, required=False,
                 help='The description for the new reset activation profile.')
@optgroup.option('--iocds', type=str, required=False,
                 # Property: 'iocds-name'
                 help='The IOCDS name, as a hexadecimal number. An empty '
                 'string indicates that the currently active IOCDS will be '
                 'used for the next CPC activation.')
@optgroup.option('--iocds-allow-expansion', type=bool, required=False,
                 help='Controls whether dynamic IOCDS expansion is allowed. '
                 'Not supported with initial HMC 2.16 version.')
@optgroup.option('--load-delay', type=int, required=False,
                 help='The delay (in seconds) before performing a load for an '
                 'LPAR. (0-6000)')
@optgroup.option('--io-priority-queuing-enabled', type=bool, required=False,
                 help='Controls whether global I/O priority queuing is '
                 'enabled. '
                 'Not supported with initial HMC 2.16 version.')
@optgroup.option('--global-interface-reset-enabled', type=bool, required=False,
                 help='Controls whether global interface reset is enabled. '
                 'Not supported with initial HMC 2.16 version.')
@optgroup.option('--processor-running-time', type=str, required=False,
                 # Properties: 'processor-running-time' and
                 # 'processor-running-time-type'
                 help='Amount of continuous time, in milliseconds, for which '
                 'shared processors are assigned to a particular LPAR (1-100).'
                 'The special value "system" indicates that the time is '
                 'determined dynamically by the system.')
@optgroup.option('--display-fenced-book-page', type=bool, required=False,
                 help='Controls whether the fenced book page flag is displayed '
                 'in the HMC GUI.')
@optgroup.option('--how-fence-determined',
                 type=click.Choice(['system', 'user']), required=False,
                 help='Controls how fenced book values are determined: '
                 '"system" – Let the system determine the fenced book values. '
                 '"user" – Let the user determine the fenced book values. '
                 'Not supported with initial HMC 2.16 version.')
@optgroup.option('--lpar-activation-order', type=str, required=False,
                 # Property: 'partition-profile-names' (array of string)
                 help='Comma-separated list of LPAR names that defines the '
                 'order in which they will be activated when activating the '
                 'CPC.')
@optgroup.option('--fenced-book-list', type=str, required=False,
                 help='List of "fenced-book-data" objects (described in the '
                 'HMC WS-API book), in YAML Flow Collection style. '
                 'A minimum of 1 item and a maximum of 5 items are permitted '
                 'in the list. '
                 'Example: --fenced-book-list "[{pu-mcm-size: 1, '
                 'num-cp-fenced: 1, num-sap-fenced: 1, num-icf-fenced: 1, '
                 'num-ifl-fenced: 1, num-ziip-fenced: 1}]"')
@click.pass_obj
def resetprofile_create(cmd_ctx, cpc, **options):
    """
    Create a reset activation profile for a CPC (Only HMC 2.16 and later).

    The default values for any options not specified will be the corresponding
    property values of the default reset activation profile (that is the
    profile specified with the --copy-name option, or if that option is not
    specified, the profile named "DEFAULT").

    Some of the options of this command are documented to be specified in YAML
    Flow Collection style. That is a format for specifying complex values
    that are lists or dictionaries as a relatively simple string. The format
    is described for example in https://www.yaml.info/learn/flowstyle.html.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.

    \b
    Limitations:
      * The command does not support defining the 'fenced-book-list' property.
    """
    cmd_ctx.execute_cmd(lambda: cmd_resetprofile_create(cmd_ctx, cpc, options))


@resetprofile_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('cpc', type=str, metavar='CPC')
@click.argument('resetprofile', type=str, metavar='RESETPROFILE')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the reset activation '
              'profile.',
              prompt='Are you sure you want to delete this reset activation '
              'profile ?')
@click.pass_obj
def resetprofile_delete(cmd_ctx, cpc, resetprofile):
    """
    Delete a reset activation profile (Only HMC 2.16 and later).

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_resetprofile_delete(cmd_ctx, cpc, resetprofile))


def cmd_resetprofile_list(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)

    if cpc_name:
        cpc = find_cpc(cmd_ctx, client, cpc_name)
        cpcs = [cpc]
    else:
        try:
            cpcs = client.cpcs.list()
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)

    # Prepare the additions dict of dicts. It contains additional
    # (=non-resource) property values by property name and by resource URI.
    # Depending on options, some of them will not be populated.
    additions = {'cpc': {}}

    show_list = [
        'name',
        'cpc',
    ]
    if not options['names_only']:
        show_list.extend([
            'iocds-name',
            'description',
        ])
    if options['uri']:
        show_list.extend([
            'element-uri',
        ])

    resetprofiles = []
    for cpc in cpcs:
        try:
            resetprofiles.extend(cpc.reset_activation_profiles.list())
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)

        for resetprofile in resetprofiles:
            cpc = resetprofile.manager.parent
            additions['cpc'][resetprofile.uri] = cpc.name

    try:
        print_resources(
            cmd_ctx, resetprofiles, cmd_ctx.output_format, show_list,
            additions, all=options['all'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_resetprofile_show(cmd_ctx, cpc_name, resetprofile_name, options):
    # pylint: disable=missing-function-docstring,unused-argument

    client = zhmcclient.Client(cmd_ctx.session)
    resetprofile = find_resetprofile(
        cmd_ctx, client, cpc_name, resetprofile_name)

    try:
        resetprofile.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(resetprofile.properties)

    # Add artificial property 'parent-name'
    properties['parent-name'] = cpc_name

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def handle_special_resetprofile_options(cmd_ctx, org_options, properties):
    """
    Handle special create and update options (i.e. those that are set to
    None in the name_map). The options are taken from org_options and
    put into properties.
    """

    if org_options['processor-running-time'] == 'system':
        properties['processor-running-time-type'] = 'system-determined'
        # 'processor-running-time' will be set to 0 by the HMC
    elif org_options['processor-running-time'] is not None:
        properties['processor-running-time-type'] = 'user-determined'
        properties['processor-running-time'] = str2int(
            cmd_ctx, 'processor-running-time',
            org_options['processor-running-time'])


def cmd_resetprofile_update(cmd_ctx, cpc_name, resetprofile_name, options):
    # pylint: disable=missing-function-docstring
    # pylint: disable=unreachable

    client = zhmcclient.Client(cmd_ctx.session)
    resetprofile = find_resetprofile(
        cmd_ctx, client, cpc_name, resetprofile_name)

    name_map = {
        'iocds': 'iocds-name',
        'processor-running-time': None,
    }

    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    handle_special_resetprofile_options(cmd_ctx, org_options, properties)

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating reset activation "
                   "profile '{ip}' for CPC '{c}'.".
                   format(ip=resetprofile_name, c=cpc_name))
        return

    try:
        resetprofile.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Reset activation profile '{ip}' for CPC '{c}' has been "
               "updated.".format(ip=resetprofile_name, c=cpc_name))


def cmd_resetprofile_create(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring
    # pylint: disable=unreachable

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    name_map = {
        'name': 'profile-name',
        'iocds': 'iocds-name',
        'processor-running-time': None,
        'lpar-activation-order': None,
        'fenced-book-list': None,
    }

    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    handle_special_resetprofile_options(cmd_ctx, org_options, properties)

    if org_options['lpar-activation-order'] is not None:
        lpar_names = org_options['lpar-activation-order'].strip(',').split(',')
        properties['partition-profile-names'] = lpar_names

    if org_options['fenced-book-list']:
        value = parse_yaml_flow_style(
            cmd_ctx, '--fenced-book-list', org_options['fenced-book-list'])
        properties['fenced-book-list'] = value

    try:
        new_resetprofile = cpc.reset_activation_profiles.create(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("New resetprofile '{ip}' for CPC '{c}' has been created.".
               format(ip=new_resetprofile.properties['name'], c=cpc_name))


def cmd_resetprofile_delete(cmd_ctx, cpc_name, resetprofile_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    resetprofile = find_resetprofile(
        cmd_ctx, client, cpc_name, resetprofile_name)

    try:
        resetprofile.delete()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Reset activation profile '{ip}' for CPC '{c}' has been "
               "deleted.".format(ip=resetprofile_name, c=cpc_name))
