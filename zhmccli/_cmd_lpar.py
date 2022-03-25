# Copyright 2016-2019 IBM Corp. All Rights Reserved.
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
Commands for LPARs in classic mode.
"""

from __future__ import absolute_import

import logging
import click

import zhmcclient
from .zhmccli import cli, CONSOLE_LOGGER_NAME
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    part_console, click_exception, add_options, LIST_OPTIONS, TABLE_FORMATS, \
    hide_property, ASYNC_TIMEOUT_OPTIONS
from ._cmd_cpc import find_cpc


def find_lpar(cmd_ctx, client, cpc_or_name, lpar_name):
    """
    Find an LPAR by name and return its resource object.
    """
    if isinstance(cpc_or_name, zhmcclient.Cpc):
        cpc_name = cpc_or_name.name
    else:
        cpc_name = cpc_or_name

    if client.version_info() >= (2, 20):  # Starting with HMC 2.14.0
        # This approach is faster than going through the CPC.
        # In addition, starting with HMC API version 3.6 (an update to
        # HMC 2.15.0), this approach supports users that do not have object
        # access permission to the parent CPC of the LPAR.
        lpars = client.consoles.console.list_permitted_lpars(
            filter_args={'name': lpar_name, 'cpc-name': cpc_name})
        if len(lpars) != 1:
            raise click_exception(
                "Could not find LPAR '{p}' in CPC '{c}'.".
                format(p=lpar_name, c=cpc_name),
                cmd_ctx.error_format)
        lpar = lpars[0]
    else:
        if isinstance(cpc_or_name, zhmcclient.Cpc):
            cpc = cpc_or_name
        else:
            cpc = find_cpc(cmd_ctx, client, cpc_name)
        # The CPC must not be in DPM mode. We don't check that because it would
        # cause a GET to the CPC resource that we otherwise don't need.
        try:
            lpar = cpc.lpars.find(name=lpar_name)
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)

    return lpar


@cli.group('lpar', options_metavar=COMMAND_OPTIONS_METAVAR)
def lpar_group():
    """
    Command group for managing LPARs (classic mode only).

    The commands in this group work only on CPCs in classic mode.

    The term 'LPAR' (logical partition) is used only for CPCs in classic mode.
    For CPCs in DPM mode, the term 'partition' is used.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@lpar_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='[CPC]', required=False)
@click.option('--type', is_flag=True, required=False, hidden=True)
@add_options(LIST_OPTIONS)
@click.pass_obj
def lpar_list(cmd_ctx, cpc, **options):
    """
    List the permitted LPARs in a CPC or in all managed CPCs.

    Note that partitions of CPCs in DPM mode are not included.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_lpar_list(cmd_ctx, cpc, options))


@lpar_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('LPAR', type=str, metavar='LPAR')
@click.option('--all', is_flag=True, required=False,
              help='Show all properties. Default: Hide some properties in '
              'table output formats.')
@click.pass_obj
def lpar_show(cmd_ctx, cpc, lpar, **options):
    """
    Show details of an LPAR in a CPC.

    \b
    In table output formats, the following properties are hidden by default
    but can be shown by using the --all option:
      - program-status-word-information

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_lpar_show(cmd_ctx, cpc, lpar, options))


@lpar_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('LPAR', type=str, metavar='LPAR')
@click.option('--acceptable-status', type=str, required=False,
              help='The new set of acceptable operational status values.')
# TODO: Support multiple values for acceptable-status
@click.option('--next-activation-profile', type=str, required=False,
              help='The name of the new next image or load activation '
              'profile.')
# TODO: Add support for updating processor capping/sharing/weight related props
@click.option('--zaware-host-name', type=str, required=False,
              help='The new hostname for IBM zAware. '
              'Empty string sets no hostname. '
              '(only for LPARs in zaware activation mode).')
@click.option('--zaware-master-userid', type=str, required=False,
              help='The new master userid for IBM zAware. '
              'Empty string sets no master userid. '
              '(only for LPARs in zaware activation mode).')
@click.option('--zaware-master-password', type=str, required=False,
              help='The new master password for IBM zAware. '
              'Empty string sets no master password. '
              '(only for LPARs in zaware activation mode).')
# TODO: Change zAware master password option to ask for password
# TODO: Add support for updating zAware network-related properties
@click.option('--ssc-host-name', type=str, required=False,
              help='The new hostname for the SSC appliance. '
              'Empty string sets no hostname. '
              '(only for LPARs in ssc activation mode).')
@click.option('--ssc-master-userid', type=str, required=False,
              help='The new master userid for the SSC appliance. '
              'Empty string sets no master userid. '
              '(only for LPARs in ssc activation mode).')
@click.option('--ssc-master-password', type=str, required=False,
              help='The new master password for the SSC appliance. '
              'Empty string sets no master password. '
              '(only for LPARs in ssc activation mode).')
# TODO: Change SSC master password option to ask for password
# TODO: Add support for updating SSC network-related properties
@click.pass_obj
def lpar_update(cmd_ctx, cpc, lpar, **options):
    """
    Update the properties of an LPAR.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.

    \b
    Limitations:
      * The --acceptable-status option does not support multiple values.
      * The processor capping/sharing/weight related properties cannot be
        updated.
      * The network-related properties for zaware and ssc cannot beupdated.
      * The --zaware-master-password and --ssc-master-password options do not
        ask for the password.
    """
    cmd_ctx.execute_cmd(lambda: cmd_lpar_update(cmd_ctx, cpc, lpar, options))


@lpar_group.command('activate', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('LPAR', type=str, metavar='LPAR')
@click.option('--activation-profile-name', type=str, required=False,
              help='Use a specific activation profile. Default: Use the one '
                   'specified in the next-activation-profile-name property '
                   'of the LPAR.')
@click.option('--allow-status-exceptions', is_flag=True, required=False,
              help='Allow status "exceptions" as a valid end status.')
@click.option('--force', is_flag=True, required=False,
              help='Controls whether this command is permitted when the '
                   'LPAR is in "operating" status.')
@add_options(ASYNC_TIMEOUT_OPTIONS)
@click.pass_obj
def lpar_activate(cmd_ctx, cpc, lpar, **options):
    """
    Activate an LPAR.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_lpar_activate(cmd_ctx, cpc, lpar, options))


@lpar_group.command('deactivate', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('LPAR', type=str, metavar='LPAR')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deactivation of the LPAR.',
              prompt='Are you sure you want to deactivate the LPAR ?')
@click.option('--allow-status-exceptions', is_flag=True, required=False,
              help='Allow status "exceptions" as a valid end status.')
@click.option('--force', is_flag=True, required=False,
              help='Controls whether this command is permitted when the '
                   'LPAR is in "operating" status.')
@add_options(ASYNC_TIMEOUT_OPTIONS)
@click.pass_obj
def lpar_deactivate(cmd_ctx, cpc, lpar, **options):
    """
    Deactivate an LPAR.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_lpar_deactivate(cmd_ctx, cpc, lpar,
                                                    options))


@lpar_group.command('load', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('LPAR', type=str, metavar='LPAR')
@click.argument('LOAD-ADDRESS', type=str, metavar='LOAD-ADDRESS')
@click.option('--load-parameter', type=str, required=False,
              help='Provides additional control over the outcome of a '
              'Load operation. Default: empty')
@click.option('--clear-indicator/--no-clear-indicator', is_flag=True,
              required=False,
              help='Controls whether the memory should be cleared before '
              'performing Load operation.')
@click.option('--store-status-indicator', is_flag=True, required=False,
              help='Controls whether the status should be stored before '
              'performing Load operation.')
@click.option('--allow-status-exceptions', is_flag=True, required=False,
              help='Allow status "exceptions" as a valid end status.')
@click.option('--force', is_flag=True, required=False,
              help='Controls whether this command is permitted when the '
                   'LPAR is in "operating" status.')
@add_options(ASYNC_TIMEOUT_OPTIONS)
@click.pass_obj
def lpar_load(cmd_ctx, cpc, lpar, load_address, **options):
    """
    Load (Boot, IML) an LPAR.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_lpar_load(cmd_ctx, cpc, lpar,
                                              load_address, options))


@lpar_group.command('console', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('LPAR', type=str, metavar='LPAR')
@click.option('--refresh', is_flag=True, required=False,
              help='Include refresh messages.')
@click.pass_obj
def lpar_console(cmd_ctx, cpc, lpar, **options):
    """
    Establish an interactive session with the console of the operating system
    running in an LPAR.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_lpar_console(cmd_ctx, cpc, lpar, options))


@lpar_group.command('stop', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('LPAR', type=str, metavar='LPAR')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm stopping of the LPAR.',
              prompt='Are you sure you want to stop the LPAR ?')
@click.option('--allow-status-exceptions', is_flag=True, required=False,
              help='Allow status "exceptions" as a valid end status.')
@add_options(ASYNC_TIMEOUT_OPTIONS)
@click.pass_obj
def lpar_stop(cmd_ctx, cpc, lpar, **options):
    """
    Stop the processors from processing instructions of an LPAR.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_lpar_stop(cmd_ctx, cpc, lpar, options))


@lpar_group.command('psw-restart', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('LPAR', type=str, metavar='LPAR')
@click.option('--allow-status-exceptions', is_flag=True, required=False,
              help='Allow status "exceptions" as a valid end status.')
@add_options(ASYNC_TIMEOUT_OPTIONS)
@click.pass_obj
def lpar_psw_restart(cmd_ctx, cpc, lpar, **options):
    """
    Restart the first available processor of the LPAR.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_lpar_psw_restart(cmd_ctx, cpc, lpar,
                                                     options))


@lpar_group.command('scsi-load', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('LPAR', type=str, metavar='LPAR')
@click.argument('LOAD-ADDRESS', type=str, metavar='LOAD-ADDRESS')
@click.argument('WWPN', type=str, metavar='WWPN')
@click.argument('LUN', type=str, metavar='LUN')
@click.option('--load-parameter', type=str, required=False,
              help='Provides additional control over the outcome of a '
              'Load operation. Default: empty')
@click.option('--disk-partition-id', type=int, required=False,
              help='Provides boot program selector. Default: 0')
@click.option('--operating-system-specific-load-parameters', type=str,
              required=False, help='Provides specific load parameters. '
              'Default: empty')
@click.option('--boot-record-logical-block-address', type=str,
              required=False, help='Provides the hexadecimal boot record '
              'logical block address. Default: hex zeros')
@click.option('--secure-boot', type=bool, required=False,
              help='Check the software signature of what is loaded against '
              'what the distributor signed it with. '
              'Requires z15 or later (recommended bundle levels on z15 are '
              'at least H28 and S38), requires the boot volume to be prepared '
              'for secure boot '
              '(see https://linux.mainframe.blog/secure-boot/). Default: False')
@click.option('--force', is_flag=True, required=False,
              help='Controls whether this command is permitted when the '
              'LPAR is in "operating" status.')
@click.option('--allow-status-exceptions', is_flag=True, required=False,
              help='Allow status "exceptions" as a valid end status.')
@add_options(ASYNC_TIMEOUT_OPTIONS)
@click.pass_obj
def lpar_scsi_load(cmd_ctx, cpc, lpar, load_address, wwpn, lun, **options):
    """
    Load (boot) this LPAR from a designated SCSI device.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_lpar_scsi_load(cmd_ctx, cpc, lpar,
                                                   load_address, wwpn, lun,
                                                   options))


@lpar_group.command('scsi-dump', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('LPAR', type=str, metavar='LPAR')
@click.argument('LOAD-ADDRESS', type=str, metavar='LOAD-ADDRESS')
@click.argument('WWPN', type=str, metavar='WWPN')
@click.argument('LUN', type=str, metavar='LUN')
@click.option('--load-parameter', type=str, required=False,
              help='Provides additional control over the outcome of a '
              'Load operation. Default: empty')
@click.option('--disk-partition-id', type=int, required=False,
              help='Provides boot program selector. Default: 0')
@click.option('--operating-system-specific-load-parameters', type=str,
              required=False, help='Provides specific load parameters. '
              'Default: empty')
@click.option('--boot-record-logical-block-address', type=str,
              required=False, help='Provides the hexadecimal boot record '
              'logical block address. Default: hex zeros')
@click.option('--secure-boot', type=bool, required=False,
              help='Check the software signature of what is loaded against '
              'what the distributor signed it with. '
              'Requires z15 or later (recommended bundle levels on z15 are '
              'at least H28 and S38), requires the boot volume to be prepared '
              'for secure boot '
              '(see https://linux.mainframe.blog/secure-boot/). Default: False')
@click.option('--os-ipl-token', type=str,
              required=False, help='Provides the hexadecimal OS-IPL-token '
              'parameter. Default: empty')
@click.option('--allow-status-exceptions', is_flag=True, required=False,
              help='Allow status "exceptions" as a valid end status.')
@click.option('--force', is_flag=True, required=False,
              help='Controls whether this command is permitted when the '
              'LPAR is in "operating" status.')
@add_options(ASYNC_TIMEOUT_OPTIONS)
@click.pass_obj
def lpar_scsi_dump(cmd_ctx, cpc, lpar, load_address, wwpn, lun, **options):
    """
    Load a standalone dump program from a designated SCSI device.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_lpar_scsi_dump(cmd_ctx, cpc, lpar,
                                                   load_address, wwpn, lun,
                                                   options))


def cmd_lpar_list(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)

    if client.version_info() >= (2, 20):  # Starting with HMC 2.14.0
        # This approach is faster than going through the CPC.
        # In addition, starting with HMC API version 3.6 (an update to
        # HMC 2.15.0), this approach supports users that do not have object
        # access permission to the CPC.
        filter_args = {}
        if cpc_name:
            filter_args['cpc-name'] = cpc_name
        lpars = client.consoles.console.list_permitted_lpars(
            filter_args=filter_args)
    else:
        filter_args = {}
        if cpc_name:
            filter_args['name'] = cpc_name
        try:
            cpcs = client.cpcs.list(filter_args=filter_args)
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)
        lpars = []
        for cpc in cpcs:
            try:
                lpars.extend(cpc.lpars.list())
            except zhmcclient.Error as exc:
                raise click_exception(exc, cmd_ctx.error_format)

    if options['type']:
        click.echo("The --type option is deprecated and type information "
                   "is now always shown.")

    # Prepare the additions dict of dicts. It contains additional
    # (=non-resource) property values by property name and by resource URI.
    # Depending on options, some of them will not be populated.
    additions = {}
    additions['cpc'] = {}

    show_list = [
        'name',
        'cpc',
    ]
    if not options['names_only']:
        show_list.extend([
            'status',
            'activation-mode',
            'os-type',
            'workload-manager-enabled',
        ])
    if options['uri']:
        show_list.extend([
            'object-uri',
        ])

    for lpar in lpars:
        cpc = lpar.manager.parent
        additions['cpc'][lpar.uri] = cpc.name

    try:
        print_resources(cmd_ctx, lpars, cmd_ctx.output_format, show_list,
                        additions, all=options['all'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_lpar_show(cmd_ctx, cpc_name, lpar_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    lpar = find_lpar(cmd_ctx, client, cpc_name, lpar_name)

    try:
        lpar.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(lpar.properties)

    # Hide some long or deeply nested properties in table output formats.
    if not options['all'] and cmd_ctx.output_format in TABLE_FORMATS:
        hide_property(properties, 'program-status-word-information')

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def cmd_lpar_update(cmd_ctx, cpc_name, lpar_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    lpar = find_lpar(cmd_ctx, client, cpc_name, lpar_name)

    name_map = {
        'next-activation-profile': 'next-activation-profile-name',
    }
    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    if org_options['zaware-host-name'] == '':
        properties['zaware-host-name'] = None
    if org_options['zaware-master-userid'] == '':
        properties['zaware-master-userid'] = None
    if org_options['zaware-master-password'] == '':
        properties['zaware-master-password'] = None

    if org_options['ssc-host-name'] == '':
        properties['ssc-host-name'] = None
    if org_options['ssc-master-userid'] == '':
        properties['ssc-master-userid'] = None
    if org_options['ssc-master-password'] == '':
        properties['ssc-master-password'] = None

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating LPAR '{p}'.".
                   format(p=lpar_name))
        return

    try:
        lpar.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    # LPARs cannot be renamed.
    click.echo("LPAR '{p}' has been updated.".format(p=lpar_name))


def cmd_lpar_activate(cmd_ctx, cpc_name, lpar_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    lpar = find_lpar(cmd_ctx, client, cpc_name, lpar_name)

    try:
        lpar.activate(wait_for_completion=True, **options)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Activation of LPAR '{p}' is complete.".format(p=lpar_name))


def cmd_lpar_deactivate(cmd_ctx, cpc_name, lpar_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    lpar = find_lpar(cmd_ctx, client, cpc_name, lpar_name)

    try:
        lpar.deactivate(wait_for_completion=True, **options)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Deactivation of LPAR '{p}' is complete.".format(p=lpar_name))


def cmd_lpar_load(cmd_ctx, cpc_name, lpar_name, load_address, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    lpar = find_lpar(cmd_ctx, client, cpc_name, lpar_name)

    try:
        lpar.load(load_address, wait_for_completion=True, **options)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Loading of LPAR '{p}' is complete.".format(p=lpar_name))


def cmd_lpar_console(cmd_ctx, cpc_name, lpar_name, options):
    # pylint: disable=missing-function-docstring

    logger = logging.getLogger(CONSOLE_LOGGER_NAME)

    client = zhmcclient.Client(cmd_ctx.session)
    lpar = find_lpar(cmd_ctx, client, cpc_name, lpar_name)

    refresh = options['refresh']

    cmd_ctx.spinner.stop()

    try:
        part_console(cmd_ctx.session, lpar, refresh, logger)
    except zhmcclient.Error as exc:
        raise click.ClickException(
            "{exc}: {msg}".format(exc=exc.__class__.__name__, msg=exc))


def cmd_lpar_stop(cmd_ctx, cpc_name, lpar_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    lpar = find_lpar(cmd_ctx, client, cpc_name, lpar_name)

    try:
        lpar.stop(wait_for_completion=True, **options)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Stopping of LPAR '{p}' is complete.".format(p=lpar_name))


def cmd_lpar_psw_restart(cmd_ctx, cpc_name, lpar_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    lpar = find_lpar(cmd_ctx, client, cpc_name, lpar_name)

    try:
        lpar.psw_restart(wait_for_completion=True, **options)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("PSW restart of LPAR '{p}' is complete.".format(p=lpar_name))


def cmd_lpar_scsi_load(cmd_ctx, cpc_name, lpar_name, load_address,
                       wwpn, lun, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    lpar = find_lpar(cmd_ctx, client, cpc_name, lpar_name)

    try:
        lpar.scsi_load(load_address, wwpn, lun, wait_for_completion=True,
                       **options)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("SCSI Load of LPAR '{p}' is complete.".format(p=lpar_name))


def cmd_lpar_scsi_dump(cmd_ctx, cpc_name, lpar_name, load_address,
                       wwpn, lun, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    lpar = find_lpar(cmd_ctx, client, cpc_name, lpar_name)

    try:
        lpar.scsi_dump(load_address, wwpn, lun, wait_for_completion=True,
                       **options)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("SCSI Dump of LPAR '{p}' is complete.".format(p=lpar_name))
