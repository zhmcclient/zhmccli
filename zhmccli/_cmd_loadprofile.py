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
Commands for load activation profiles for CPCs in classic mode.
"""

from __future__ import absolute_import

import click
from click_option_group import optgroup

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS, str2int
from ._cmd_cpc import find_cpc


def find_loadprofile(cmd_ctx, client, cpc_name, loadprofile_name):
    """
    Find a load activation profile by name and return its resource object.
    """
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    # The CPC must be in classic mode. We don't check that because it would
    # cause a GET to the CPC resource that we otherwise don't need.
    try:
        loadprofile = cpc.load_activation_profiles.find(
            name=loadprofile_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    return loadprofile


@cli.group('loadprofile', options_metavar=COMMAND_OPTIONS_METAVAR)
def loadprofile_group():
    """
    Command group for managing load activation profiles (classic mode only).

    "Load activation profiles" are used to load (= boot, IPL) an operating
    system or dump program (also known as "control program") into an LPAR.
    Load activation profiles include definitions for loading the
    control program.

    The commands in this group work only on CPCs in classic mode.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@loadprofile_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('cpc', type=str, metavar='[CPC]', required=False)
@add_options(LIST_OPTIONS)
@click.pass_obj
def loadprofile_list(cmd_ctx, cpc, **options):
    """
    List the load activation profiles for a CPC, or if omitted for all
    managed CPCs.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_loadprofile_list(cmd_ctx, cpc, options))


@loadprofile_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('cpc', type=str, metavar='CPC')
@click.argument('loadprofile', type=str, metavar='LOADPROFILE')
@click.pass_obj
def loadprofile_show(cmd_ctx, cpc, loadprofile, **options):
    """
    Show details of a load activation profile.

    The following properties are shown in addition to those returned by the HMC:

    \b
      - 'parent-name' - Name of the associated (parent) CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_loadprofile_show(cmd_ctx, cpc, loadprofile, options))


@loadprofile_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('cpc', type=str, metavar='CPC')
@click.argument('loadprofile', type=str, metavar='LOADPROFILE')
@optgroup.group('General options')
@optgroup.option('--description', type=str, required=False,
                 help='The new description for the load activation profile.')
@optgroup.group('Load configuration')
@optgroup.option('--ipl-type', type=str, metavar='IPLTYPE', required=False,
                 help='The new IPL type for the operating system. The IPL type '
                 'defines from where the control program for the LPAR will be '
                 'loaded:\n'
                 '\n'
                 '\b\n'
                 '  - "ipltype-scsi" - SCSI list-directed OS load\n'
                 '  - "ipltype-scsidump" - SCSI list-directed OS dump\n'
                 '  - "ipltype-nvmeload" – NVMe list-directed OS load '
                 '(z15 or later)\n'
                 '  - "ipltype-nvmedump" – NVMe list-directed OS dump '
                 '(z15 or later)\n'
                 '  - "ipltype-tape-load" - Tape Channel Command Word (CCW) '
                 'OS load (z16 or later)\n'
                 '  - "ipltype-tape-dump" - Tape Channel Command Word (CCW) '
                 'OS dump (z16 or later)\n'
                 '  - "ipltype-eckd-ccw-load" - ECKD Channel Command Word '
                 '(CCW) OS load (z16 or later)\n'
                 '  - "ipltype-eckd-ccw-dump" - ECKD Channel Command Word '
                 '(CCW) OS dump (z16 or later)\n'
                 '  - "ipltype-eckd-ld-load" - ECKD list-directed OS load '
                 '(z16 or later)\n'
                 '  - "ipltype-eckd-ld-dump" - ECKD list-directed OS dump '
                 '(z16 or later)\n'
                 '  - "ipltype-standard" - Channel Command Word (CCW) '
                 'standard load. This is present for\n'
                 '    compatibility and will be interpreted as one of the '
                 'new values.\n')
@optgroup.option('--load-address', type=str, required=False,
                 # Property: 'ipl-address'
                 help='The new IPL address (property "ipl-address"). '
                 'For NVMe IPL types, this is the FID of the NVMe device '
                 'as 4 hex characters in any lexical case. '
                 'For any other IPL types, this is the device number of the '
                 'boot device as 4 or 5 hex characters in any lexical case. '
                 'If empty, the IPL address will be taken from the load '
                 'activation profile.')
@optgroup.option('--load-parameter', type=str, required=False,
                 # Property: 'ipl-parameter'
                 help='The new IPL parameter (property "ipl-parameter"). This '
                 'is a short (0-8 characters)string passed to the control '
                 'program. Valid characters are "0"-"9", "A"-"Z", blank (" ") '
                 'and period ("."). On z14 and later, the characters "@", "$", '
                 'and "#" are valid in addition.')
@optgroup.option('--os-load-parameters', type=str, required=False,
                 # Property: 'os-specific-load-parameters'
                 help='The new operating system-specific load parameters '
                 '(property "os-specific-load-parameters"). This is a longer '
                 'string string passed to the control program. '
                 'Only used for the list-directed IPL types "ipltype-scsi", '
                 '"ipltype-scsidump", "ipltype-nvmeload", "ipltype-nvmedump", '
                 '"ipltype-eckd-ld-load", or "ipltype-eckd-ld-dump".')
@optgroup.option('--load-timeout', type=int, required=False,
                 help='The new amount of time, in seconds, to wait for the '
                 'load to complete (60-600).')
@optgroup.option('--store-status', type=bool, required=False,
                 # Property: 'store-status-indicator'
                 help='The new indicator for storing status values to their '
                 'assigned absolute storage locations before performing the '
                 'load of the dump program. The status values consist of the '
                 'processing unit timer, the clock comparator, the program '
                 'status word, and the contents of the processor registers. '
                 'Only used for the IPL types "ipltype-standard", '
                 '"ipltype-eckd-ld-dump", "ipltype-eckd-ccw-dump", or '
                 '"ipltype-tape-dump".')
@optgroup.option('--clear-memory', type=bool, required=False,
                 # Property: 'clear-indicator'
                 help='The new indicator for clearing the LPAR memory before '
                 'performing the load. '
                 'Only used for the IPL types "ipltype-standard", '
                 '"ipltype-scsi", "ipltype-nvmeload", "ipltype-eckd-ld-load", '
                 'or "ipltype-tape-load".')
@optgroup.option('--secure-boot', type=bool, required=False,
                 help='The new secure-boot indicator. It indicates whether the '
                 'software signature of the control program will be verified '
                 'using the secure-boot certificate(s) assigned to the LPAR. '
                 'Only used for the list-directed IPL types "ipltype-scsi", '
                 '"ipltype-scsidump", "ipltype-nvmeload", "ipltype-nvmedump", '
                 '"ipltype-eckd-ld-load", or "ipltype-eckd-ld-dump".')
@optgroup.option('--disk-partition-id', type=str, required=False,
                 # Properties: 'disk-partition-id' and
                 # 'disk-partition-id-automatic'
                 help='The new disk partition number (also called the boot '
                 'program selector), in decimal. The special value "auto" '
                 '(only valid on z16 or later) causes the disk partition '
                 'number to be determined automatically. '
                 'Only used for the list-directed IPL types "ipltype-scsi", '
                 '"ipltype-scsidump", "ipltype-nvmeload", "ipltype-nvmedump", '
                 '"ipltype-eckd-ld-load", or "ipltype-eckd-ld-dump".')
@optgroup.option('--worldwide-port-name', type=str, required=False,
                 help='The new worldwide port name (WWPN) of the SCSI boot '
                 'device, in hexadecimal. Only used for the SCSI IPL types '
                 '"ipltype-scsi" or "ipltype-scsidump".')
@optgroup.option('--logical-unit-number', type=str, required=False,
                 help='The new logical unit number of the SCSI boot device, '
                 'in hexadecimal. Only used for the SCSI IPL types '
                 '"ipltype-scsi" or "ipltype-scsidump".')
@optgroup.option('--boot-record-lba', type=str, required=False,
                 help='The new boot record logical block address the SCSI/NVMe '
                 'boot device, in hexadecimal. Only used for SCSI and NVMe IPL '
                 'types "ipltype-scsi", "ipltype-scsidump", '
                 '"ipltype-nvmeload", or "ipltype-nvmedump".')
@optgroup.option('--boot-record-location-cylinder', type=str, required=False,
                 help='The new boot record location cylinder value, in '
                 'hexadecimal. Only used for ECKD IPL types '
                 '"ipltype-eckd-ld-load" or "ipltype-eckd-ld-dump".')
@optgroup.option('--boot-record-location-head', type=str, required=False,
                 help='The new boot record location head value, in '
                 'hexadecimal. Only used for ECKD IPL types '
                 '"ipltype-eckd-ld-load" or "ipltype-eckd-ld-dump".')
@optgroup.option('--boot-record-location-record', type=str, required=False,
                 help='The new boot record location record value, in '
                 'hexadecimal. Only used for ECKD IPL types '
                 '"ipltype-eckd-ld-load" or "ipltype-eckd-ld-dump".')
@optgroup.option('--boot-record-location-use-volume-label', type=bool,
                 required=False,
                 help='The new indicator whether the boot record location '
                 'cylinder, head, and record should be determined by the '
                 'volume label. Only used for ECKD IPL types '
                 '"ipltype-eckd-ld-load" or "ipltype-eckd-ld-dump".')
@click.pass_obj
def loadprofile_update(cmd_ctx, cpc, loadprofile, **options):
    """
    Update the properties of a load activation profile.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_loadprofile_update(cmd_ctx, cpc, loadprofile, options))


@loadprofile_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('cpc', type=str, metavar='CPC')
@optgroup.group('General options')
@optgroup.option('--name', type=str, required=True,
                 # Property: 'profile-name'
                 help='The name of the new load activation profile. '
                 'The names of reset, image, and load activation profiles are '
                 'all in the same namespace for each CPC and must be unique '
                 'within that namespace.')
@optgroup.option('--copy-name', type=str, required=False,
                 help='The name of an existing load activation profile whose '
                 'properties act as defaults for options not specified in '
                 'this command. Default: The load activation profile named '
                 '"DEFAULTLOAD".')
@optgroup.option('--description', type=str, required=False,
                 help='The description for the new load activation profile.')
@optgroup.group('Load configuration')
@optgroup.option('--ipl-type', type=str, metavar='IPLTYPE', required=False,
                 help='The IPL type for the operating system. The IPL type '
                 'defines from where the control program for the LPAR will be '
                 'loaded:\n'
                 '\n'
                 '\b\n'
                 '  - "ipltype-scsi" - SCSI list-directed OS load\n'
                 '  - "ipltype-scsidump" - SCSI list-directed OS dump\n'
                 '  - "ipltype-nvmeload" – NVMe list-directed OS load '
                 '(z15 or later)\n'
                 '  - "ipltype-nvmedump" – NVMe list-directed OS dump '
                 '(z15 or later)\n'
                 '  - "ipltype-tape-load" - Tape Channel Command Word (CCW) '
                 'OS load (z16 or later)\n'
                 '  - "ipltype-tape-dump" - Tape Channel Command Word (CCW) '
                 'OS dump (z16 or later)\n'
                 '  - "ipltype-eckd-ccw-load" - ECKD Channel Command Word '
                 '(CCW) OS load (z16 or later)\n'
                 '  - "ipltype-eckd-ccw-dump" - ECKD Channel Command Word '
                 '(CCW) OS dump (z16 or later)\n'
                 '  - "ipltype-eckd-ld-load" - ECKD list-directed OS load '
                 '(z16 or later)\n'
                 '  - "ipltype-eckd-ld-dump" - ECKD list-directed OS dump '
                 '(z16 or later)\n'
                 '  - "ipltype-standard" - Channel Command Word (CCW) '
                 'standard load. This is present for\n'
                 '    compatibility and will be interpreted as one of the '
                 'new values.\n')
@optgroup.option('--load-address', type=str, required=False,
                 # Property: 'ipl-address'
                 help='The IPL address (property "ipl-address"). '
                 'For NVMe IPL types, this is the FID of the NVMe device '
                 'as 4 hex characters in any lexical case. '
                 'For any other IPL types, this is the device number of the '
                 'boot device as 4 or 5 hex characters in any lexical case. '
                 'If empty, the IPL address will be taken from the load '
                 'activation profile.')
@optgroup.option('--load-parameter', type=str, required=False,
                 # Property: 'ipl-parameter'
                 help='The IPL parameter (property "ipl-parameter"). This '
                 'is a short (0-8 characters)string passed to the control '
                 'program. Valid characters are "0"-"9", "A"-"Z", blank (" ") '
                 'and period ("."). On z14 and later, the characters "@", "$", '
                 'and "#" are valid in addition.')
@optgroup.option('--os-load-parameters', type=str, required=False,
                 # Property: 'os-specific-load-parameters'
                 help='The operating system-specific load parameters '
                 '(property "os-specific-load-parameters"). This is a longer '
                 'string string passed to the control program. '
                 'Only used for the list-directed IPL types "ipltype-scsi", '
                 '"ipltype-scsidump", "ipltype-nvmeload", "ipltype-nvmedump", '
                 '"ipltype-eckd-ld-load", or "ipltype-eckd-ld-dump".')
@optgroup.option('--load-timeout', type=int, required=False,
                 help='The amount of time, in seconds, to wait for the '
                 'load to complete (60-600).')
@optgroup.option('--store-status', type=bool, required=False,
                 # Property: 'store-status-indicator'
                 help='The indicator for storing status values to their '
                 'assigned absolute storage locations before performing the '
                 'load of the dump program. The status values consist of the '
                 'processing unit timer, the clock comparator, the program '
                 'status word, and the contents of the processor registers. '
                 'Only used for the IPL types "ipltype-standard", '
                 '"ipltype-eckd-ld-dump", "ipltype-eckd-ccw-dump", or '
                 '"ipltype-tape-dump".')
@optgroup.option('--clear-memory', type=bool, required=False,
                 # Property: 'clear-indicator'
                 help='The indicator for clearing the LPAR memory before '
                 'performing the load. '
                 'Only used for the IPL types "ipltype-standard", '
                 '"ipltype-scsi", "ipltype-nvmeload", "ipltype-eckd-ld-load", '
                 'or "ipltype-tape-load".')
@optgroup.option('--secure-boot', type=bool, required=False,
                 help='The secure-boot indicator. It indicates whether the '
                 'software signature of the control program will be verified '
                 'using the secure-boot certificate(s) assigned to the LPAR. '
                 'Only used for the list-directed IPL types "ipltype-scsi", '
                 '"ipltype-scsidump", "ipltype-nvmeload", "ipltype-nvmedump", '
                 '"ipltype-eckd-ld-load", or "ipltype-eckd-ld-dump".')
@optgroup.option('--disk-partition-id', type=str, required=False,
                 # Properties: 'disk-partition-id' and
                 # 'disk-partition-id-automatic'
                 help='The disk partition number (also called the boot '
                 'program selector), in decimal. The special value "auto" '
                 '(only valid on z16 or later) causes the disk partition '
                 'number to be determined automatically. '
                 'Only used for the list-directed IPL types "ipltype-scsi", '
                 '"ipltype-scsidump", "ipltype-nvmeload", "ipltype-nvmedump", '
                 '"ipltype-eckd-ld-load", or "ipltype-eckd-ld-dump".')
@optgroup.option('--worldwide-port-name', type=str, required=False,
                 help='The worldwide port name (WWPN) of the SCSI boot '
                 'device, in hexadecimal. Only used for the SCSI IPL types '
                 '"ipltype-scsi" or "ipltype-scsidump".')
@optgroup.option('--logical-unit-number', type=str, required=False,
                 help='The logical unit number of the SCSI boot device, '
                 'in hexadecimal. Only used for the SCSI IPL types '
                 '"ipltype-scsi" or "ipltype-scsidump".')
@optgroup.option('--boot-record-lba', type=str, required=False,
                 help='The boot record logical block address the SCSI/NVMe '
                 'boot device, in hexadecimal. Only used for SCSI and NVMe IPL '
                 'types "ipltype-scsi", "ipltype-scsidump", '
                 '"ipltype-nvmeload", or "ipltype-nvmedump".')
@optgroup.option('--boot-record-location-cylinder', type=str, required=False,
                 help='The boot record location cylinder value, in '
                 'hexadecimal. Only used for ECKD IPL types '
                 '"ipltype-eckd-ld-load" or "ipltype-eckd-ld-dump".')
@optgroup.option('--boot-record-location-head', type=str, required=False,
                 help='The boot record location head value, in '
                 'hexadecimal. Only used for ECKD IPL types '
                 '"ipltype-eckd-ld-load" or "ipltype-eckd-ld-dump".')
@optgroup.option('--boot-record-location-record', type=str, required=False,
                 help='The boot record location record value, in '
                 'hexadecimal. Only used for ECKD IPL types '
                 '"ipltype-eckd-ld-load" or "ipltype-eckd-ld-dump".')
@optgroup.option('--boot-record-location-use-volume-label', type=bool,
                 required=False,
                 help='The indicator whether the boot record location '
                 'cylinder, head, and record should be determined by the '
                 'volume label. Only used for ECKD IPL types '
                 '"ipltype-eckd-ld-load" or "ipltype-eckd-ld-dump".')
@click.pass_obj
def loadprofile_create(cmd_ctx, cpc, **options):
    """
    Create a load activation profile for a CPC (Only HMC 2.16 and later).

    The default values for any options not specified will be the corresponding
    property values of the default load activation profile (that is the
    profile specified with the --copy-name option, or if that option is not
    specified, the profile named "DEFAULTLOAD").

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_loadprofile_create(cmd_ctx, cpc, options))


@loadprofile_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('cpc', type=str, metavar='CPC')
@click.argument('loadprofile', type=str, metavar='LOADPROFILE')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the load activation '
              'profile.',
              prompt='Are you sure you want to delete this load activation '
              'profile ?')
@click.pass_obj
def loadprofile_delete(cmd_ctx, cpc, loadprofile):
    """
    Delete a load activation profile (Only HMC 2.16 and later).

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_loadprofile_delete(cmd_ctx, cpc, loadprofile))


def cmd_loadprofile_list(cmd_ctx, cpc_name, options):
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
            'ipl-type',
            'description',
        ])
    if options['uri']:
        show_list.extend([
            'element-uri',
        ])

    loadprofiles = []
    for cpc in cpcs:
        try:
            loadprofiles.extend(cpc.load_activation_profiles.list())
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)

        for loadprofile in loadprofiles:
            cpc = loadprofile.manager.parent
            additions['cpc'][loadprofile.uri] = cpc.name

    try:
        print_resources(
            cmd_ctx, loadprofiles, cmd_ctx.output_format, show_list,
            additions, all=options['all'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_loadprofile_show(cmd_ctx, cpc_name, loadprofile_name, options):
    # pylint: disable=missing-function-docstring,unused-argument

    client = zhmcclient.Client(cmd_ctx.session)
    loadprofile = find_loadprofile(
        cmd_ctx, client, cpc_name, loadprofile_name)

    try:
        loadprofile.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(loadprofile.properties)

    # Add artificial property 'parent-name'
    properties['parent-name'] = cpc_name

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def handle_special_loadprofile_options(cmd_ctx, org_options, properties):
    """
    Handle special create and update options (i.e. those that are set to
    None in the name_map). The options are taken from org_options and
    put into properties.
    """

    if org_options['disk-partition-id'] == 'auto':
        properties['disk-partition-id-automatic'] = True
        # 'disk-partition-id will be unchanged
    elif org_options['disk-partition-id'] is not None:
        properties['disk-partition-id-automatic'] = False
        properties['disk-partition-id'] = str2int(
            cmd_ctx, 'disk-partition-id', org_options['disk-partition-id'])


def cmd_loadprofile_update(cmd_ctx, cpc_name, loadprofile_name, options):
    # pylint: disable=missing-function-docstring
    # pylint: disable=unreachable

    client = zhmcclient.Client(cmd_ctx.session)
    loadprofile = find_loadprofile(
        cmd_ctx, client, cpc_name, loadprofile_name)

    name_map = {
        'store-status': 'store-status-indicator',
        'clear-memory': 'clear-indicator',
        'load-address': 'ipl-address',
        'load-parameter': 'ipl-parameter',
        'os-load-parameters': 'os-specific-load-parameters',
        'disk-partition-id': None,
    }
    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    handle_special_loadprofile_options(cmd_ctx, org_options, properties)

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating load activation "
                   "profile '{lp}' for CPC '{c}'.".
                   format(lp=loadprofile_name, c=cpc_name))
        return

    try:
        loadprofile.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Load activation profile '{lp}' for CPC '{c}' has been updated.".
               format(lp=loadprofile_name, c=cpc_name))


def cmd_loadprofile_create(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring
    # pylint: disable=unreachable

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    name_map = {
        'name': 'profile-name',
        'store-status': 'store-status-indicator',
        'clear-memory': 'clear-indicator',
        'load-address': 'ipl-address',
        'load-parameter': 'ipl-parameter',
        'os-load-parameters': 'os-specific-load-parameters',
        'disk-partition-id': None,
    }

    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    handle_special_loadprofile_options(cmd_ctx, org_options, properties)

    try:
        new_loadprofile = cpc.load_activation_profiles.create(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("New loadprofile '{lp}' for CPC '{c}' has been created.".
               format(lp=new_loadprofile.properties['name'], c=cpc_name))


def cmd_loadprofile_delete(cmd_ctx, cpc_name, loadprofile_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    loadprofile = find_loadprofile(
        cmd_ctx, client, cpc_name, loadprofile_name)

    try:
        loadprofile.delete()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Load activation profile '{lp}' for CPC '{c}' has been deleted.".
               format(lp=loadprofile_name, c=cpc_name))
