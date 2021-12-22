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
Commands for partitions in DPM mode.
"""

from __future__ import absolute_import
from __future__ import print_function

import os
import io
import logging

import click

import zhmcclient
from .zhmccli import cli, CONSOLE_LOGGER_NAME
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    part_console, click_exception, storage_management_feature, \
    add_options, LIST_OPTIONS, TABLE_FORMATS, hide_property, \
    ASYNC_TIMEOUT_OPTIONS
from ._cmd_cpc import find_cpc
from ._cmd_storagegroup import find_storagegroup
from ._cmd_metrics import get_metric_values


# Defaults for partition creation
DEFAULT_IFL_PROCESSORS = 1
DEFAULT_INITIAL_MEMORY_MB = 1024
DEFAULT_MAXIMUM_MEMORY_MB = 1024
DEFAULT_PROCESSOR_MODE = 'shared'
PARTITION_TYPES = ['ssc', 'linux', 'zvm']
DEFAULT_PARTITION_TYPE = 'linux'
DEFAULT_SSC_BOOT = 'installer'
DEFAULT_PROCESSING_WEIGHT = 100
MIN_PROCESSING_WEIGHT = 1
MAX_PROCESSING_WEIGHT = 999


def find_partition(cmd_ctx, client, cpc_or_name, partition_name):
    """
    Find a partition by name and return its resource object.
    """
    if isinstance(cpc_or_name, zhmcclient.Cpc):
        cpc_name = cpc_or_name.name
    else:
        cpc_name = cpc_or_name

    if client.version_info() >= (2, 20):  # Starting with HMC 2.14.0
        # This approach is faster than going through the CPC.
        # In addition, this approach supports users that do not have object
        # access permission to the parent CPC of the LPAR.
        partitions = client.consoles.console.list_permitted_partitions(
            filter_args={'name': partition_name, 'cpc-name': cpc_name})
        if len(partitions) != 1:
            raise click_exception(
                "Could not find partition '{p}' in CPC '{c}'.".
                format(p=partition_name, c=cpc_name),
                cmd_ctx.error_format)
        partition = partitions[0]
    else:
        if isinstance(cpc_or_name, zhmcclient.Cpc):
            cpc = cpc_or_name
        else:
            cpc = find_cpc(cmd_ctx, client, cpc_or_name)
        # The CPC must be in DPM mode. We don't check that because it would
        # cause a GET to the CPC resource that we otherwise don't need.
        try:
            partition = cpc.partitions.find(name=partition_name)
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)

    return partition


@cli.group('partition', options_metavar=COMMAND_OPTIONS_METAVAR)
def partition_group():
    """
    Command group for managing partitions (DPM mode only).

    The commands in this group work only on CPCs that are in DPM mode.

    The term 'partition' is used only for CPCs in DPM mode.
    For CPCs in classic mode, the term 'LPAR' (logical partition) is used.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@partition_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='[CPC]', required=False)
@click.option('--type', is_flag=True, required=False, hidden=True)
@add_options(LIST_OPTIONS)
@click.option('--ifl-usage', is_flag=True, required=False,
              help='Show additional properties for IFL usage.')
@click.option('--cp-usage', is_flag=True, required=False,
              help='Show additional properties for CP usage.')
@click.option('--memory-usage', is_flag=True, required=False,
              help='Show additional properties for memory usage.')
@click.option('--help-usage', is_flag=True, required=False,
              help='Help on the usage related options.')
@click.pass_obj
def partition_list(cmd_ctx, cpc, **options):
    """
    List the permitted partitions in a CPC or in all managed CPCs.

    Note that LPARs of CPCs in classic mode are not included.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_partition_list(cmd_ctx, cpc, options))


@partition_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.option('--all', is_flag=True, required=False,
              help='Show all properties. Default: Hide some properties in '
              'table output formats.')
@click.pass_obj
def partition_show(cmd_ctx, cpc, partition, **options):
    """
    Show the details of a partition in a CPC.

    \b
    In table output formats, the following properties are hidden by default
    but can be shown by using the --all option:
      - crypto-configuration

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_partition_show(cmd_ctx, cpc, partition, options))


@partition_group.command('start', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@add_options(ASYNC_TIMEOUT_OPTIONS)
@click.pass_obj
def partition_start(cmd_ctx, cpc, partition, **options):
    """
    Start a partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_partition_start(
        cmd_ctx, cpc, partition, options))


@partition_group.command('stop', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@add_options(ASYNC_TIMEOUT_OPTIONS)
@click.pass_obj
def partition_stop(cmd_ctx, cpc, partition, **options):
    """
    Stop a partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_partition_stop(
        cmd_ctx, cpc, partition, options))


@partition_group.command('dump', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.option('--volume', type=str, required=True,
              help='The storage volume that contains the dump program. '
              'For CPCs with the storage management feature (z14 and later): '
              'A string of the form "SG/SV" where SG is the name '
              'of the storage group resource attached to the partition and SV '
              'is the name of the storage volume in that storage group, or of '
              'the form "UUID" where UUID is the UUID of the storage volume '
              'on the storage array (also shown in the HMC GUI). The storage '
              'volume may be of type FCP or FICON. '
              'For CPCs without the storage management feature (z13 and '
              'earlier): A string of the form "HBA/WWPN/LUN", where HBA is the '
              'name of the HBA resource in the partition and WWPN and LUN '
              'identify the storage array and storage volume thereon. The '
              'storage volume must be of type FCP.')
@click.option('--lba', type=str, required=False, default='0',
              help='The logical block number of the anchor point for locating '
              'the dump program on the storage volume. Default: 0')
@click.option('--configuration', type=int, required=False, default=0,
              help='A selector that is passed to the dump program for '
              'selecting the boot configuration to use. 0 means to use the '
              'default boot configuration. Default: 0')
@click.option('--parameters', type=str, required=False, default='',
              help='A parameter string that is passed to the dump program as '
              'boot parameters. Default: empty string')
@click.option('--timeout', type=int, required=False, default=60,
              help='The time in seconds that is waited before the load of the '
              'dump program from a FICON storage volume is aborted. Only used '
              'for CPCs with the storage management feature (z14 and later) '
              'when loading from a FICON storage volume, and ignored '
              'otherwise. Default: 60')
@add_options(ASYNC_TIMEOUT_OPTIONS)
@click.pass_obj
def partition_dump(cmd_ctx, cpc, partition, **options):
    """
    Load and execute a standalone dump program from a volume.

    This command loads a standalone dump program into a partition and begins
    its execution. It does so in a special way that the existing contents of
    the partition's memory are not overwritten so that the dump program can
    dump those contents. The partition must be in one of the states "active",
    "degraded", "paused", or "terminated".

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_partition_dump(
        cmd_ctx, cpc, partition, **options))


@partition_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.option('--name', type=str, required=True,
              help='The name of the new partition.')
@click.option('--description', type=str, required=False,
              help='The description of the new partition.')
@click.option('--cp-processors', type=int, required=False,
              help='The number of general purpose (CP) processors. '
              'Default: No CP processors')
@click.option('--ifl-processors', type=int, required=False,
              help='The number of IFL processors. '
              'Default: {d}, if no CP processors have been specified'.
              format(d=DEFAULT_IFL_PROCESSORS))
@click.option('--processor-mode', type=click.Choice(['dedicated', 'shared']),
              required=False, default=DEFAULT_PROCESSOR_MODE,
              help='The sharing mode for processors. '
              'Default: {d}'.format(d=DEFAULT_PROCESSOR_MODE))
@click.option('--initial-memory', type=int, required=False,
              default=DEFAULT_INITIAL_MEMORY_MB,
              help='The initial amount of memory (in MiB) when the partition '
              'is started. '
              'Default: {d} MiB'.format(d=DEFAULT_INITIAL_MEMORY_MB))
@click.option('--maximum-memory', type=int, required=False,
              default=DEFAULT_MAXIMUM_MEMORY_MB,
              help='The maximum amount of memory (in MiB) while the partition '
              'is running. '
              'Default: {d} MiB'.format(d=DEFAULT_MAXIMUM_MEMORY_MB))
@click.option('--boot-ftp-host', type=str, required=False,
              help='Boot from an FTP server: The hostname or IP address of '
              'the FTP server.')
@click.option('--boot-ftp-username', type=str, required=False,
              help='Boot from an FTP server: The user name on the FTP server.')
@click.option('--boot-ftp-password', type=str, required=False,
              help='Boot from an FTP server: The password on the FTP server.')
@click.option('--boot-ftp-insfile', type=str, required=False,
              help='Boot from an FTP server: The path to the INS-file on the '
              'FTP server.')
@click.option('--boot-media-file', type=str, required=False,
              help='Boot from removable media on the HMC: The path to the '
              'image file on the HMC.')
@click.option('--access-global-performance-data', type=bool, required=False,
              help='Indicates if global performance data authorization '
              'control is requested. Default: False')
@click.option('--permit-cross-partition-commands', type=bool, required=False,
              help='Indicates if cross partition commands authorization is'
              'requested. Default: False')
@click.option('--access-basic-counter-set', type=bool, required=False,
              help='Indicates if basic counter set authorization control is '
              'requested. Default: False')
@click.option('--access-problem-state-counter-set', type=bool, required=False,
              help='Indicates if problem state counter set authorization '
              'is requested. Default: False')
@click.option('--access-crypto-activity-counter-set',
              type=bool, required=False,
              help='Indicates is crypto activity counter set authorization '
              'control is requested. Default: False')
@click.option('--access-extended-counter-set', type=bool, required=False,
              help='Indicates if extended counter set authorization control '
              'is requested. Default: False')
@click.option('--access-coprocessor-group-set', type=bool, required=False,
              help='Indicates if coprocessor group set authorization control '
              'is requested. Default: False')
@click.option('--access-basic-sampling', type=bool, required=False,
              help='Indicates if basic CPU sampling authorization control is '
              'requested. Default: False')
@click.option('--access-diagnostic-sampling', type=bool, required=False,
              help='Indicates if diagnostic sampling authorization control '
              'is requested. Default: False')
@click.option('--type', type=click.Choice(PARTITION_TYPES), required=False,
              help='Defines the type of the partition. Default: {pd}'.
              format(pd=DEFAULT_PARTITION_TYPE))
@click.option('--ssc-host-name', type=str, required=False,
              help='Secure Service Container host name. '
              'Only applicable to and required for ssc type partitions.')
@click.option('--ssc-ipv4-gateway', type=str, required=False,
              help='Default IPv4 Gateway to be used. '
              'Empty string sets no IPv4 Gateway. '
              'Only applicable to ssc type partitions. '
              'Default: No IPv4 Gateway')
@click.option('--ssc-dns-servers', type=str, required=False,
              help='DNS IP addresses (comma-separated). '
              'Empty string sets no DNS IP addresses. '
              'Only applicable to ssc type partitions. '
              'Default: No DNS IP addresses')
@click.option('--ssc-master-userid', type=str, required=False,
              help='Secure Service Container master user ID. '
              'Only applicable to and required for ssc type partitions.')
@click.option('--ssc-master-pw', type=str, required=False,
              help='Secure Service Container master user password. '
              'Only applicable to and required for ssc type partitions.')
@click.option('--initial-cp-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT),
              required=False, default=DEFAULT_PROCESSING_WEIGHT,
              help='Defines the initial processing weight of CP processors. '
              'Default: {d}'.format(d=DEFAULT_PROCESSING_WEIGHT))
@click.option('--initial-ifl-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT),
              required=False, default=DEFAULT_PROCESSING_WEIGHT,
              help='Defines the initial processing weight of IFL processors. '
              'Default: {d}'.format(d=DEFAULT_PROCESSING_WEIGHT))
@click.option('--minimum-ifl-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT),
              required=False, default=MIN_PROCESSING_WEIGHT,
              help='Represents the minimum amount of IFL processor '
              'resources allocated to the partition. '
              'Default: {d}'.format(d=MIN_PROCESSING_WEIGHT))
@click.option('--minimum-cp-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT),
              required=False, default=MIN_PROCESSING_WEIGHT,
              help='Represents the minimum amount of general purpose '
              'processor resources allocated to the partition. '
              'Default: {d}'.format(d=MIN_PROCESSING_WEIGHT))
@click.option('--maximum-ifl-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT),
              required=False, default=MAX_PROCESSING_WEIGHT,
              help='Represents the maximum amount of IFL processor '
              'resources allocated to the partition. '
              'Default: {d}'.format(d=MAX_PROCESSING_WEIGHT))
@click.option('--maximum-cp-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT),
              required=False, default=MAX_PROCESSING_WEIGHT,
              help='Represents the maximum amount of general purpose '
              'processor resources allocated to the partition. '
              'Default: {d}'.format(d=MAX_PROCESSING_WEIGHT))
@click.pass_obj
def partition_create(cmd_ctx, cpc, **options):
    """
    Create a partition in a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_partition_create(cmd_ctx, cpc, options))


@partition_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.option('--name', type=str, required=False,
              help='The new name of the partition.')
@click.option('--description', type=str, required=False,
              help='The new description of the partition.')
@click.option('--cp-processors', type=int, required=False,
              help='The new number of general purpose (CP) processors.')
@click.option('--ifl-processors', type=int, required=False,
              help='The new number of IFL processors.')
@click.option('--processor-mode', type=click.Choice(['dedicated', 'shared']),
              required=False,
              help='The new sharing mode for processors.')
@click.option('--initial-memory', type=int, required=False,
              help='The new initial amount of memory (in MiB) when the '
              'partition is started.')
@click.option('--maximum-memory', type=int, required=False,
              help='The new maximum amount of memory (in MiB) while the '
              'partition is running.')
@click.option('--boot-storage-volume', type=str, required=False,
              help='Boot from a storage volume. '
              'For CPCs with the storage management feature (z14 and later): '
              'A string of the form "SG/SV" where SG is the name of the '
              'storage group attached to the partition and SV is the name of '
              'the storage volume in that storage group, or of the form '
              '"UUID" where UUID is the UUID of the storage volume on the '
              'storage array (also shown in the HMC GUI). The storage '
              'volume may be of type FCP or FICON. '
              'For CPCs without the storage management feature (z13 and '
              'earlier): A string of the form "HBA/WWPN/LUN", where HBA is the '
              'name of the HBA to be used and WWPN and LUN identify the '
              'storage array and storage volume thereon. The storage volume '
              'must be of type FCP.')
@click.option('--boot-storage-hba', type=str, required=False,
              help='Boot from an FCP storage volume: The name of the HBA to be '
              'used. '
              'Deprecated, use --boot-storage-volume instead.')
@click.option('--boot-storage-lun', type=str, required=False,
              help='Boot from an FCP storage volume: The LUN of the storage '
              'volume on the storage array. '
              'Deprecated, use --boot-storage-volume instead.')
@click.option('--boot-storage-wwpn', type=str, required=False,
              help='Boot from an FCP storage volume: The WWPN of the storage '
              'array that has the storage volume. '
              'Deprecated, use --boot-storage-volume instead.')
@click.option('--boot-network-nic', type=str, required=False,
              help='Boot from a PXE server: The name of the NIC to be used.')
@click.option('--boot-ftp-host', type=str, required=False,
              help='Boot from an FTP server: The hostname or IP address of '
              'the FTP server.')
@click.option('--boot-ftp-username', type=str, required=False,
              help='Boot from an FTP server: The user name on the FTP server.')
@click.option('--boot-ftp-password', type=str, required=False,
              help='Boot from an FTP server: The password on the FTP server.')
@click.option('--boot-ftp-insfile', type=str, required=False,
              help='Boot from an FTP server: The path to the INS-file on the '
              'FTP server.')
@click.option('--boot-media-file', type=str, required=False,
              help='Boot from removable media on the HMC: The path to the '
              'image file on the HMC.')
@click.option('--boot-iso', type=str, required=False,
              help='Boot from an ISO image mounted to this partition.')
@click.option('--secure-boot', type=bool, required=False,
              help='Check the software signature of what is booted against '
              'what the distributor signed it with. '
              'Requires z15 or later (recommended bundle levels on z15 are '
              'at least H28 and S38), requires the boot volume to be prepared '
              'for secure boot '
              '(see https://linux.mainframe.blog/secure-boot/), requires the '
              'partition to have type "linux" and boot-device "storage-volume" '
              'with volume type "fcp" or "nvme". Default: False')
@click.option('--access-global-performance-data', type=bool, required=False,
              help='Indicates if global performance data authorization '
              'control is requested. Default: False')
@click.option('--permit-cross-partition-commands', type=bool, required=False,
              help='Indicates if cross partition commands authorization is'
              'requested. Default: False')
@click.option('--access-basic-counter-set', type=bool, required=False,
              help='Indicates if basic counter set authorization control is '
              'requested. Default: False')
@click.option('--access-problem-state-counter-set', type=bool, required=False,
              help='Indicates if problem state counter set authorization '
              'is requested. Default: False')
@click.option('--access-crypto-activity-counter-set',
              type=bool, required=False,
              help='Indicates is crypto activity counter set authorization '
              'control is requested. Default: False')
@click.option('--access-extended-counter-set', type=bool, required=False,
              help='Indicates if extended counter set authorization control '
              'is requested. Default: False')
@click.option('--access-coprocessor-group-set', type=bool, required=False,
              help='Indicates if coprocessor group set authorization control '
              'is requested. Default: False')
@click.option('--access-basic-sampling', type=bool, required=False,
              help='Indicates if basic CPU sampling authorization control is '
              'requested. Default: False')
@click.option('--access-diagnostic-sampling', type=bool, required=False,
              help='Indicates if diagnostic sampling authorization control '
              'is requested. Default: False')
@click.option('--ssc-host-name', type=str, required=False,
              help='Secure Service Container host name.')
@click.option('--ssc-boot-selection',
              type=click.Choice(['installer']), required=False,
              help='Set the boot mode of the Secure Service Container '
              'to run the SSC Appliance Installer again upon next '
              'partition start. Only applicable to ssc type partitions.')
@click.option('--ssc-ipv4-gateway', type=str, required=False,
              help='Default IPv4 Gateway to be used. '
              'Empty string sets no IPv4 Gateway. '
              'Only applicable to ssc type partitions.')
@click.option('--ssc-dns-servers', type=str, required=False,
              help='DNS IP addresses (comma-separated). '
              'Empty string sets no DNS IP addresses. '
              'Only applicable to ssc type partitions.')
@click.option('--ssc-master-userid', type=str, required=False,
              help='Secure Service Container master user ID. '
              'Only applicable to ssc type partitions.')
@click.option('--ssc-master-pw', type=str, required=False,
              help='Secure Service Container master user password. '
              'Only applicable to ssc type partitions.')
@click.option('--initial-cp-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT), required=False,
              help='Defines the initial processing weight of CP processors.')
@click.option('--initial-ifl-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT), required=False,
              help='Defines the initial processing weight of IFL processors.')
@click.option('--minimum-ifl-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT), required=False,
              help='Represents the minimum amount of IFL processor '
              'resources allocated to the partition.')
@click.option('--minimum-cp-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT), required=False,
              help='Represents the minimum amount of general purpose '
              'processor resources allocated to the partition.')
@click.option('--maximum-ifl-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT), required=False,
              help='Represents the maximum amount of IFL processor '
              'resources allocated to the partition.')
@click.option('--maximum-cp-processing-weight',
              type=click.IntRange(MIN_PROCESSING_WEIGHT,
                                  MAX_PROCESSING_WEIGHT), required=False,
              help='Represents the maximum amount of general purpose '
              'processor resources allocated to the partition.')
@click.pass_obj
def partition_update(cmd_ctx, cpc, partition, **options):
    """
    Update the properties of a partition.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_partition_update(cmd_ctx, cpc, partition,
                                                     options))


@partition_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the partition.',
              prompt='Are you sure you want to delete this partition ?')
@click.pass_obj
def partition_delete(cmd_ctx, cpc, partition):
    """
    Delete a partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_partition_delete(cmd_ctx, cpc, partition))


@partition_group.command('console', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.option('--refresh', is_flag=True, required=False,
              help='Include refresh messages.')
@click.pass_obj
def partition_console(cmd_ctx, cpc, partition, **options):
    """
    Establish an interactive session with the console of the operating system
    running in a partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_partition_console(cmd_ctx, cpc, partition,
                                                      options))


@partition_group.command('mountiso', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.option('--imagefile', type=str, required=True,
              help='The file path of the ISO image file.')
@click.option('--imageinsfile', type=str, required=True,
              help='The file path of the INS file (within the file system '
              'of the ISO image file).')
@click.option('--boot', '-b', is_flag=True, required=False,
              help='Set boot-device property to iso-image.')
@click.pass_obj
def partition_mount_iso(cmd_ctx, cpc, partition, **options):
    """
    Mount an ISO image to a partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_partition_mount_iso(cmd_ctx, cpc,
                                                        partition, options))


@partition_group.command('unmountiso', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.pass_obj
def partition_unmount_iso(cmd_ctx, cpc, partition):
    """
    Unmount an ISO image from a partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_partition_unmount_iso(cmd_ctx, cpc,
                                                          partition))


@partition_group.command('list-storagegroups',
                         options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.pass_obj
def partition_list_storagegroups(cmd_ctx, cpc, partition):
    """
    List the storage groups attached to a partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_partition_list_storagegroups(cmd_ctx, cpc, partition))


@partition_group.command('attach-storagegroup',
                         options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.option('--storagegroup', type=str, required=True,
              help='The name of the storage group.')
@click.pass_obj
def partition_attach_storagegroup(cmd_ctx, cpc, partition, **options):
    """
    Attach a storage group to a partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_partition_attach_storagegroup(cmd_ctx, cpc, partition,
                                                  options))


@partition_group.command('detach-storagegroup',
                         options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION', type=str, metavar='PARTITION')
@click.option('--storagegroup', type=str, required=True,
              help='The name of the storage group.')
@click.pass_obj
def partition_detach_storagegroup(cmd_ctx, cpc, partition, **options):
    """
    Detach a storage group from a partition.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_partition_detach_storagegroup(cmd_ctx, cpc, partition,
                                                  options))


def cmd_partition_list(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    if options['help_usage']:
        help_lines = """
Help for usage related options of the partition list command:

--memory-usage option:

  - 'initial-memory' field: Memory allocated to the partition, in MiB.

--ifl-usage option:

  - 'processor-mode' field: 'shared' or 'dedicated' depending on the processor
    sharing mode for the partition. This applies to all types of processors
    (IFLs and CPs).

  - 'ifls' field: Number of IFLs assigned to the partition. For dedicated
    processor mode, each of these has the capacity of a physical processors.
    For shared processor mode, these are shared processors each of which gets
    a subset of the capacity of a physical processor.
    This is the value of the 'ifl-processors' property of the partition.

  - 'ifl-weight' field: IFL weight of the partition. This is a relative number
    that is put in proportion to the IFL weights of other partitions.
    Note that the IFL weight is applied at the partition level, not at the
    IFL level.
    This is the value of the 'initial-ifl-processing-weight' property of the
    partition.

  - 'ifl-capacity' field: IFL capacity assigned to the partition, in
    units of physical IFLs.
    The assigned IFL capacity takes into account the IFL weight of the
    partition relative to the IFL weights of all other partitions that are
    active and in shared processor mode.
    This is a calculated value.

  - 'processor-usage' field: The percentage of the processor (IFL and CP)
    capacity of the partition that is actually used (=consumed).
    This is the value of the 'processor-usage' metric of the partition.

  - 'processors-used' field: Processor (IFL and CP) capacity currently consumed
    by the partition, in units of physical processors.
    This is a calculated value.

--cp-usage option: Same as --ifl-usage option, just with CPs instead of IFLs.
"""

        cmd_ctx.spinner.stop()
        click.echo(help_lines)
        return

    client = zhmcclient.Client(cmd_ctx.session)

    if client.version_info() >= (2, 20):  # Starting with HMC 2.14.0
        # This approach is faster than going through the CPC.
        # In addition, this approach supports users that do not have object
        # access permission to the parent CPC of the LPAR.
        filter_args = {}
        if cpc_name:
            filter_args['cpc-name'] = cpc_name
        partitions = client.consoles.console.list_permitted_partitions(
            filter_args=filter_args)
    else:
        filter_args = {}
        if cpc_name:
            filter_args['name'] = cpc_name
        try:
            cpcs = client.cpcs.list(filter_args=filter_args)
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)
        partitions = []
        for cpc in cpcs:
            try:
                partitions.extend(cpc.partitions.list())
            except zhmcclient.Error as exc:
                raise click_exception(exc, cmd_ctx.error_format)

    if options['type']:
        click.echo("The --type option is deprecated and type information "
                   "is now always shown.")

    # Prepare the additions dict of dicts. It contains additional
    # (=non-resource) property values by property name and by resource URI.
    # Depending on options, some of them will not be populated.
    additions = {}
    additions['ifl-capacity'] = {}
    additions['ifls'] = {}
    additions['ifl-weight'] = {}
    additions['cp-capacity'] = {}
    additions['cps'] = {}
    additions['cp-weight'] = {}
    additions['processor-usage'] = {}
    additions['processors-used'] = {}
    additions['cpc'] = {}

    show_list = [
        'name',
        'cpc',
    ]
    if not options['names_only']:
        show_list.extend([
            'status',
            'type',
            'os-name',
            'os-type',
            'os-version',
        ])
    if options['uri']:
        show_list.extend([
            'object-uri',
        ])

    if options['memory_usage']:
        show_list.extend([
            'initial-memory',
        ])

    if options['ifl_usage'] or options['cp_usage']:

        for p in partitions:
            p.pull_full_properties()

        # Calculate effective IFLs and add it
        total_ifls = {}  # by CPC name
        total_ifl_weight = {}  # by CPC name
        for p in partitions:
            cpc = p.manager.parent
            if p.properties['processor-mode'] == 'shared' and \
                    p.properties['status'] == 'active':
                if cpc.name not in total_ifl_weight:
                    total_ifl_weight[cpc.name] = 0
                    total_ifls[cpc.name] = cpc.prop('processor-count-ifl')
                total_ifl_weight[cpc.name] += \
                    p.properties['initial-ifl-processing-weight']
        for p in partitions:
            cpc = p.manager.parent
            if p.properties['status'] != 'active':
                ifls_eff = None
            elif p.properties['processor-mode'] == 'shared':
                ifl_weight = p.properties['initial-ifl-processing-weight']
                ifls_eff = float(total_ifls[cpc.name]) * ifl_weight / \
                    total_ifl_weight[cpc.name]
            else:
                ifls_eff = float(p.properties['ifl-processors'])
            additions['ifl-capacity'][p.uri] = ifls_eff
            additions['ifls'][p.uri] = p.properties['ifl-processors']
            additions['ifl-weight'][p.uri] = \
                p.properties['initial-ifl-processing-weight']

        # Calculate effective CPs and add it
        total_cps = {}  # by CPC name
        total_cp_weight = {}  # by CPC name
        for p in partitions:
            cpc = p.manager.parent
            if p.properties['processor-mode'] == 'shared' and \
                    p.properties['status'] == 'active':
                if cpc.name not in total_cp_weight:
                    total_cp_weight[cpc.name] = 0
                    total_cps[cpc.name] = \
                        cpc.prop('processor-count-general-purpose')
                total_cp_weight[cpc.name] += \
                    p.properties['initial-cp-processing-weight']
        for p in partitions:
            cpc = p.manager.parent
            if p.properties['status'] != 'active':
                cps_eff = None
            elif p.properties['processor-mode'] == 'shared':
                cp_weight = p.properties['initial-cp-processing-weight']
                cps_eff = float(total_cps[cpc.name]) * cp_weight / \
                    total_cp_weight[cpc.name]
            else:
                cps_eff = float(p.properties['cp-processors'])
            additions['cp-capacity'][p.uri] = cps_eff
            additions['cps'][p.uri] = p.properties['cp-processors']
            additions['cp-weight'][p.uri] = \
                p.properties['initial-cp-processing-weight']

        # Get processor-usage metrics and add it
        metric_group = 'partition-usage'
        resource_filter = []
        if cpc_name:
            resource_filter.append(('cpc', cpc_name))
        mov_list, _ = get_metric_values(
            client, metric_group, resource_filter)
        partition_metrics = {}
        for mov in mov_list:
            assert isinstance(mov.resource, zhmcclient.Partition)
            p_name = mov.resource.name
            partition_metrics[p_name] = mov.metrics
        for p in partitions:
            # Note: Partitions that are stopped have no metrics value for
            # partition-usage.
            p_metrics = partition_metrics.get(p.name, None)
            if p_metrics:
                usage = p_metrics['processor-usage']
                # Independent of sharing mode:
                procs_eff = (additions['ifl-capacity'][p.uri] or 0) + \
                    (additions['cp-capacity'][p.uri] or 0)
                used = float(usage) / 100 * procs_eff
            else:
                usage = None
                used = None
            additions['processor-usage'][p.uri] = usage
            additions['processors-used'][p.uri] = used

        show_list.append('processor-mode')

        if options['ifl_usage']:
            show_list.append('ifls')
            show_list.append('ifl-weight')
            show_list.append('ifl-capacity')

        if options['cp_usage']:
            show_list.append('cps')
            show_list.append('cp-weight')
            show_list.append('cp-capacity')

        show_list.append('processor-usage')
        show_list.append('processors-used')

    for p in partitions:
        cpc = p.manager.parent
        additions['cpc'][p.uri] = cpc.name

    try:
        print_resources(cmd_ctx, partitions, cmd_ctx.output_format, show_list,
                        additions, all=options['all'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_partition_show(cmd_ctx, cpc_name, partition_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    try:
        partition.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(partition.properties)

    # Hide some long or deeply nested properties in table output formats.
    if not options['all'] and cmd_ctx.output_format in TABLE_FORMATS:
        hide_property(properties, 'crypto-configuration')

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def cmd_partition_start(cmd_ctx, cpc_name, partition_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    try:
        partition.start(wait_for_completion=True,
                        operation_timeout=options['operation_timeout'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Partition '{p}' has been started.".format(p=partition_name))


def cmd_partition_stop(cmd_ctx, cpc_name, partition_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    try:
        partition.stop(wait_for_completion=True,
                       operation_timeout=options['operation_timeout'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Partition '{p}' has been stopped.".format(p=partition_name))


def cmd_partition_create(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    # The following options are handled specifically in this function (as
    # opposed to be handled generically in options_to_properties()):

    # The options for booting from an FTP server.
    # They need to be specified together, all of them are required.
    boot_ftp_option_names = (
        'boot-ftp-host',
        'boot-ftp-username',
        'boot-ftp-password',
        'boot-ftp-insfile',
    )

    # The option for booting from an HMC media file.
    # For consistency, a list is used even though it is a single option.
    boot_media_option_names = (
        'boot-media-file',
    )

    # Options handled in this function
    special_opt_names = boot_ftp_option_names + boot_media_option_names
    name_map = dict((opt, None) for opt in special_opt_names)

    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    # Used and missing options handled in this function
    used_boot_ftp_opts = [
        '--' + name for name in boot_ftp_option_names
        if org_options[name] is not None]
    missing_boot_ftp_opts = [
        '--' + name for name in boot_ftp_option_names
        if org_options[name] is None]

    used_boot_media_opts = [
        '--' + name for name in boot_media_option_names
        if org_options[name] is not None]

    used_boot_opts = used_boot_ftp_opts + used_boot_media_opts
    num_boot_devices = bool(used_boot_ftp_opts) + bool(used_boot_media_opts)
    if num_boot_devices > 1:
        raise click_exception(
            "Boot from multiple devices specified: {opts}".
            format(opts=', '.join(used_boot_opts)),
            cmd_ctx.error_format)

    if used_boot_ftp_opts:
        if missing_boot_ftp_opts:
            raise click_exception(
                "Boot from FTP server specified, but misses the following "
                "options: {opts}".
                format(opts=', '.join(missing_boot_ftp_opts)),
                cmd_ctx.error_format)
        properties['boot-device'] = 'ftp'
        properties['boot-ftp-host'] = org_options['boot-ftp-host']
        properties['boot-ftp-username'] = org_options['boot-ftp-username']
        properties['boot-ftp-password'] = org_options['boot-ftp-password']
        properties['boot-ftp-insfile'] = org_options['boot-ftp-insfile']

    elif used_boot_media_opts:
        properties['boot-device'] = 'removable-media'
        properties['boot-removable-media'] = org_options['boot-media-file']

    else:
        # boot-device="none" is the default
        pass

    # Default for the number of processors
    if 'ifl-processors' not in properties and \
            'cp-processors' not in properties:
        properties['ifl-processors'] = DEFAULT_IFL_PROCESSORS

    if org_options['ssc-dns-servers'] == '':
        properties['ssc-dns-servers'] = []
    elif org_options['ssc-dns-servers'] is not None:
        properties['ssc-dns-servers'] = \
            org_options['ssc-dns-servers'].split(',')

    if org_options['ssc-ipv4-gateway'] == '':
        properties['ssc-ipv4-gateway'] = None

    try:
        new_partition = cpc.partitions.create(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("New partition '{p}' has been created.".
               format(p=new_partition.properties['name']))


def cmd_partition_update(cmd_ctx, cpc_name, partition_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    # The following options are handled specifically in this function (as
    # opposed to be handled generically in options_to_properties()):

    # The option for booting from a storage volume.
    # For consistency, a list is used even though it is a single option.
    boot_storage_option_names = (
        'boot-storage-volume',
    )

    # The deprecated options for booting from an FCP storage volume.
    # They need to be specified together, all of them are required.
    old_boot_storage_option_names = (
        'boot-storage-hba',
        'boot-storage-lun',
        'boot-storage-wwpn',
    )

    # The option for booting from a PXE server.
    # For consistency, a list is used even though it is a single option.
    boot_network_option_names = (
        'boot-network-nic',
    )

    # The options for booting from an FTP server.
    # They need to be specified together, all of them are required.
    boot_ftp_option_names = (
        'boot-ftp-host',
        'boot-ftp-username',
        'boot-ftp-password',
        'boot-ftp-insfile',
    )

    # The option for booting from an HMC media file.
    # For consistency, a list is used even though it is a single option.
    boot_media_option_names = (
        'boot-media-file',
    )

    # The option for booting from an HMC ISO image.
    # For consistency, a list is used even though it is a single option.
    boot_iso_option_names = (
        'boot-iso',
    )

    # Options handled in this function
    special_opt_names = \
        boot_storage_option_names + old_boot_storage_option_names + \
        boot_network_option_names + boot_ftp_option_names + \
        boot_media_option_names + boot_iso_option_names
    name_map = dict((opt, None) for opt in special_opt_names)

    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    # Used and missing options handled in this function
    used_boot_storage_opts = [
        '--' + name for name in boot_storage_option_names
        if org_options[name] is not None]

    used_old_boot_storage_opts = [
        '--' + name for name in old_boot_storage_option_names
        if org_options[name] is not None]
    missing_old_boot_storage_opts = [
        '--' + name for name in old_boot_storage_option_names
        if org_options[name] is None]

    used_boot_network_opts = [
        '--' + name for name in boot_network_option_names
        if org_options[name] is not None]

    used_boot_ftp_opts = [
        '--' + name for name in boot_ftp_option_names
        if org_options[name] is not None]
    missing_boot_ftp_opts = [
        '--' + name for name in boot_ftp_option_names
        if org_options[name] is None]

    used_boot_media_opts = [
        '--' + name for name in boot_media_option_names
        if org_options[name] is not None]

    used_boot_iso_opts = [
        '--' + name for name in boot_iso_option_names
        if org_options[name] is not None]

    if used_boot_storage_opts and used_old_boot_storage_opts:
        raise click_exception(
            "Boot from storage volume specified using both "
            "--boot-storage-volume and the deprecated options "
            "--boot-storage-hba/lun/wwpn",
            cmd_ctx.error_format)

    used_boot_opts = \
        used_boot_storage_opts + used_old_boot_storage_opts + \
        used_boot_network_opts + used_boot_ftp_opts + \
        used_boot_media_opts + used_boot_iso_opts
    num_boot_devices = \
        bool(used_boot_storage_opts + used_old_boot_storage_opts) + \
        bool(used_boot_network_opts) + bool(used_boot_ftp_opts) + \
        bool(used_boot_media_opts) + bool(used_boot_iso_opts)
    if num_boot_devices > 1:
        raise click_exception(
            "Boot from multiple devices specified: {opts}".
            format(opts=', '.join(used_boot_opts)),
            cmd_ctx.error_format)

    if used_boot_storage_opts:
        sv_name = org_options['boot-storage-volume']
        if storage_management_feature(partition):
            storage_volume = parse_volume_with_sm(
                sv_name, partition, "--boot-storage-volume option",
                cmd_ctx.error_format)
            properties['boot-device'] = 'storage-volume'
            properties['boot-storage-volume'] = storage_volume.uri
        else:
            hba, wwpn, lun = parse_volume_without_sm(
                sv_name, partition, "--boot-storage-volume option",
                cmd_ctx.error_format)
            properties['boot-device'] = 'storage-adapter'
            properties['boot-storage-device'] = hba.uri
            properties['boot-world-wide-port-name'] = wwpn
            properties['boot-logical-unit-number'] = lun

    elif used_old_boot_storage_opts:
        if storage_management_feature(partition):
            raise click_exception(
                "The deprecated options --boot-storage-hba/lun/wwpn can be "
                "used only with CPCs without the storage management feature "
                "(z13 and earlier)",
                cmd_ctx.error_format)
        if missing_old_boot_storage_opts:
            raise click_exception(
                "Boot from storage volume specified using the deprecated "
                "options --boot-storage-hba/lun/wwpn, but misses the "
                "following options: {opts}".
                format(opts=', '.join(missing_old_boot_storage_opts)),
                cmd_ctx.error_format)
        click.echo("Deprecated: The options --boot-storage-hba/lun/wwpn are "
                   "deprecated. Use the --boot-storage-volume option instead")
        properties['boot-device'] = 'storage-adapter'
        properties['boot-storage-device'] = hba.uri
        properties['boot-world-wide-port-name'] = \
            org_options['boot-storage-wwpn']
        properties['boot-logical-unit-number'] = \
            org_options['boot-storage-lun']

    elif used_boot_network_opts:
        nic_name = org_options['boot-network-nic']
        try:
            nic = partition.nics.find(name=nic_name)
        except zhmcclient.NotFound:
            raise click_exception("Could not find NIC '{n}' in partition '{p}' "
                                  "in CPC '{c}'.".
                                  format(n=nic_name, p=partition_name,
                                         c=cpc_name),
                                  cmd_ctx.error_format)
        properties['boot-device'] = 'network-adapter'
        properties['boot-network-device'] = nic.uri

    elif used_boot_ftp_opts:
        if missing_boot_ftp_opts:
            raise click_exception("Boot from FTP server specified, but misses "
                                  "the following options: {o}".
                                  format(o=', '.join(missing_boot_ftp_opts)),
                                  cmd_ctx.error_format)
        properties['boot-device'] = 'ftp'
        properties['boot-ftp-host'] = org_options['boot-ftp-host']
        properties['boot-ftp-username'] = org_options['boot-ftp-username']
        properties['boot-ftp-password'] = org_options['boot-ftp-password']
        properties['boot-ftp-insfile'] = org_options['boot-ftp-insfile']

    elif used_boot_media_opts:
        properties['boot-device'] = 'removable-media'
        properties['boot-removable-media'] = org_options['boot-media-file']

    elif used_boot_iso_opts:
        properties['boot-device'] = 'iso-image'

    else:
        # boot-device="none" is the default
        pass

    if org_options['ssc-dns-servers'] == '':
        properties['ssc-dns-servers'] = []
    elif org_options['ssc-dns-servers'] is not None:
        properties['ssc-dns-servers'] = \
            org_options['ssc-dns-servers'].split(',')

    if org_options['ssc-ipv4-gateway'] == '':
        properties['ssc-ipv4-gateway'] = None

    if org_options['secure-boot']:
        properties['secure-boot'] = True

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating partition '{p}'.".
                   format(p=partition_name))
        return

    try:
        partition.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    if 'name' in properties and properties['name'] != partition_name:
        click.echo("Partition '{p}' has been renamed to '{pn}' and was "
                   "updated.".
                   format(p=partition_name, pn=properties['name']))
    else:
        click.echo("Partition '{p}' has been updated.".format(p=partition_name))


def cmd_partition_delete(cmd_ctx, cpc_name, partition_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    try:
        partition.delete()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Partition '{p}' has been deleted.".format(p=partition_name))


def cmd_partition_console(cmd_ctx, cpc_name, partition_name, options):
    # pylint: disable=missing-function-docstring

    logger = logging.getLogger(CONSOLE_LOGGER_NAME)

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    refresh = options['refresh']

    cmd_ctx.spinner.stop()

    try:
        part_console(cmd_ctx.session, partition, refresh, logger)
    except zhmcclient.Error as exc:
        raise click.ClickException(
            "{exc}: {msg}".format(exc=exc.__class__.__name__, msg=exc))


def cmd_partition_dump(cmd_ctx, cpc_name, partition_name, **options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    if storage_management_feature(partition):
        partition_dump_with_sm(cmd_ctx, partition, **options)
    else:
        partition_dump_without_sm(cmd_ctx, partition, **options)

    cmd_ctx.spinner.stop()
    click.echo('Dump of Partition %s is complete.' % partition.name)


def partition_dump_with_sm(cmd_ctx, partition, **options):
    """Dump partition on CPCs that have the storage mgmt feature enabled"""

    # Maps zhmc command options to fields of the dump-program-info parameter
    # within the Start Dump Program parameters
    dpi_name_map = {
        'configuration': 'dump-configuration-selector',
        'parameters': 'dump-os-specific-parameters',
        'lba': 'dump-record-lba',
        'volume': None,  # Handled in this function
        'timeout': None,  # Handled in this function
    }
    org_options = original_options(options)
    dpi_parms = options_to_properties(org_options, dpi_name_map)
    volume_opt = options['volume']  # It is required
    timeout = options['timeout']  # It is optional but has a default

    storage_volume = parse_volume_with_sm(
        volume_opt, partition, "--volume option", cmd_ctx.error_format)

    # Set the remaining dump-program-info parameters
    dpi_parms['storage-volume-uri'] = storage_volume.uri
    if storage_volume.manager.parent.prop('type') == 'fc':
        # HMC rejects timeout on non-FICON volumes with 400,14.
        dpi_parms['timeout'] = timeout

    parameters = {
        'dump-program-info': dpi_parms,
        'dump-program-type': 'storage',
    }
    try:
        partition.start_dump_program(
            parameters=parameters, wait_for_completion=True,
            operation_timeout=options['operation_timeout'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def partition_dump_without_sm(cmd_ctx, partition, **options):
    """Dump partition on CPCs that have the storage mgmt feature disabled"""

    # Maps zhmc command options to Dump Partition parameters
    name_map = {
        'configuration': 'dump-configuration-selector',
        'parameters': 'dump-os-specific-parameters',
        'lba': 'dump-record-lba',
        'volume': None,  # Handled in this function
        'timeout': None,  # Ignored
    }
    org_options = original_options(options)
    parameters = options_to_properties(org_options, name_map)
    volume_opt = options['volume']  # It is required

    hba, wwpn, lun = parse_volume_without_sm(
        volume_opt, partition, "--volume option", cmd_ctx.error_format)

    # Set the remaining Dump Partition parameters
    parameters['dump-load-hba-uri'] = hba.uri
    parameters['dump-world-wide-port-name'] = wwpn
    parameters['dump-logical-unit-number'] = lun

    try:
        partition.dump_partition(
            parameters=parameters, wait_for_completion=True,
            operation_timeout=options['operation_timeout'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_partition_mount_iso(cmd_ctx, cpc_name, partition_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    image_file = options['imagefile']
    _, image_name = os.path.split(image_file)
    with io.open(image_file, 'rb') as image_fp:
        partition.mount_iso_image(image_fp, image_name, options['imageinsfile'])
    if options['boot']:
        partition.update_properties({'boot-device': 'iso-image'})
    cmd_ctx.spinner.stop()
    click.echo("ISO image {i} has been mounted to partition '{p}'.".
               format(i=image_name, p=partition.name))


def cmd_partition_unmount_iso(cmd_ctx, cpc_name, partition_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    partition.pull_full_properties()
    image_name = partition.get_property('boot-iso-image-name')
    if image_name:
        boot_device = partition.get_property('boot-device')
        if boot_device == 'iso-image':
            partition.update_properties({'boot-device': 'none'})
        partition.unmount_iso_image()
        cmd_ctx.spinner.stop()
        click.echo("ISO image {i} has been unmounted from partition '{p}'.".
                   format(i=image_name, p=partition.name))
    else:
        cmd_ctx.spinner.stop()
        click.echo("No ISO image is mounted to partition '{p}'.".
                   format(p=partition.name))


def cmd_partition_list_storagegroups(cmd_ctx, cpc_name, partition_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    try:
        stogrps = partition.list_attached_storage_groups()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    show_list = [
        'name',
        'type',
        'shared',
        'fulfillment-state',
    ]

    try:
        print_resources(cmd_ctx, stogrps, cmd_ctx.output_format, show_list)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_partition_attach_storagegroup(
        cmd_ctx, cpc_name, partition_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    stogrp_name = options['storagegroup']
    stogrp = find_storagegroup(cmd_ctx, client, stogrp_name)

    try:
        partition.attach_storage_group(stogrp)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Storage group '{sg}' was attached to partition '{p}'.".
               format(sg=stogrp_name, p=partition.name))


def cmd_partition_detach_storagegroup(
        cmd_ctx, cpc_name, partition_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    partition = find_partition(cmd_ctx, client, cpc_name, partition_name)

    stogrp_name = options['storagegroup']
    stogrp = find_storagegroup(cmd_ctx, client, stogrp_name)

    try:
        partition.detach_storage_group(stogrp)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Storage group '{sg}' was detached from partition '{p}'.".
               format(sg=stogrp_name, p=partition.name))


# pylint: disable=inconsistent-return-statements
def parse_volume_with_sm(volume_specifier, partition, where, error_format):
    """
    Parse a volume specifier for a CPC with the storage management feature
    (i.e. z14 or later) and return its StorageVolume resource object.

    The partition that has the storage group of the volume attached, must be
    known.

    Parameters:

      volume_specifier (string): The volume specifier, in one of these forms:

        * "SG/SV", where SG is the name of the storage group resource
          attached to the partition and SV is the name of the storage volume
          in that storage group.

        * "UUID", where UUID is the UUID of the storage volume on the storage
          array (also shown in the HMC GUI).

      partition (Partition): The partition that has the storage group attached
        that contains the specified volume.

      cpc_name (string): Name of the CPC containinng the partition (only used
        for messages).

      where (string): Text stating where the volue has been specified, e.g.
        "--volume option" (only used for messages).

      error_format (string):
        The error format (see ``--error-format`` general option, only used for
        messages).

    Returns:

      zhmcclient.StorageVolume: The storage volume resource (of type FCP or
      FICON.)
    """
    cpc_name = partition.manager.parent.name
    volume_parts = volume_specifier.split('/')

    if len(volume_parts) == 1:  # format: UUID
        uuid = volume_parts[0]
        sg_list = partition.list_attached_storage_groups()
        storage_volume = None
        for sg in sg_list:
            try:
                storage_volume = sg.storage_volumes.find(uuid=uuid)
                break
            except zhmcclient.NotFound:
                continue
        if not storage_volume:
            raise click_exception(
                "Storage volume with UUID '{uuid}' specified in "
                "{where} was not found in any storage group attached "
                "to partition '{part}' of CPC '{cpc}'.".
                format(uuid=uuid, where=where, part=partition.name,
                       cpc=cpc_name),
                error_format)
        return storage_volume

    if len(volume_parts) == 2:  # format: SG/SV
        sg_name, sv_name = volume_parts
        sg_list = partition.list_attached_storage_groups()
        sg = None
        for _sg in sg_list:
            if _sg.name == sg_name:
                sg = _sg
                break
        if not sg:
            raise click_exception(
                "Storage group '{sg}' specified in {where} was not "
                "found in the storage groups attached to partition '{part}' "
                "of CPC '{cpc}'.".
                format(sg=sg_name, where=where, part=partition.name,
                       cpc=cpc_name),
                error_format)
        try:
            storage_volume = sg.storage_volumes.find(name=sv_name)
        except zhmcclient.NotFound:
            raise click_exception(
                "Storage volume '{sv}' specified in {where} was not "
                "found in the volumes of storage group '{sg}' attached to "
                "partition '{part}' of CPC '{cpc}'.".
                format(sv=sv_name, where=where, sg=sg_name,
                       part=partition.name, cpc=cpc_name),
                error_format)
        return storage_volume

    raise click_exception(
        "Invalid format for volume specified in {where}: '{vs}'. "
        "CPC '{cpc}' has the storage management feature and therefore "
        "only one of the formats 'SG/SV' or 'UUID' is supported.".
        format(where=where, vs=volume_specifier, cpc=cpc_name),
        error_format)


# pylint: disable=inconsistent-return-statements
def parse_volume_without_sm(volume_specifier, partition, where, error_format):
    """
    Parse a volume specifier for a CPC without the storage management feature
    (i.e. z13 and earlier) and return data identifying the storage volume as
    a tuple of:
    * the Hba resource object of the HBA named in the volume specifier
    * the WWPN in the volume specifier
    * the LUN in the volume specifier

    The returned storage volume will always be of type FCP.

    Parameters:

      volume_specifier (string): The volume specifier, in one of these forms:

        * "HBA/WWPN/LUN", where HBA is the name of the HBA resource in the
          partition and WWPN and LUN identify the storage array and storage
          volume thereon.

      partition (Partition): The partition that has the storage group attached
        that contains the specified volume.

      where (string): Text stating where the volume has been specified, e.g.
        "--volume option" (only used for messages).

      error_format (string):
        The error format (see ``--error-format`` general option, only used for
        messages).

    Returns:

      tuple(zhmcclient.Hba, WWPN, LUN): Data identifying the storage volume,
      see description.
    """
    cpc_name = partition.manager.parent.name
    volume_parts = volume_specifier.split('/')

    if len(volume_parts) == 3:  # format: HBA/WWPN/LUN
        hba_name, wwpn, lun = volume_parts
        try:
            hba = partition.hbas.find(name=hba_name)
        except zhmcclient.NotFound:
            raise click_exception(
                "HBA '{hba}' specified in {where} was not found in partition "
                "'{part}' of CPC '{cpc}'.".
                format(hba=hba_name, where=where, part=partition.name,
                       cpc=cpc_name),
                error_format)

        return hba, wwpn, lun

    raise click_exception(
        "Invalid format for volume specified in {where}: '{vs}'. "
        "CPC '{cpc}' does not have the storage management feature and "
        "therefore only the format 'HBA/WWPN/LUN' is supported.".
        format(where=where, vs=volume_specifier, cpc=cpc_name),
        error_format)
