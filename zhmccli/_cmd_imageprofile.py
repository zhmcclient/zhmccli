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
Commands for image activation profiles for CPCs in classic mode.
"""

from __future__ import absolute_import

import click
from click_option_group import optgroup

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS, str2int, \
    absolute_capping_value, parse_yaml_flow_style
from ._cmd_cpc import find_cpc
from ._cmd_certificates import find_certificate


def find_imageprofile(cmd_ctx, client, cpc_name, imageprofile_name):
    """
    Find an image activation profile by name and return its resource object.
    """
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    # The CPC must be in classic mode. We don't check that because it would
    # cause a GET to the CPC resource that we otherwise don't need.
    try:
        imageprofile = cpc.image_activation_profiles.find(
            name=imageprofile_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    return imageprofile


@cli.group('imageprofile', options_metavar=COMMAND_OPTIONS_METAVAR)
def imageprofile_group():
    """
    Command group for managing image activation profiles (classic mode only).

    "Image activation profiles" are used to activate LPARs, and optionally
    to load (= boot, IPL) an operating system or dump program (also known as
    "control program") into the LPAR. Image activation profiles include
    definitions for the resources to be assigned to the LPAR, and also
    definitions for loading the control program.

    The commands in this group work only on CPCs in classic mode.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@imageprofile_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('cpc', type=str, metavar='[CPC]', required=False)
@add_options(LIST_OPTIONS)
@click.pass_obj
def imageprofile_list(cmd_ctx, cpc, **options):
    """
    List the image activation profiles for a CPC, or if omitted for all
    managed CPCs.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_imageprofile_list(cmd_ctx, cpc, options))


@imageprofile_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('cpc', type=str, metavar='CPC')
@click.argument('imageprofile', type=str, metavar='IMAGEPROFILE')
@click.pass_obj
def imageprofile_show(cmd_ctx, cpc, imageprofile, **options):
    """
    Show details of an image activation profile.

    The following properties are shown in addition to those returned by the HMC:

    \b
      - 'parent-name' - Name of the associated (parent) CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_imageprofile_show(cmd_ctx, cpc, imageprofile, options))


@imageprofile_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('cpc', type=str, metavar='CPC')
@click.argument('imageprofile', type=str, metavar='IMAGEPROFILE')
@optgroup.group('General options')
@optgroup.option('--description', type=str, required=False,
                 help='The new description for the image activation profile.')
@optgroup.option('--operating-mode', type=str, metavar='OPMODE', required=False,
                 help='The new operating mode for the LPAR:\n'
                 '\n'
                 '\b\n'
                 '  - "general" - TBD (Update only on z14 or later)\n'
                 '  - "esa390" - z/OS, z/VSE (Update only on z13 or later)\n'
                 '  - "esa390-tpf" - TPF (Update only on z13 or later)\n'
                 '  - "coupling-facility" - Internal Coupling Facility\n'
                 '  - "linux-only" - Linux\n'
                 '  - "zvm" - z/VM\n'
                 '  - "zaware" - zAware appliance (Update only on z13 or '
                 'later)\n'
                 '  - "ssc" - SSC appliances (Update only on z13 or later)\n')
@optgroup.option('--load-at-activation', type=bool, required=False,
                 help='The new indicator for whether the LPAR will be loaded '
                 'at the end of the activation.')
@optgroup.option('--partition-id', type=str, required=False,
                 # Property: 'partition-identifier'
                 help='The new partition identifier (two-digit hexadecimal) to '
                 'be used for the LPAR.')
@optgroup.option('--local-cluster-name', type=str, required=False,
                 help='The name of the new CP management cluster for the LPAR.')
# TODO: Support for --group-profile
@optgroup.option('--liccc-validation-enabled', type=bool, required=False,
                 help='The new indicator for validating that the image profile '
                 'data conforms to the current maximum LICCC configuration.')
@optgroup.option('--lpar-isolation', type=bool, required=False,
                 # Property: 'logical-partition-isolation-control'
                 help='The new LPAR isolation indicator. When True, '
                 'reconfigurable channel paths assigned to the LPAR are '
                 'reserved for its exclusive use.')
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
@optgroup.group('CPU configuration')
@optgroup.option('--processor-usage',
                 type=click.Choice(['dedicated', 'shared']), required=False,
                 help='The new indicator for how processors are allocated to '
                 'the LPAR:\n'
                 '\n'
                 '\b\n'
                 '  - "dedicated" - The processors are exclusively available '
                 'to this LPAR.\n'
                 '  - "shared" - The processors are shareable across LPARs.\n')
@optgroup.option('--wlm-enabled', type=bool, required=False,
                 # Property: 'workload-manager-enabled'
                 help='The new indicator for enabling z/OS Workload Manager. '
                 'If True, z/OS Workload Manager is allowed to change '
                 'processing weight related properties of the LPAR after '
                 'activation.')
@optgroup.option('--defined-capacity', type=bool, required=False,
                 help='The new defined capacity of the LPAR '
                 '(in MSU/h). This specifies how much capacity the LPAR is to '
                 'be managed to by z/OS Workload Manager for the purpose of '
                 'software pricing. 0 means that no defined capacity is '
                 'specified for this LPAR.')
@optgroup.option('--shared-cp-processors', type=int, required=False,
                 # Property: 'number-shared-general-purpose-processors'
                 help='The new number of shared CP (general purpose) '
                 'processors to be allocated to the LPAR at activation.')
@optgroup.option('--reserved-shared-cp-processors', type=int, required=False,
                 # Property: 'number-reserved-shared-general-purpose-processors'
                 help='The new number of shared CP (general purpose) '
                 'processors to be reserved for the LPAR, which can be '
                 'dynamically configured after activation.')
@optgroup.option('--initial-cp-processing-weight', type=int, required=False,
                 # Property: 'initial-processing-weight'
                 help='The new initial processing weight for CP (general '
                 'purpose) processors (1-999).')
@optgroup.option('--minimum-cp-processing-weight', type=int, required=False,
                 # Property: 'minimum-processing-weight'
                 help='The new minimum processing weight for CP (general '
                 'purpose) processors (0-999).')
@optgroup.option('--maximum-cp-processing-weight', type=int, required=False,
                 # Property: 'maximum-processing-weight'
                 help='The new maximum processing weight for CP (general '
                 'purpose) processors (0-999).')
@optgroup.option('--cp-processing-weight-capped', type=bool, required=False,
                 # Property: 'initial-processing-weight-capped'
                 help='The new indicator for whether the CP (general purpose) '
                 'processing weight is capped. If True, the processing weight '
                 'is an upper limit. If False, the processing weight is a '
                 'target that can be exceeded if excess CP processor resources '
                 'are available.')
@optgroup.option('--absolute-cp-capping', type=str, metavar='FLOAT',
                 required=False,
                 # Property: 'absolute-general-purpose-capping'
                 #           -> absolute-capping object
                 help='The new value for absolute CP (general purpose) '
                 'processor capping. A numeric value prevents the partition '
                 'from using any more than the specified number of physical '
                 'CP processors. An empty string disables absolute CP '
                 'processor capping.')
@optgroup.option('--dedicated-cp-processors', type=int, required=False,
                 # Property: 'number-dedicated-general-purpose-processors'
                 help='The new number of dedicated CP (general purpose) '
                 'processors to be allocated for the LPAR\'s exclusive use '
                 'at activation.')
@optgroup.option('--reserved-dedicated-cp-processors', type=int, required=False,
                 # Prop: 'number-reserved-dedicated-general-purpose-processors'
                 help='The new number of dedicated CP (general purpose) '
                 'processors to be reserved for the LPAR, which can be '
                 'dynamically configured after activation.')
#
@optgroup.option('--shared-ifl-processors', type=int, required=False,
                 # Property: 'number-shared-ifl-processors'
                 help='The new number of shared IFL (Integrated Facility for '
                 'Linux) processors to be allocated to the LPAR at activation.')
@optgroup.option('--reserved-shared-ifl-processors', type=int, required=False,
                 # Property: 'number-reserved-shared-ifl-processors'
                 help='The new number of shared IFL (Integrated Facility for '
                 'Linux) processors to be reserved for the LPAR, which can be '
                 'dynamically configured after activation.')
@optgroup.option('--initial-ifl-processing-weight', type=int, required=False,
                 # Property: 'initial-ifl-processing-weight'
                 help='The new initial processing weight for IFL (Integrated '
                 'Facility for Linux) processors (1-999).')
@optgroup.option('--minimum-ifl-processing-weight', type=int, required=False,
                 # Property: 'minimum-ifl-processing-weight'
                 help='The new minimum processing weight for IFL (Integrated '
                 'Facility for Linux) processors (0-999).')
@optgroup.option('--maximum-ifl-processing-weight', type=int, required=False,
                 # Property: 'maximum-ifl-processing-weight'
                 help='The new maximum processing weight for IFL (Integrated '
                 'Facility for Linux) processors (0-999).')
@optgroup.option('--ifl-processing-weight-capped', type=bool, required=False,
                 # Property: 'initial-ifl-processing-weight-capped'
                 help='The new indicator for whether the IFL (Integrated '
                 'Facility for Linux) processing weight is capped. If True, '
                 'the processing weight is an upper limit. If False, the '
                 'processing weight is a target that can be exceeded if '
                 'excess IFL processor resources are available.')
@optgroup.option('--absolute-ifl-capping', type=str, metavar='FLOAT',
                 required=False,
                 # Property: 'absolute-ifl-capping' -> absolute-capping object
                 help='The new value for absolute IFL (Integrated Facility for '
                 'Linux) processor capping. A numeric value prevents the '
                 'partition from using any more than the specified number of '
                 'physical IFL processors. An empty string disables absolute '
                 'IFL processor capping.')
@optgroup.option('--dedicated-ifl-processors', type=int, required=False,
                 # Property: 'number-dedicated-ifl-processors'
                 help='The new number of dedicated IFL (Integrated Facility '
                 'for Linux) processors to be allocated for the LPAR\'s '
                 'exclusive use at activation.')
@optgroup.option('--reserved-dedicated-ifl-processors', type=int,
                 required=False,
                 # Property: 'number-reserved-dedicated-ifl-processors'
                 help='The new number of dedicated IFL (Integrated Facility '
                 'for Linux) processors to be reserved for the LPAR, which '
                 'can be dynamically configured after activation.')
#
@optgroup.option('--shared-zaap-processors', type=int, required=False,
                 # Property: 'number-shared-aap-processors'
                 help='The new number of shared zAAP (z Application Assist '
                 'Processor) processors to be allocated to the LPAR at '
                 'activation.')
@optgroup.option('--reserved-shared-zaap-processors', type=int, required=False,
                 # Property: 'number-reserved-shared-aap-processors'
                 help='The new number of shared zAAP (z Application Assist '
                 'Processor) processors to be reserved for the LPAR, which can '
                 'be dynamically configured after activation.')
@optgroup.option('--initial-zaap-processing-weight', type=int, required=False,
                 # Property: 'initial-aap-processing-weight'
                 help='The new initial processing weight for zAAP (z '
                 'Application Assist Processor) processors (1-999).')
@optgroup.option('--minimum-zaap-processing-weight', type=int, required=False,
                 # Property: 'minimum-aap-processing-weight'
                 help='The new minimum processing weight for zAAP (z '
                 'Application Assist Processor) processors (0-999).')
@optgroup.option('--maximum-zaap-processing-weight', type=int, required=False,
                 # Property: 'maximum-aap-processing-weight'
                 help='The new maximum processing weight for zAAP (z '
                 'Application Assist Processor) processors (0-999).')
@optgroup.option('--zaap-processing-weight-capped', type=bool, required=False,
                 # Property: 'initial-aap-processing-weight-capped'
                 help='The new indicator for whether the zAAP (z '
                 'Application Assist Processor) processing weight is capped. '
                 'If True, the processing weight is an upper limit. If False, '
                 'the processing weight is a target that can be exceeded if '
                 'excess zAAP processor resources are available.')
@optgroup.option('--absolute-zaap-capping', type=str, metavar='FLOAT',
                 required=False,
                 # Property: 'absolute-aap-capping' -> absolute-capping object
                 help='The new value for absolute zAAP (z Application Assist '
                 'Processor) processor capping. A numeric value prevents the '
                 'partition from using any more than the specified number of '
                 'physical zAAP processors. An empty string disables absolute '
                 'zAAP processor capping.')
@optgroup.option('--dedicated-zaap-processors', type=int, required=False,
                 # Property: 'number-dedicated-aap-processors'
                 help='The new number of dedicated zAAP (z Application Assist '
                 'Processor) processors to be allocated for the LPAR\'s '
                 'exclusive use at activation.')
@optgroup.option('--reserved-dedicated-zaap-processors', type=int,
                 # Property: 'number-reserved-dedicated-aap-processors'
                 required=False,
                 help='The new number of dedicated zAAP (z Application Assist '
                 'Processor) processors to be reserved for the LPAR, which '
                 'can be dynamically configured after activation.')
#
@optgroup.option('--shared-ziip-processors', type=int, required=False,
                 # Property: 'number-shared-ziip-processors'
                 help='The new number of shared zIIP (z Integrated '
                 'Information Processor) processors to be allocated to the '
                 'LPAR at activation.')
@optgroup.option('--reserved-shared-ziip-processors', type=int, required=False,
                 # Property: 'number-reserved-shared-ziip-processors'
                 help='The new number of shared zIIP (z Integrated '
                 'Information Processor) processors to be reserved for the '
                 'LPAR, which can be dynamically configured after activation.')
@optgroup.option('--initial-ziip-processing-weight', type=int, required=False,
                 # Property: 'initial-ziip-processing-weight'
                 help='The new initial processing weight for zIIP (z '
                 'Integrated Information Processor) processors (1-999).')
@optgroup.option('--minimum-ziip-processing-weight', type=int, required=False,
                 # Property: 'minimum-ziip-processing-weight'
                 help='The new minimum processing weight for zIIP (z '
                 'Integrated Information Processor) processors (0-999).')
@optgroup.option('--maximum-ziip-processing-weight', type=int, required=False,
                 # Property: 'maximum-ziip-processing-weight'
                 help='The new maximum processing weight for zIIP (z '
                 'Integrated Information Processor) processors (0-999).')
@optgroup.option('--ziip-processing-weight-capped', type=bool, required=False,
                 # Property: 'initial-ziip-processing-weight-capped'
                 help='The new indicator for whether the zIIP (z Integrated '
                 'Information Processor) processing weight is capped. '
                 'If True, the processing weight is an upper limit. If False, '
                 'the processing weight is a target that can be exceeded if '
                 'excess zIIP processor resources are available.')
@optgroup.option('--absolute-ziip-capping', type=str, metavar='FLOAT',
                 required=False,
                 # Property: 'absolute-ziip-capping' -> absolute-capping object
                 help='The new value for absolute zIIP (z Integrated '
                 'Information Processor) processor capping. A numeric value '
                 'prevents the partition from using any more than the '
                 'specified number of physical zIIP processors. An empty '
                 'string disables absolute zIIP processor capping.')
@optgroup.option('--dedicated-ziip-processors', type=int, required=False,
                 # Property: 'number-dedicated-ziip-processors'
                 help='The new number of dedicated zIIP (z Integrated '
                 'Information Processor) processors to be allocated for the '
                 'LPAR\'s exclusive use at activation.')
@optgroup.option('--reserved-dedicated-ziip-processors', type=int,
                 # Property: 'number-reserved-dedicated-ziip-processors'
                 required=False,
                 help='The new number of dedicated zIIP (z Integrated '
                 'Information Processor) processors to be reserved for the '
                 'LPAR, which can be dynamically configured after activation.')
#
@optgroup.option('--shared-icf-processors', type=int, required=False,
                 # Property: 'number-shared-icf-processors'
                 help='The new number of shared ICF (Integrated Coupling '
                 'Facility) processors to be allocated to the LPAR at '
                 'activation.')
@optgroup.option('--reserved-shared-icf-processors', type=int, required=False,
                 # Property: 'number-reserved-shared-icf-processors'
                 help='The new number of shared ICF (Integrated Coupling '
                 'Facility) processors to be reserved for the '
                 'LPAR, which can be dynamically configured after activation.')
@optgroup.option('--initial-icf-processing-weight', type=int, required=False,
                 # Property: 'initial-internal-cf-processing-weight'
                 help='The new initial processing weight for ICF (Integrated '
                 'Coupling Facility) processors (1-999).')
@optgroup.option('--minimum-icf-processing-weight', type=int, required=False,
                 # Property: 'minimum-internal-cf-processing-weight'
                 help='The new minimum processing weight for ICF (Integrated '
                 'Coupling Facility) processors (0-999).')
@optgroup.option('--maximum-icf-processing-weight', type=int, required=False,
                 # Property: 'maximum-internal-cf-processing-weight'
                 help='The new maximum processing weight for ICF (Integrated '
                 'Coupling Facility) processors (0-999).')
@optgroup.option('--icf-processing-weight-capped', type=bool, required=False,
                 # Property: 'initial-internal-cf-processing-weight-capped'
                 help='The new indicator for whether the ICF (Integrated '
                 'Coupling Facility) processing weight is capped. '
                 'If True, the processing weight is an upper limit. If False, '
                 'the processing weight is a target that can be exceeded if '
                 'excess ICF processor resources are available.')
@optgroup.option('--absolute-icf-capping', type=str, metavar='FLOAT',
                 required=False,
                 # Property: 'absolute-icf-capping'
                 #           -> absolute-capping object
                 help='The new value for absolute ICF (Integrated Coupling '
                 'Facility) processor capping. A numeric value '
                 'prevents the partition from using any more than the '
                 'specified number of physical ICF processors. An empty '
                 'string disables absolute ICF processor capping.')
@optgroup.option('--dedicated-icf-processors', type=int, required=False,
                 # Property: 'number-dedicated-icf-processors'
                 help='The new number of dedicated ICF (Integrated Coupling '
                 'Facility) processors to be allocated for the LPAR\'s '
                 'exclusive use at activation.')
@optgroup.option('--reserved-dedicated-icf-processors', type=int,
                 # Property: 'number-reserved-dedicated-icf-processors'
                 required=False,
                 help='The new number of dedicated ICF (Integrated Coupling '
                 'Facility) processors to be reserved for the LPAR, which '
                 'can be dynamically configured after activation.')
#
@optgroup.group('Memory configuration')
@optgroup.option('--central-storage', type=int, required=False,
                 help='The new amount of central storage (in MiB) to be '
                 'allocated for the LPAR\'s exclusive use at activation.')
@optgroup.option('--reserved-central-storage', type=int, required=False,
                 help='The new amount of central storage (in MiB) that is '
                 'dynamically reconfigurable to the LPAR after activation.')
@optgroup.option('--expanded-storage', type=int, required=False,
                 help='The new amount of expanded storage (in MiB) to be '
                 'allocated for the LPAR\'s exclusive use at activation.')
@optgroup.option('--reserved-expanded-storage', type=int, required=False,
                 help='The new amount of expanded storage (in MiB) that is '
                 'dynamically reconfigurable to the LPAR after activation.')
@optgroup.option('--initial-vfm-storage', type=int, required=False,
                 help='The new amount of Virtual Flash Memory (VFM) storage '
                 '(in GiB) to be allocated for the LPAR\'s exclusive use at '
                 'activation.')
@optgroup.option('--maximum-vfm-storage', type=int, required=False,
                 help='The new maximum amount of VFM storage (in GiB) that can '
                 'be allocated to the LPAR while it is running.')
@optgroup.option('--central-storage-origin', type=str, required=False,
                 # Property: 'user-specified-central-storage-origin' (bool),
                 #           'central-storage-origin' (long)
                 help='The new user-specified central storage origin address, '
                 'as hexadecimal. An empty string disables the user '
                 'specification of the central storage origin.')
#
@optgroup.group('I/O priority configuration')
@optgroup.option('--minimum-io-priority-queuing', type=int, required=False,
                 help='The new minimum I/O priority queuing (0-255).')
@optgroup.option('--maximum-io-priority-queuing', type=int, required=False,
                 help='The new maximum I/O priority queuing (0-255).')
#
@optgroup.group('Special permission configuration')
@optgroup.option('--access-basic-cpu-counter', type=bool, required=False,
                 # Property: 'basic-cpu-counter-authorization-control'
                 help='The new indicator for enabling access to the '
                 'basic CPU counter facility for the LPAR.')
@optgroup.option('--access-problem-state-cpu-counter', type=bool,
                 required=False,
                 # Property: 'problem-state-cpu-counter-authorization-control'
                 help='The new indicator for enabling access to the '
                 'problem state CPU counter facility for the LPAR.')
@optgroup.option('--access-crypto-activity-cpu-counter', type=bool,
                 required=False,
                 # Property: 'crypto-activity-cpu-counter-authorization-control'
                 help='The new indicator for enabling access to the '
                 'crypto activity CPU counter facility for the LPAR.')
@optgroup.option('--access-extended-cpu-counter', type=bool, required=False,
                 # Property: 'extended-cpu-counter-authorization-control'
                 help='The new indicator for enabling access to the '
                 'extended CPU counter facility for the LPAR.')
@optgroup.option('--access-coprocessor-cpu-counter', type=bool, required=False,
                 # Property: 'coprocessor-cpu-counter-authorization-control'
                 help='The new indicator for enabling access to the '
                 'coprocessor group CPU counter facility for the LPAR.')
@optgroup.option('--access-diagnostic-sampling', type=bool, required=False,
                 # Property: 'diagnostic-sampling-authorization-control'
                 help='The new indicator for enabling access to the '
                 'diagnostic sampling facility for the LPAR.')
@optgroup.option('--access-basic-cpu-sampling', type=bool, required=False,
                 # Property: 'basic-cpu-sampling-authorization-control'
                 help='The new indicator for enabling access to the '
                 'basic CPU sampling facility for the LPAR.')
@optgroup.option('--permit-aes-key-import', type=bool, required=False,
                 # Property: 'permit-aes-key-import-functions'
                 help='The new indicator for permitting the '
                 'importing of AES keys for the LPAR.')
@optgroup.option('--permit-des-key-import', type=bool, required=False,
                 # Property: 'permit-des-key-import-functions'
                 help='The new indicator for permitting the '
                 'importing of DES keys for the LPAR.')
@optgroup.option('--permit-ecc-key-import', type=bool, required=False,
                 # Property: 'permit-ecc-key-import-functions'
                 help='The new indicator for permitting the '
                 'importing of ECC keys for the LPAR.')
@optgroup.option('--access-global-performance-data', type=bool, required=False,
                 # Property: 'global-performance-data-authorization-control'
                 help='The new indicator for enabling access to the processor '
                 'activity data for all other LPARs on the same CPC.')
@optgroup.option('--permit-global-iocds', type=bool, required=False,
                 # Property: 'io-configuration-authorization-control'
                 help='The new indicator for permitting to read and write any '
                 'IOCDS in the configuration.')
@optgroup.option('--permit-cross-partition-authority', type=bool,
                 required=False,
                 # Property: 'cross-partition-authority-authorization-control'
                 help='The new indicator for permitting to issue control '
                 'program instructions that reset or deactivate other LPARs.')
@optgroup.option('--permit-bcpii-send-commands', type=bool, required=False,
                 # Property: 'security-bcpii-send-commands'
                 help='The new indicator for whether the LPAR is permitted to '
                 'send commands through BCPii.')
@optgroup.option('--permit-bcpii-receive-commands', required=False,
                 # Property: 'security-bcpii-receive-commands', (bool)
                 #           'security-bcpii-receive-selection' (enum)
                 type=click.Choice(['none', 'all', 'bcpii-list']),
                 help='The new indicator that determines whether and which '
                 'commands the LPAR is permitted to receive through BCPii:\n'
                 '\n'
                 '\b\n'
                 '  - "none" – (default) No BCPii commands are allowed.\n'
                 '  - "all" – all BCPii commands are allowed.\n'
                 '  - "bcpii-list" – only the BCPii commands in the list are '
                 'allowed.\n')
@optgroup.option('--bcpii-receive-partitions', type=str, required=False,
                 # Property: 'security-bcpii-receive-partition-list'
                 #           -> add to list
                 help='The new list of LPARs from which the LPAR activated by '
                 'this profile is allowed to receive commands through BCPii '
                 '(if generally permitted). The LPARs in the string are '
                 'comma-separated, and each LPAR is referenced in the format '
                 '"NETID.SYSTEM.LPAR".')
@optgroup.group('Clock configuration')
@optgroup.option('--clock-type', required=False,
                 type=click.Choice(['standard', 'lpar']),
                 help='The new clock type for the LPAR: '
                 '"standard" - Use the CPC\'s time source. '
                 '"lpar" - Use an offset from the External Time Source.')
@optgroup.option('--time-offset-direction', required=False,
                 # Property: 'time-offset-increase-decrease'
                 type=click.Choice(['increase', 'decrease']),
                 help='The new clock type for the LPAR:\n'
                 '\n'
                 '\b\n'
                 '  - "increase" - LPAR clock is ahead of the External '
                 'Time Source.\n'
                 '  - "decrease" - LPAR clock is behind the External '
                 'Time Source.\n')
@optgroup.option('--time-offset-days', type=int, required=False,
                 help='The new number of days the LPAR\'s clock '
                 'is to be offset from the External Time Source.')
@optgroup.option('--time-offset-hours', type=int, required=False,
                 help='The new number of hours the LPAR\'s clock '
                 'is to be offset from the External Time Source.')
@optgroup.option('--time-offset-minutes', type=int, required=False,
                 help='The new number of minutes the LPAR\'s '
                 'clock is to be offset from the External Time Source.')
@optgroup.group('zAware configuration (only applicable to zAware LPARs)')
@optgroup.option('--zaware-host-name', type=str, required=False,
                 help='The new hostname for IBM zAware. '
                 'Empty string sets no hostname.')
@optgroup.option('--zaware-master-userid', type=str, required=False,
                 help='The new master userid for IBM zAware. '
                 'Empty string sets no master userid.')
@optgroup.option('--zaware-master-password', type=str, required=False,
                 # Property: 'zaware-master-pw'
                 help='The new master password for IBM zAware. '
                 'Empty string sets no master password.')
@optgroup.option('--zaware-network-info', type=str, required=False,
                 help='The new list of networks available to IBM zAware, in '
                 'YAML Flow Collection style. '
                 'Each list item must be a "zaware-network" object (described '
                 'in the HMC WS-API book). '
                 'A minimum of 1 network and a maximum of 100 networks are '
                 'permitted. The specified list fully replaces the existing '
                 'list in the HMC. '
                 'Example: --zaware-network-info "[{port: 444, ipaddr-type: '
                 'static, vlan-id: 53, static-ip-info: {type: ipv4, '
                 'ip-address: \'10.11.12.13\', prefix: 24}}]"')
@optgroup.option('--zaware-gateway-info', type=str, required=False,
                 help='The new default gateway IP address information for IBM '
                 'zAware, as an "ip-info" object (described in the HMC WS-API '
                 'book) in YAML Flow Collection style. '
                 'An empty string removes the default gateway IP address. '
                 'Example: --zaware-gateway-info "{type: ipv4, ip-address: '
                 '\'10.11.12.13\', prefix: 24}"')
@optgroup.option('--zaware-dns-info', type=str, required=False,
                 help='The new list of DNS IP addresses for IBM zAware, in '
                 'YAML Flow Collection style. '
                 'Each list item must be an "ip-info" object (described in the '
                 'HMC WS-API book). '
                 'A minimum of 0 addresses and a maximum of 2 addresses are '
                 'permitted. The specified list fully replaces the existing '
                 'list in the HMC. '
                 'Example: --zaware-dns-info "[{type: ipv4, ip-address: '
                 '\'10.11.12.13\', prefix: 24}]"')
@optgroup.group('SSC configuration (only applicable to SSC LPARs)')
@optgroup.option('--ssc-host-name', type=str, required=False,
                 help='The new hostname for the SSC appliance. '
                 'Empty string sets no hostname.')
@optgroup.option('--ssc-master-userid', type=str, required=False,
                 help='The new master userid for the SSC appliance. '
                 'Empty string sets no master userid.')
@optgroup.option('--ssc-master-password', type=str, required=False,
                 # Property: 'ssc-master-pw'
                 help='The new master password for the SSC appliance. '
                 'Empty string sets no master password.')
@optgroup.option('--ssc-boot-selection', required=False,
                 type=click.Choice(['installer', 'appliance']),
                 help='The new boot selection for the SSC LPAR.')
@optgroup.option('--ssc-network-info', type=str, required=False,
                 help='The new list of networks available to the SSC '
                 'appliance, in YAML Flow Collection style. '
                 'Each list item must be a "ssc-network" object (described '
                 'in the HMC WS-API book). '
                 'A minimum of 1 network and a maximum of 100 networks are '
                 'permitted. The specified list fully replaces the existing '
                 'list in the HMC. '
                 'Example: --ssc-network-info "[{port: 444, ipaddr-type: '
                 'static, vlan-id: 53, static-ip-info: {type: ipv4, '
                 'ip-address: \'10.11.12.13\', prefix: 24}}]"')
@optgroup.option('--ssc-gateway-info', type=str, required=False,
                 help='The new default gateway IP address information for the '
                 'SSC appliance, as an "ip-info" object (described in the '
                 'HMC WS-API book) in YAML Flow Collection style. '
                 'An empty string removes the default gateway IP address. '
                 'Example: --ssc-gateway-info "{type: ipv4, ip-address: '
                 '\'10.11.12.13\', prefix: 24}"')
@optgroup.option('--ssc-gateway-ipv6-info', type=str, required=False,
                 help='The new default gateway IPv6 address information for '
                 'the SSC appliance, as an "ip-info" object (described in the '
                 'HMC WS-API book) in YAML Flow Collection style. '
                 'An empty string removes the default gateway IP address. '
                 'Example: --ssc-gateway-ipv6-info "{type: ipv6, ip-address: '
                 '\'10:11:12:13:14:15\', prefix: 24}"')
@optgroup.option('--ssc-dns-info', type=str, required=False,
                 help='The new list of DNS IP addresses for the SSC appliance, '
                 'in YAML Flow Collection style. '
                 'Each list item must be an "ip-info" object (described in the '
                 'HMC WS-API book). '
                 'A minimum of 0 addresses and a maximum of 2 addresses are '
                 'permitted. The specified list fully replaces the existing '
                 'list in the HMC. '
                 'Example: --ssc-dns-info "[{type: ipv4, ip-address: '
                 '\'10.11.12.13\', prefix: 24}]"')
# TODO: SEPARATE assigned-crypto-domains Array of assigned-crypto-domain
#       objects - Specifies the crypto domains and their access modes to be
#       assigned to the LPAR once activated.
# TODO: SEPARATE assigned-cryptos — Array of assigned-crypto objects - Specifies
#       the crypto adapters to be assigned to the LPAR once activated.
# TODO: SEPARATE assigned-certificate-uris (c)(pc) Array of String/ URI - Array
#       of URIs referring to the certificates that are assigned to this image
#       activation profile, or an empty array if there are no assigned
#       certificates.
@click.pass_obj
def imageprofile_update(cmd_ctx, cpc, imageprofile, **options):
    """
    Update the properties of an image activation profile.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    Some of the options of this command are documented to be specified in YAML
    Flow Collection style. That is a format for specifying complex values
    that are lists or dictionaries as a relatively simple string. The format
    is described for example in https://www.yaml.info/learn/flowstyle.html.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.

    \b
    Limitations:
      * The command does not support updating the network-related properties
        for zAware and SSC.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_imageprofile_update(cmd_ctx, cpc, imageprofile, options))


@imageprofile_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('cpc', type=str, metavar='CPC')
@optgroup.group('General options')
@optgroup.option('--name', type=str, required=True,
                 # Property: 'profile-name'
                 help='The name for the new image activation profile. '
                 'The names of reset, image, and load activation profiles are '
                 'all in the same namespace for each CPC and must be unique '
                 'within that namespace.')
@optgroup.option('--copy-name', type=str, required=False,
                 help='The name of an existing image activation profile whose '
                 'properties act as defaults for options not specified in '
                 'this command. Default: The image activation profile named '
                 '"DEFAULT".')
@optgroup.option('--description', type=str, required=False,
                 help='The description for the new image activation profile.')
@optgroup.option('--operating-mode', type=str, metavar='OPMODE', required=False,
                 help='The operating mode for the LPAR:\n'
                 '\n'
                 '\b\n'
                 '  - "general" - TBD (Only on z14 or later)\n'
                 '  - "coupling-facility" - Internal Coupling Facility\n'
                 '  - "linux-only" - Linux\n'
                 '  - "zvm" - z/VM\n'
                 '  - "ssc" - SSC appliances (Only on z13 or later)\n'
                 'Note that only this subset of operating modes can be used '
                 'when creating image activation profiles.')
@optgroup.option('--load-at-activation', type=bool, required=False,
                 help='The indicator for whether the LPAR will be loaded '
                 'at the end of the activation.')
@optgroup.option('--partition-id', type=str, required=False,
                 # Property: 'partition-identifier'
                 help='The partition identifier (two-digit hexadecimal) to '
                 'be used for the LPAR.')
@optgroup.option('--local-cluster-name', type=str, required=False,
                 help='The name of the CP management cluster for the LPAR.')
# TODO: Support for --group-profile
@optgroup.option('--liccc-validation-enabled', type=bool, required=False,
                 help='The indicator for validating that the image profile '
                 'data conforms to the current maximum LICCC configuration.')
@optgroup.option('--lpar-isolation', type=bool, required=False,
                 # Property: 'logical-partition-isolation-control'
                 help='The LPAR isolation indicator. When True, '
                 'reconfigurable channel paths assigned to the LPAR are '
                 'reserved for its exclusive use.')
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
                 help='The load parameter (property "ipl-parameter"). '
                 'This is a short (0-8 characters) string passed to the '
                 'control program. Valid characters are "0"-"9", "A"-"Z", '
                 'blank (" ") and period ("."). On z14 and later, the '
                 'characters "@", "$", and "#" are valid in addition.')
@optgroup.option('--os-load-parameters', type=str, required=False,
                 # Property: 'os-specific-load-parameters'
                 help='The operating system-specific load parameters (property '
                 '"os-specific-load-parameters"). '
                 'This is a longer string string passed to the control '
                 'program. Only used for the list-directed IPL types '
                 '"ipltype-scsi", "ipltype-scsidump", "ipltype-nvmeload", '
                 '"ipltype-nvmedump", "ipltype-eckd-ld-load", or '
                 '"ipltype-eckd-ld-dump".')
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
@optgroup.group('CPU configuration')
@optgroup.option('--processor-usage',
                 type=click.Choice(['dedicated', 'shared']), required=False,
                 help='The indicator for how processors are allocated to '
                 'the LPAR:\n'
                 '\n'
                 '\b\n'
                 '  - "dedicated" - The processors are exclusively available '
                 'to this LPAR.\n'
                 '  - "shared" - The processors are shareable across LPARs.\n')
@optgroup.option('--wlm-enabled', type=bool, required=False,
                 # Property: 'workload-manager-enabled'
                 help='The indicator for enabling z/OS Workload Manager. '
                 'If True, z/OS Workload Manager is allowed to change '
                 'processing weight related properties of the LPAR after '
                 'activation.')
@optgroup.option('--defined-capacity', type=bool, required=False,
                 help='The defined capacity of the LPAR '
                 '(in MSU/h). This specifies how much capacity the LPAR is to '
                 'be managed to by z/OS Workload Manager for the purpose of '
                 'software pricing. 0 means that no defined capacity is '
                 'specified for this LPAR.')
@optgroup.option('--shared-cp-processors', type=int, required=False,
                 # Property: 'number-shared-general-purpose-processors'
                 help='The number of shared CP (general purpose) '
                 'processors to be allocated to the LPAR at activation.')
@optgroup.option('--reserved-shared-cp-processors', type=int, required=False,
                 # Property: 'number-reserved-shared-general-purpose-processors'
                 help='The number of shared CP (general purpose) '
                 'processors to be reserved for the LPAR, which can be '
                 'dynamically configured after activation.')
@optgroup.option('--initial-cp-processing-weight', type=int, required=False,
                 # Property: 'initial-processing-weight'
                 help='The initial processing weight for CP (general '
                 'purpose) processors (1-999).')
@optgroup.option('--minimum-cp-processing-weight', type=int, required=False,
                 # Property: 'minimum-processing-weight'
                 help='The minimum processing weight for CP (general '
                 'purpose) processors (0-999).')
@optgroup.option('--maximum-cp-processing-weight', type=int, required=False,
                 # Property: 'maximum-processing-weight'
                 help='The maximum processing weight for CP (general '
                 'purpose) processors (0-999).')
@optgroup.option('--cp-processing-weight-capped', type=bool, required=False,
                 # Property: 'initial-processing-weight-capped'
                 help='The indicator for whether the CP (general purpose) '
                 'processing weight is capped. If True, the processing weight '
                 'is an upper limit. If False, the processing weight is a '
                 'target that can be exceeded if excess CP processor resources '
                 'are available.')
@optgroup.option('--absolute-cp-capping', type=str, metavar='FLOAT',
                 required=False,
                 # Property: 'absolute-general-purpose-capping'
                 #           -> absolute-capping object
                 help='The value for absolute CP (general purpose) '
                 'processor capping. A numeric value prevents the partition '
                 'from using any more than the specified number of physical '
                 'CP processors. An empty string disables absolute CP '
                 'processor capping.')
@optgroup.option('--dedicated-cp-processors', type=int, required=False,
                 # Property: 'number-dedicated-general-purpose-processors'
                 help='The number of dedicated CP (general purpose) '
                 'processors to be allocated for the LPAR\'s exclusive use '
                 'at activation.')
@optgroup.option('--reserved-dedicated-cp-processors', type=int, required=False,
                 # Prop: 'number-reserved-dedicated-general-purpose-processors'
                 help='The number of dedicated CP (general purpose) '
                 'processors to be reserved for the LPAR, which can be '
                 'dynamically configured after activation.')
#
@optgroup.option('--shared-ifl-processors', type=int, required=False,
                 # Property: 'number-shared-ifl-processors'
                 help='The number of shared IFL (Integrated Facility for '
                 'Linux) processors to be allocated to the LPAR at activation.')
@optgroup.option('--reserved-shared-ifl-processors', type=int, required=False,
                 # Property: 'number-reserved-shared-ifl-processors'
                 help='The number of shared IFL (Integrated Facility for '
                 'Linux) processors to be reserved for the LPAR, which can be '
                 'dynamically configured after activation.')
@optgroup.option('--initial-ifl-processing-weight', type=int, required=False,
                 # Property: 'initial-ifl-processing-weight'
                 help='The initial processing weight for IFL (Integrated '
                 'Facility for Linux) processors (1-999).')
@optgroup.option('--minimum-ifl-processing-weight', type=int, required=False,
                 # Property: 'minimum-ifl-processing-weight'
                 help='The minimum processing weight for IFL (Integrated '
                 'Facility for Linux) processors (0-999).')
@optgroup.option('--maximum-ifl-processing-weight', type=int, required=False,
                 # Property: 'maximum-ifl-processing-weight'
                 help='The maximum processing weight for IFL (Integrated '
                 'Facility for Linux) processors (0-999).')
@optgroup.option('--ifl-processing-weight-capped', type=bool, required=False,
                 # Property: 'initial-ifl-processing-weight-capped'
                 help='The indicator for whether the IFL (Integrated '
                 'Facility for Linux) processing weight is capped. If True, '
                 'the processing weight is an upper limit. If False, the '
                 'processing weight is a target that can be exceeded if '
                 'excess IFL processor resources are available.')
@optgroup.option('--absolute-ifl-capping', type=str, metavar='FLOAT',
                 required=False,
                 # Property: 'absolute-ifl-capping' -> absolute-capping object
                 help='The value for absolute IFL (Integrated Facility for '
                 'Linux) processor capping. A numeric value prevents the '
                 'partition from using any more than the specified number of '
                 'physical IFL processors. An empty string disables absolute '
                 'IFL processor capping.')
@optgroup.option('--dedicated-ifl-processors', type=int, required=False,
                 # Property: 'number-dedicated-ifl-processors'
                 help='The number of dedicated IFL (Integrated Facility '
                 'for Linux) processors to be allocated for the LPAR\'s '
                 'exclusive use at activation.')
@optgroup.option('--reserved-dedicated-ifl-processors', type=int,
                 required=False,
                 # Property: 'number-reserved-dedicated-ifl-processors'
                 help='The number of dedicated IFL (Integrated Facility '
                 'for Linux) processors to be reserved for the LPAR, which '
                 'can be dynamically configured after activation.')
#
@optgroup.option('--shared-zaap-processors', type=int, required=False,
                 # Property: 'number-shared-aap-processors'
                 help='The number of shared zAAP (z Application Assist '
                 'Processor) processors to be allocated to the LPAR at '
                 'activation.')
@optgroup.option('--reserved-shared-zaap-processors', type=int, required=False,
                 # Property: 'number-reserved-shared-aap-processors'
                 help='The number of shared zAAP (z Application Assist '
                 'Processor) processors to be reserved for the LPAR, which can '
                 'be dynamically configured after activation.')
@optgroup.option('--initial-zaap-processing-weight', type=int, required=False,
                 # Property: 'initial-aap-processing-weight'
                 help='The initial processing weight for zAAP (z '
                 'Application Assist Processor) processors (1-999).')
@optgroup.option('--minimum-zaap-processing-weight', type=int, required=False,
                 # Property: 'minimum-aap-processing-weight'
                 help='The minimum processing weight for zAAP (z '
                 'Application Assist Processor) processors (0-999).')
@optgroup.option('--maximum-zaap-processing-weight', type=int, required=False,
                 # Property: 'maximum-aap-processing-weight'
                 help='The maximum processing weight for zAAP (z '
                 'Application Assist Processor) processors (0-999).')
@optgroup.option('--zaap-processing-weight-capped', type=bool, required=False,
                 # Property: 'initial-aap-processing-weight-capped'
                 help='The indicator for whether the zAAP (z '
                 'Application Assist Processor) processing weight is capped. '
                 'If True, the processing weight is an upper limit. If False, '
                 'the processing weight is a target that can be exceeded if '
                 'excess zAAP processor resources are available.')
@optgroup.option('--absolute-zaap-capping', type=str, metavar='FLOAT',
                 required=False,
                 # Property: 'absolute-aap-capping' -> absolute-capping object
                 help='The value for absolute zAAP (z Application Assist '
                 'Processor) processor capping. A numeric value prevents the '
                 'partition from using any more than the specified number of '
                 'physical zAAP processors. An empty string disables absolute '
                 'zAAP processor capping.')
@optgroup.option('--dedicated-zaap-processors', type=int, required=False,
                 # Property: 'number-dedicated-aap-processors'
                 help='The number of dedicated zAAP (z Application Assist '
                 'Processor) processors to be allocated for the LPAR\'s '
                 'exclusive use at activation.')
@optgroup.option('--reserved-dedicated-zaap-processors', type=int,
                 # Property: 'number-reserved-dedicated-aap-processors'
                 required=False,
                 help='The number of dedicated zAAP (z Application Assist '
                 'Processor) processors to be reserved for the LPAR, which '
                 'can be dynamically configured after activation.')
#
@optgroup.option('--shared-ziip-processors', type=int, required=False,
                 # Property: 'number-shared-ziip-processors'
                 help='The number of shared zIIP (z Integrated '
                 'Information Processor) processors to be allocated to the '
                 'LPAR at activation.')
@optgroup.option('--reserved-shared-ziip-processors', type=int, required=False,
                 # Property: 'number-reserved-shared-ziip-processors'
                 help='The number of shared zIIP (z Integrated '
                 'Information Processor) processors to be reserved for the '
                 'LPAR, which can be dynamically configured after activation.')
@optgroup.option('--initial-ziip-processing-weight', type=int, required=False,
                 # Property: 'initial-ziip-processing-weight'
                 help='The initial processing weight for zIIP (z '
                 'Integrated Information Processor) processors (1-999).')
@optgroup.option('--minimum-ziip-processing-weight', type=int, required=False,
                 # Property: 'minimum-ziip-processing-weight'
                 help='The minimum processing weight for zIIP (z '
                 'Integrated Information Processor) processors (0-999).')
@optgroup.option('--maximum-ziip-processing-weight', type=int, required=False,
                 # Property: 'maximum-ziip-processing-weight'
                 help='The maximum processing weight for zIIP (z '
                 'Integrated Information Processor) processors (0-999).')
@optgroup.option('--ziip-processing-weight-capped', type=bool, required=False,
                 # Property: 'initial-ziip-processing-weight-capped'
                 help='The indicator for whether the zIIP (z Integrated '
                 'Information Processor) processing weight is capped. '
                 'If True, the processing weight is an upper limit. If False, '
                 'the processing weight is a target that can be exceeded if '
                 'excess zIIP processor resources are available.')
@optgroup.option('--absolute-ziip-capping', type=str, metavar='FLOAT',
                 required=False,
                 # Property: 'absolute-ziip-capping' -> absolute-capping object
                 help='The value for absolute zIIP (z Integrated '
                 'Information Processor) processor capping. A numeric value '
                 'prevents the partition from using any more than the '
                 'specified number of physical zIIP processors. An empty '
                 'string disables absolute zIIP processor capping.')
@optgroup.option('--dedicated-ziip-processors', type=int, required=False,
                 # Property: 'number-dedicated-ziip-processors'
                 help='The number of dedicated zIIP (z Integrated '
                 'Information Processor) processors to be allocated for the '
                 'LPAR\'s exclusive use at activation.')
@optgroup.option('--reserved-dedicated-ziip-processors', type=int,
                 # Property: 'number-reserved-dedicated-ziip-processors'
                 required=False,
                 help='The number of dedicated zIIP (z Integrated '
                 'Information Processor) processors to be reserved for the '
                 'LPAR, which can be dynamically configured after activation.')
#
@optgroup.option('--shared-icf-processors', type=int, required=False,
                 # Property: 'number-shared-icf-processors'
                 help='The number of shared ICF (Integrated Coupling '
                 'Facility) processors to be allocated to the LPAR at '
                 'activation.')
@optgroup.option('--reserved-shared-icf-processors', type=int, required=False,
                 # Property: 'number-reserved-shared-icf-processors'
                 help='The number of shared ICF (Integrated Coupling '
                 'Facility) processors to be reserved for the '
                 'LPAR, which can be dynamically configured after activation.')
@optgroup.option('--initial-icf-processing-weight', type=int, required=False,
                 # Property: 'initial-internal-cf-processing-weight'
                 help='The initial processing weight for ICF (Integrated '
                 'Coupling Facility) processors (1-999).')
@optgroup.option('--minimum-icf-processing-weight', type=int, required=False,
                 # Property: 'minimum-internal-cf-processing-weight'
                 help='The minimum processing weight for ICF (Integrated '
                 'Coupling Facility) processors (0-999).')
@optgroup.option('--maximum-icf-processing-weight', type=int, required=False,
                 # Property: 'maximum-internal-cf-processing-weight'
                 help='The maximum processing weight for ICF (Integrated '
                 'Coupling Facility) processors (0-999).')
@optgroup.option('--icf-processing-weight-capped', type=bool, required=False,
                 # Property: 'initial-internal-cf-processing-weight-capped'
                 help='The indicator for whether the ICF (Integrated '
                 'Coupling Facility) processing weight is capped. '
                 'If True, the processing weight is an upper limit. If False, '
                 'the processing weight is a target that can be exceeded if '
                 'excess ICF processor resources are available.')
@optgroup.option('--absolute-icf-capping', type=str, metavar='FLOAT',
                 required=False,
                 # Property: 'absolute-icf-capping'
                 #           -> absolute-capping object
                 help='The value for absolute ICF (Integrated Coupling '
                 'Facility) processor capping. A numeric value '
                 'prevents the partition from using any more than the '
                 'specified number of physical ICF processors. An empty '
                 'string disables absolute ICF processor capping.')
@optgroup.option('--dedicated-icf-processors', type=int, required=False,
                 # Property: 'number-dedicated-icf-processors'
                 help='The number of dedicated ICF (Integrated Coupling '
                 'Facility) processors to be allocated for the LPAR\'s '
                 'exclusive use at activation.')
@optgroup.option('--reserved-dedicated-icf-processors', type=int,
                 # Property: 'number-reserved-dedicated-icf-processors'
                 required=False,
                 help='The number of dedicated ICF (Integrated Coupling '
                 'Facility) processors to be reserved for the LPAR, which '
                 'can be dynamically configured after activation.')
#
@optgroup.group('Memory configuration')
@optgroup.option('--central-storage', type=int, required=False,
                 help='New amount of central storage (in MiB) to be allocated '
                 'for the LPAR\'s exclusive use at activation.')
@optgroup.option('--reserved-central-storage', type=int, required=False,
                 help='New amount of central storage (in MiB) that is '
                 'dynamically reconfigurable to the LPAR after activation.')
@optgroup.option('--expanded-storage', type=int, required=False,
                 help='New amount of expanded storage (in MiB) to be allocated '
                 'for the LPAR\'s exclusive use at activation.')
@optgroup.option('--reserved-expanded-storage', type=int, required=False,
                 help='New amount of expanded storage (in MiB) that is '
                 'dynamically reconfigurable to the LPAR after activation.')
@optgroup.option('--initial-vfm-storage', type=int, required=False,
                 help='New amount of Virtual Flash Memory (VFM) storage '
                 '(in GiB) to be allocated for the LPAR\'s exclusive use at '
                 'activation.')
@optgroup.option('--maximum-vfm-storage', type=int, required=False,
                 help='New maximum amount of VFM storage (in GiB) that can be '
                 'allocated to the LPAR while it is running.')
@optgroup.option('--central-storage-origin', type=str, required=False,
                 # Property: 'user-specified-central-storage-origin' (bool),
                 #           'central-storage-origin' (long)
                 help='New user-specified central storage origin address, as '
                 'hexadecimal. An empty string disables the user specification '
                 'of the central storage origin.')
#
@optgroup.group('I/O priority configuration')
@optgroup.option('--minimum-io-priority-queuing', type=int, required=False,
                 help='The minimum I/O priority queuing (0-255).')
@optgroup.option('--maximum-io-priority-queuing', type=int, required=False,
                 help='The maximum I/O priority queuing (0-255).')
#
@optgroup.group('Special permission configuration')
@optgroup.option('--access-basic-cpu-counter', type=bool, required=False,
                 # Property: 'basic-cpu-counter-authorization-control'
                 help='The indicator for enabling access to the '
                 'basic CPU counter facility for the LPAR.')
@optgroup.option('--access-problem-state-cpu-counter', type=bool,
                 required=False,
                 # Property: 'problem-state-cpu-counter-authorization-control'
                 help='The indicator for enabling access to the '
                 'problem state CPU counter facility for the LPAR.')
@optgroup.option('--access-crypto-activity-cpu-counter', type=bool,
                 required=False,
                 # Property: 'crypto-activity-cpu-counter-authorization-control'
                 help='The indicator for enabling access to the '
                 'crypto activity CPU counter facility for the LPAR.')
@optgroup.option('--access-extended-cpu-counter', type=bool, required=False,
                 # Property: 'extended-cpu-counter-authorization-control'
                 help='The indicator for enabling access to the '
                 'extended CPU counter facility for the LPAR.')
@optgroup.option('--access-coprocessor-cpu-counter', type=bool, required=False,
                 # Property: 'coprocessor-cpu-counter-authorization-control'
                 help='The indicator for enabling access to the '
                 'coprocessor group CPU counter facility for the LPAR.')
@optgroup.option('--access-diagnostic-sampling', type=bool, required=False,
                 # Property: 'diagnostic-sampling-authorization-control'
                 help='The indicator for enabling access to the '
                 'diagnostic sampling facility for the LPAR.')
@optgroup.option('--access-basic-cpu-sampling', type=bool, required=False,
                 # Property: 'basic-cpu-sampling-authorization-control'
                 help='The indicator for enabling access to the '
                 'basic CPU sampling facility for the LPAR.')
@optgroup.option('--permit-aes-key-import', type=bool, required=False,
                 # Property: 'permit-aes-key-import-functions'
                 help='The indicator for permitting the '
                 'importing of AES keys for the LPAR.')
@optgroup.option('--permit-des-key-import', type=bool, required=False,
                 # Property: 'permit-des-key-import-functions'
                 help='The indicator for permitting the '
                 'importing of DES keys for the LPAR.')
@optgroup.option('--permit-ecc-key-import', type=bool, required=False,
                 # Property: 'permit-ecc-key-import-functions'
                 help='The indicator for permitting the '
                 'importing of ECC keys for the LPAR.')
@optgroup.option('--access-global-performance-data', type=bool, required=False,
                 # Property: 'global-performance-data-authorization-control'
                 help='The indicator for enabling access to the processor '
                 'activity data for all other LPARs on the same CPC.')
@optgroup.option('--permit-global-iocds', type=bool, required=False,
                 # Property: 'io-configuration-authorization-control'
                 help='The indicator for permitting to read and write any '
                 'IOCDS in the configuration.')
@optgroup.option('--permit-cross-partition-authority', type=bool,
                 required=False,
                 # Property: 'cross-partition-authority-authorization-control'
                 help='The indicator for permitting to issue control '
                 'program instructions that reset or deactivate other LPARs.')
@optgroup.option('--permit-bcpii-send-commands', type=bool, required=False,
                 # Property: 'security-bcpii-send-commands'
                 help='Determines whether the LPAR is permitted to send '
                 'commands through BCPii.')
@optgroup.option('--permit-bcpii-receive-commands', required=False,
                 # Property: 'security-bcpii-receive-commands', (bool)
                 #           'security-bcpii-receive-selection' (enum)
                 type=click.Choice(['none', 'all', 'bcpii-list']),
                 help='Determines whether and which commands the LPAR is '
                 'permitted to receive through BCPii:\n'
                 '\n'
                 '\b\n'
                 '  - "none" – (default) No BCPii commands are allowed.\n'
                 '  - "all" – all BCPii commands are allowed.\n'
                 '  - "bcpii-list" – only the BCPii commands in the list are '
                 'allowed.\n')
@optgroup.option('--bcpii-receive-partitions', type=str, required=False,
                 # Property: 'security-bcpii-receive-partition-list'
                 #           -> add to list
                 help='Comma-separated list of LPARs from which the LPAR '
                 'activated by this profile is allowed to receive commands '
                 'through BCPii (if generally permitted). '
                 'Each LPAR is referenced in the format "NETID.SYSTEM.LPAR".')
@optgroup.group('Clock configuration')
@optgroup.option('--clock-type', required=False,
                 type=click.Choice(['standard', 'lpar']),
                 help='The clock type for the LPAR: '
                 '"standard" - Use the CPC\'s time source. '
                 '"lpar" - Use an offset from the External Time Source.')
@optgroup.option('--time-offset-direction', required=False,
                 # Property: 'time-offset-increase-decrease'
                 type=click.Choice(['increase', 'decrease']),
                 help='The clock type for the LPAR:\n'
                 '\n'
                 '\b\n'
                 '  - "increase" - LPAR clock is ahead of the External '
                 'Time Source.\n'
                 '  - "decrease" - LPAR clock is behind the External '
                 'Time Source.\n')
@optgroup.option('--time-offset-days', type=int, required=False,
                 help='The number of days the LPAR\'s clock '
                 'is to be offset from the External Time Source.')
@optgroup.option('--time-offset-hours', type=int, required=False,
                 help='The number of hours the LPAR\'s clock '
                 'is to be offset from the External Time Source.')
@optgroup.option('--time-offset-minutes', type=int, required=False,
                 help='The number of minutes the LPAR\'s '
                 'clock is to be offset from the External Time Source.')
@optgroup.group('zAware configuration (only applicable to zAware LPARs)')
@optgroup.option('--zaware-host-name', type=str, required=False,
                 help='The hostname for IBM zAware. '
                 'Empty string sets no hostname.')
@optgroup.option('--zaware-master-userid', type=str, required=False,
                 help='The master userid for IBM zAware. '
                 'Empty string sets no master userid.')
@optgroup.option('--zaware-master-password', type=str, required=False,
                 # Property: 'zaware-master-pw'
                 help='The master password for IBM zAware. '
                 'Empty string sets no master password.')
@optgroup.option('--zaware-network-info', type=str, required=False,
                 help='The list of networks available to IBM zAware, in '
                 'YAML Flow Collection style. '
                 'Each list item must be a "zaware-network" object (described '
                 'in the HMC WS-API book). '
                 'A minimum of 1 network and a maximum of 100 networks are '
                 'permitted. The specified list fully replaces the existing '
                 'list in the HMC. '
                 'Example: --zaware-network-info "[{port: 444, ipaddr-type: '
                 'static, vlan-id: 53, static-ip-info: {type: ipv4, '
                 'ip-address: \'10.11.12.13\', prefix: 24}}]"')
@optgroup.option('--zaware-gateway-info', type=str, required=False,
                 help='The default gateway IP address information for IBM '
                 'zAware, as an "ip-info" object (described in the HMC WS-API '
                 'book) in YAML Flow Collection style. '
                 'An empty string removes the default gateway IP address. '
                 'Example: --zaware-gateway-info "{type: ipv4, ip-address: '
                 '\'10.11.12.13\', prefix: 24}"')
@optgroup.option('--zaware-dns-info', type=str, required=False,
                 help='The list of DNS IP addresses for IBM zAware, in '
                 'YAML Flow Collection style. '
                 'Each list item must be an "ip-info" object (described in the '
                 'HMC WS-API book). '
                 'A minimum of 0 addresses and a maximum of 2 addresses are '
                 'permitted. The specified list fully replaces the existing '
                 'list in the HMC. '
                 'Example: --zaware-dns-info "[{type: ipv4, ip-address: '
                 '\'10.11.12.13\', prefix: 24}]"')
@optgroup.group('SSC configuration (only applicable to SSC partitions)')
@optgroup.option('--ssc-host-name', type=str, required=False,
                 help='The hostname for the SSC appliance. '
                 'Empty string sets no hostname.')
@optgroup.option('--ssc-master-userid', type=str, required=False,
                 help='The master userid for the SSC appliance. '
                 'Empty string sets no master userid.')
@optgroup.option('--ssc-master-password', type=str, required=False,
                 # Property: 'ssc-master-pw'
                 help='The master password for the SSC appliance. '
                 'Empty string sets no master password.')
@optgroup.option('--ssc-boot-selection', required=False,
                 type=click.Choice(['installer', 'appliance']),
                 help='The boot selection for the SSC LPAR.')
@optgroup.option('--ssc-network-info', type=str, required=False,
                 help='The list of networks available to the SSC '
                 'appliance, in YAML Flow Collection style. '
                 'Each list item must be a "ssc-network" object (described '
                 'in the HMC WS-API book). '
                 'A minimum of 1 network and a maximum of 100 networks are '
                 'permitted. The specified list fully replaces the existing '
                 'list in the HMC. '
                 'Example: --ssc-network-info "[{port: 444, ipaddr-type: '
                 'static, vlan-id: 53, static-ip-info: {type: ipv4, '
                 'ip-address: \'10.11.12.13\', prefix: 24}}]"')
@optgroup.option('--ssc-gateway-info', type=str, required=False,
                 help='The default gateway IP address information for the '
                 'SSC appliance, as an "ip-info" object (described in the '
                 'HMC WS-API book) in YAML Flow Collection style. '
                 'An empty string removes the default gateway IP address. '
                 'Example: --ssc-gateway-info "{type: ipv4, ip-address: '
                 '\'10.11.12.13\', prefix: 24}"')
@optgroup.option('--ssc-gateway-ipv6-info', type=str, required=False,
                 help='The default gateway IPv6 address information for '
                 'the SSC appliance, as an "ip-info" object (described in the '
                 'HMC WS-API book) in YAML Flow Collection style. '
                 'An empty string removes the default gateway IP address. '
                 'Example: --ssc-gateway-ipv6-info "{type: ipv6, ip-address: '
                 '\'10:11:12:13:14:15\', prefix: 24}"')
@optgroup.option('--ssc-dns-info', type=str, required=False,
                 help='The list of DNS IP addresses for the SSC appliance, '
                 'in YAML Flow Collection style. '
                 'Each list item must be an "ip-info" object (described in the '
                 'HMC WS-API book). '
                 'A minimum of 0 addresses and a maximum of 2 addresses are '
                 'permitted. The specified list fully replaces the existing '
                 'list in the HMC. '
                 'Example: --ssc-dns-info "[{type: ipv4, ip-address: '
                 '\'10.11.12.13\', prefix: 24}]"')
# TODO: SEPARATE assigned-crypto-domains Array of assigned-crypto-domain
#       objects - Specifies the crypto domains and their access modes to be
#       assigned to the LPAR once activated.
# TODO: SEPARATE assigned-cryptos — Array of assigned-crypto objects - Specifies
#       the crypto adapters to be assigned to the LPAR once activated.
# TODO: SEPARATE assigned-certificate-uris (c)(pc) Array of String/ URI - Array
#       of URIs referring to the certificates that are assigned to this image
#       activation profile, or an empty array if there are no assigned
#       certificates.
@click.pass_obj
def imageprofile_create(cmd_ctx, cpc, **options):
    """
    Create an image activation profile for a CPC (Only HMC 2.16 and later).

    The default values for any options not specified will be the corresponding
    property values of the default image activation profile (that is the
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
      * The command does not support defining the network-related properties
        for zAware and SSC.
    """
    cmd_ctx.execute_cmd(lambda: cmd_imageprofile_create(cmd_ctx, cpc, options))


@imageprofile_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('cpc', type=str, metavar='CPC')
@click.argument('imageprofile', type=str, metavar='IMAGEPROFILE')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the image activation '
              'profile.',
              prompt='Are you sure you want to delete this image activation '
              'profile ?')
@click.pass_obj
def imageprofile_delete(cmd_ctx, cpc, imageprofile):
    """
    Delete an image activation profile (Only HMC 2.16 and later).

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_imageprofile_delete(cmd_ctx, cpc, imageprofile))


@imageprofile_group.command('assign-certificate',
                            options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('cpc', type=str, metavar='CPC')
@click.argument('imageprofile', type=str, metavar='IMAGEPROFILE')
@click.option('--certificate', type=str, required=True,
              help='The name of the certificate.')
@click.pass_obj
def imageprofile_assign_certificate(cmd_ctx, cpc, imageprofile, **options):
    """
    Assign a certificate to an image activation profile (Only HMC 2.16 and
    later).

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_imageprofile_assign_certificate(
            cmd_ctx, cpc, imageprofile, options))


@imageprofile_group.command('unassign-certificate',
                            options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('cpc', type=str, metavar='CPC')
@click.argument('imageprofile', type=str, metavar='IMAGEPROFILE')
@click.option('--certificate', type=str, required=True,
              help='The name of the certificate.')
@click.pass_obj
def imageprofile_unassign_certificate(cmd_ctx, cpc, imageprofile, **options):
    """
    Unassign a certificate from an image activation profile (Only HMC 2.16 and
    later).

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_imageprofile_unassign_certificate(
            cmd_ctx, cpc, imageprofile, options))


def cmd_imageprofile_list(cmd_ctx, cpc_name, options):
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
            'operating-mode',
            'ipl-type',
            'workload-manager-enabled',
            'load-at-activation',
            'description',
        ])
    if options['uri']:
        show_list.extend([
            'element-uri',
        ])

    imageprofiles = []
    for cpc in cpcs:
        try:
            imageprofiles.extend(cpc.image_activation_profiles.list())
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)

        for imageprofile in imageprofiles:
            cpc = imageprofile.manager.parent
            additions['cpc'][imageprofile.uri] = cpc.name

    try:
        print_resources(
            cmd_ctx, imageprofiles, cmd_ctx.output_format, show_list,
            additions, all=options['all'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_imageprofile_show(cmd_ctx, cpc_name, imageprofile_name, options):
    # pylint: disable=missing-function-docstring,unused-argument

    client = zhmcclient.Client(cmd_ctx.session)
    imageprofile = find_imageprofile(
        cmd_ctx, client, cpc_name, imageprofile_name)

    try:
        imageprofile.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(imageprofile.properties)

    # Add artificial property 'parent-name'
    properties['parent-name'] = cpc_name

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def handle_special_imageprofile_options(cmd_ctx, org_options, properties):
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

    if org_options['absolute-cp-capping'] is not None:
        value = absolute_capping_value(
            cmd_ctx, org_options, 'absolute-cp-capping')
        properties['absolute-general-purpose-capping'] = value

    if org_options['absolute-ifl-capping'] is not None:
        value = absolute_capping_value(
            cmd_ctx, org_options, 'absolute-ifl-capping')
        properties['absolute-ifl-capping'] = value

    if org_options['absolute-zaap-capping'] is not None:
        value = absolute_capping_value(
            cmd_ctx, org_options, 'absolute-zaap-capping')
        properties['absolute-aap-capping'] = value

    if org_options['absolute-ziip-capping'] is not None:
        value = absolute_capping_value(
            cmd_ctx, org_options, 'absolute-ziip-capping')
        properties['absolute-ziip-capping'] = value

    if org_options['absolute-icf-capping'] is not None:
        value = absolute_capping_value(
            cmd_ctx, org_options, 'absolute-icf-capping')
        properties['absolute-icf-capping'] = value

    if org_options['zaware-host-name'] == '':
        properties['zaware-host-name'] = None
    if org_options['zaware-master-userid'] == '':
        properties['zaware-master-userid'] = None
    if org_options['zaware-master-password'] == '':
        properties['zaware-master-pw'] = None
    if org_options['zaware-network-info']:
        value = parse_yaml_flow_style(
            cmd_ctx, '--zaware-network-info',
            org_options['zaware-network-info'])
        properties['zaware-network-info'] = value
    if org_options['zaware-gateway-info'] == '':
        properties['zaware-gateway-info'] = None
    elif org_options['zaware-gateway-info']:
        value = parse_yaml_flow_style(
            cmd_ctx, '--zaware-gateway-info',
            org_options['zaware-gateway-info'])
        properties['zaware-gateway-info'] = value
    if org_options['zaware-dns-info']:
        value = parse_yaml_flow_style(
            cmd_ctx, '--zaware-dns-info', org_options['zaware-dns-info'])
        properties['zaware-dns-info'] = value

    if org_options['ssc-host-name'] == '':
        properties['ssc-host-name'] = None
    if org_options['ssc-master-userid'] == '':
        properties['ssc-master-userid'] = None
    if org_options['ssc-master-password'] == '':
        properties['ssc-master-pw'] = None
    if org_options['ssc-network-info']:
        value = parse_yaml_flow_style(
            cmd_ctx, '--ssc-network-info', org_options['ssc-network-info'])
        properties['ssc-network-info'] = value
    if org_options['ssc-gateway-info'] == '':
        properties['ssc-gateway-info'] = None
    elif org_options['ssc-gateway-info']:
        value = parse_yaml_flow_style(
            cmd_ctx, '--ssc-gateway-info', org_options['ssc-gateway-info'])
        properties['ssc-gateway-info'] = value
    if org_options['ssc-gateway-ipv6-info'] == '':
        properties['ssc-gateway-ipv6-info'] = None
    elif org_options['ssc-gateway-ipv6-info']:
        value = parse_yaml_flow_style(
            cmd_ctx, '--ssc-gateway-ipv6-info',
            org_options['ssc-gateway-ipv6-info'])
        properties['ssc-gateway-ipv6-info'] = value
    if org_options['ssc-dns-info']:
        value = parse_yaml_flow_style(
            cmd_ctx, '--ssc-dns-info', org_options['ssc-dns-info'])
        properties['ssc-dns-info'] = value


def cmd_imageprofile_update(cmd_ctx, cpc_name, imageprofile_name, options):
    # pylint: disable=missing-function-docstring
    # pylint: disable=unreachable

    client = zhmcclient.Client(cmd_ctx.session)
    imageprofile = find_imageprofile(
        cmd_ctx, client, cpc_name, imageprofile_name)

    name_map = {
        'partition-id': 'partition-identifier',
        'lpar-isolation': 'logical-partition-isolation-control',
        'load-address': 'ipl-address',
        'load-parameter': 'ipl-parameter',
        'os-load-parameters': 'os-specific-load-parameters',
        'store-status': 'store-status-indicator',
        'disk-partition-id': None,
        'wlm-enabled': 'workload-manager-enabled',

        'shared-cp-processors': 'number-shared-general-purpose-processors',
        'reserved-shared-cp-processors':
            'number-reserved-shared-general-purpose-processors',
        'initial-cp-processing-weight': 'initial-processing-weight',
        'minimum-cp-processing-weight': 'minimum-processing-weight',
        'maximum-cp-processing-weight': 'maximum-processing-weight',
        'cp-processing-weight-capped': 'initial-processing-weight-capped',
        'absolute-cp-capping': None,
        'dedicated-cp-processors':
            'number-dedicated-general-purpose-processors',

        'shared-ifl-processors': 'number-shared-ifl-processors',
        'reserved-shared-ifl-processors':
            'number-reserved-shared-ifl-processors',
        'initial-ifl-processing-weight': 'initial-ifl-processing-weight',
        'minimum-ifl-processing-weight': 'minimum-ifl-processing-weight',
        'maximum-ifl-processing-weight': 'maximum-ifl-processing-weight',
        'ifl-processing-weight-capped': 'initial-ifl-processing-weight-capped',
        'absolute-ifl-capping': None,
        'dedicated-ifl-processors': 'number-dedicated-ifl-processors',
        'reserved-dedicated-ifl-processors':
            'number-reserved-dedicated-ifl-processors',

        'shared-zaap-processors': 'number-shared-aap-processors',
        'reserved-shared-zaap-processors':
            'number-reserved-shared-aap-processors',
        'initial-zaap-processing-weight': 'initial-aap-processing-weight',
        'minimum-zaap-processing-weight': 'minimum-aap-processing-weight',
        'maximum-zaap-processing-weight': 'maximum-aap-processing-weight',
        'zaap-processing-weight-capped': 'initial-aap-processing-weight-capped',
        'absolute-zaap-capping': None,
        'dedicated-zaap-processors': 'number-dedicated-aap-processors',
        'reserved-dedicated-zaap-processors':
            'number-reserved-dedicated-aap-processors',

        'shared-ziip-processors': 'number-shared-ziip-processors',
        'reserved-shared-ziip-processors':
            'number-reserved-shared-ziip-processors',
        'initial-ziip-processing-weight': 'initial-ziip-processing-weight',
        'minimum-ziip-processing-weight': 'minimum-ziip-processing-weight',
        'maximum-ziip-processing-weight': 'maximum-ziip-processing-weight',
        'ziip-processing-weight-capped':
            'initial-ziip-processing-weight-capped',
        'absolute-ziip-capping': None,
        'dedicated-ziip-processors': 'number-dedicated-ziip-processors',
        'reserved-dedicated-ziip-processors':
            'number-reserved-dedicated-ziip-processors',

        'shared-icf-processors': 'number-shared-icf-processors',
        'reserved-shared-icf-processors':
            'number-reserved-shared-icf-processors',
        'initial-icf-processing-weight':
            'initial-internal-cf-processing-weight',
        'minimum-icf-processing-weight':
            'minimum-internal-cf-processing-weight',
        'maximum-icf-processing-weight':
            'maximum-internal-cf-processing-weight',
        'icf-processing-weight-capped':
            'initial-internal-cf-processing-weight-capped',
        'absolute-icf-capping': None,
        'dedicated-icf-processors': 'number-dedicated-icf-processors',
        'reserved-dedicated-icf-processors':
            'number-reserved-dedicated-icf-processors',

        'central-storage-origin': 'user-specified-central-storage-origin',
        'access-basic-cpu-counter': 'basic-cpu-counter-authorization-control',
        'access-problem-state-cpu-counter':
            'problem-state-cpu-counter-authorization-control',
        'access-crypto-activity-cpu-counter':
            'crypto-activity-cpu-counter-authorization-control',
        'access-extended-cpu-counter':
            'extended-cpu-counter-authorization-control',
        'access-coprocessor-cpu-counter':
            'coprocessor-cpu-counter-authorization-control',
        'access-diagnostic-sampling':
            'diagnostic-sampling-authorization-control',
        'access-basic-cpu-sampling': 'basic-cpu-sampling-authorization-control',
        'permit-aes-key-import': 'permit-aes-key-import-functions',
        'permit-des-key-import': 'permit-des-key-import-functions',
        'permit-ecc-key-import': 'permit-ecc-key-import-functions',
        'access-global-performance-data':
            'global-performance-data-authorization-control',
        'permit-global-iocds': 'io-configuration-authorization-control',
        'permit-cross-partition-authority':
            'cross-partition-authority-authorization-control',
        'permit-bcpii-send-commands': 'security-bcpii-send-commands',
        'permit-bcpii-receive-commands': 'security-bcpii-receive-commands',

        'zaware-master-password': 'zaware-master-pw',
        'zaware-network-info': None,
        'zaware-gateway-info': None,
        'zaware-dns-info': None,

        'ssc-master-password': 'ssc-master-pw',
        'ssc-network-info': None,
        'ssc-gateway-info': None,
        'ssc-gateway-ipv6-info': None,
        'ssc-dns-info': None,

        'bcpii-receive-partitions': 'security-bcpii-receive-partition-list',
        'time-offset-direction': 'time-offset-increase-decrease',
    }

    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    handle_special_imageprofile_options(cmd_ctx, org_options, properties)

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating image activation "
                   "profile '{ip}' for CPC '{c}'.".
                   format(ip=imageprofile_name, c=cpc_name))
        return

    try:
        imageprofile.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Image activation profile '{ip}' for CPC '{c}' has been "
               "updated.".format(ip=imageprofile_name, c=cpc_name))


def cmd_imageprofile_create(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring
    # pylint: disable=unreachable

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    name_map = {
        'name': 'profile-name',
        'partition-id': 'partition-identifier',
        'lpar-isolation': 'logical-partition-isolation-control',
        'load-address': 'ipl-address',
        'load-parameter': 'ipl-parameter',
        'os-load-parameters': 'os-specific-load-parameters',
        'store-status': 'store-status-indicator',
        'disk-partition-id': None,
        'wlm-enabled': 'workload-manager-enabled',

        'shared-cp-processors': 'number-shared-general-purpose-processors',
        'reserved-shared-cp-processors':
            'number-reserved-shared-general-purpose-processors',
        'initial-cp-processing-weight': 'initial-processing-weight',
        'minimum-cp-processing-weight': 'minimum-processing-weight',
        'maximum-cp-processing-weight': 'maximum-processing-weight',
        'cp-processing-weight-capped': 'initial-processing-weight-capped',
        'absolute-cp-capping': None,
        'dedicated-cp-processors':
            'number-dedicated-general-purpose-processors',

        'shared-ifl-processors': 'number-shared-ifl-processors',
        'reserved-shared-ifl-processors':
            'number-reserved-shared-ifl-processors',
        'initial-ifl-processing-weight': 'initial-ifl-processing-weight',
        'minimum-ifl-processing-weight': 'minimum-ifl-processing-weight',
        'maximum-ifl-processing-weight': 'maximum-ifl-processing-weight',
        'ifl-processing-weight-capped': 'initial-ifl-processing-weight-capped',
        'absolute-ifl-capping': None,
        'dedicated-ifl-processors': 'number-dedicated-ifl-processors',
        'reserved-dedicated-ifl-processors':
            'number-reserved-dedicated-ifl-processors',

        'shared-zaap-processors': 'number-shared-aap-processors',
        'reserved-shared-zaap-processors':
            'number-reserved-shared-aap-processors',
        'initial-zaap-processing-weight': 'initial-aap-processing-weight',
        'minimum-zaap-processing-weight': 'minimum-aap-processing-weight',
        'maximum-zaap-processing-weight': 'maximum-aap-processing-weight',
        'zaap-processing-weight-capped': 'initial-aap-processing-weight-capped',
        'absolute-zaap-capping': None,
        'dedicated-zaap-processors': 'number-dedicated-aap-processors',
        'reserved-dedicated-zaap-processors':
            'number-reserved-dedicated-aap-processors',

        'shared-ziip-processors': 'number-shared-ziip-processors',
        'reserved-shared-ziip-processors':
            'number-reserved-shared-ziip-processors',
        'initial-ziip-processing-weight': 'initial-ziip-processing-weight',
        'minimum-ziip-processing-weight': 'minimum-ziip-processing-weight',
        'maximum-ziip-processing-weight': 'maximum-ziip-processing-weight',
        'ziip-processing-weight-capped':
            'initial-ziip-processing-weight-capped',
        'absolute-ziip-capping': None,
        'dedicated-ziip-processors': 'number-dedicated-ziip-processors',
        'reserved-dedicated-ziip-processors':
            'number-reserved-dedicated-ziip-processors',

        'shared-icf-processors': 'number-shared-icf-processors',
        'reserved-shared-icf-processors':
            'number-reserved-shared-icf-processors',
        'initial-icf-processing-weight':
            'initial-internal-cf-processing-weight',
        'minimum-icf-processing-weight':
            'minimum-internal-cf-processing-weight',
        'maximum-icf-processing-weight':
            'maximum-internal-cf-processing-weight',
        'icf-processing-weight-capped':
            'initial-internal-cf-processing-weight-capped',
        'absolute-icf-capping': None,
        'dedicated-icf-processors': 'number-dedicated-icf-processors',
        'reserved-dedicated-icf-processors':
            'number-reserved-dedicated-icf-processors',

        'central-storage-origin': 'user-specified-central-storage-origin',
        'access-basic-cpu-counter': 'basic-cpu-counter-authorization-control',
        'access-problem-state-cpu-counter':
            'problem-state-cpu-counter-authorization-control',
        'access-crypto-activity-cpu-counter':
            'crypto-activity-cpu-counter-authorization-control',
        'access-extended-cpu-counter':
            'extended-cpu-counter-authorization-control',
        'access-coprocessor-cpu-counter':
            'coprocessor-cpu-counter-authorization-control',
        'access-diagnostic-sampling':
            'diagnostic-sampling-authorization-control',
        'access-basic-cpu-sampling': 'basic-cpu-sampling-authorization-control',
        'permit-aes-key-import': 'permit-aes-key-import-functions',
        'permit-des-key-import': 'permit-des-key-import-functions',
        'permit-ecc-key-import': 'permit-ecc-key-import-functions',
        'access-global-performance-data':
            'global-performance-data-authorization-control',
        'permit-global-iocds': 'io-configuration-authorization-control',
        'permit-cross-partition-authority':
            'cross-partition-authority-authorization-control',
        'permit-bcpii-send-commands': 'security-bcpii-send-commands',
        'permit-bcpii-receive-commands': 'security-bcpii-receive-commands',

        'zaware-master-password': 'zaware-master-pw',
        'zaware-network-info': None,
        'zaware-gateway-info': None,
        'zaware-dns-info': None,

        'ssc-master-password': 'ssc-master-pw',
        'ssc-network-info': None,
        'ssc-gateway-info': None,
        'ssc-gateway-ipv6-info': None,
        'ssc-dns-info': None,

        'bcpii-receive-partitions': 'security-bcpii-receive-partition-list',
        'time-offset-direction': 'time-offset-increase-decrease',
    }

    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    handle_special_imageprofile_options(cmd_ctx, org_options, properties)

    try:
        new_imageprofile = cpc.image_activation_profiles.create(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("New imageprofile '{ip}' for CPC '{c}' has been created.".
               format(ip=new_imageprofile.properties['name'], c=cpc_name))


def cmd_imageprofile_delete(cmd_ctx, cpc_name, imageprofile_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    imageprofile = find_imageprofile(
        cmd_ctx, client, cpc_name, imageprofile_name)

    try:
        imageprofile.delete()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Image activation profile '{ip}' for CPC '{c}' has been "
               "deleted.".format(ip=imageprofile_name, c=cpc_name))


def cmd_imageprofile_assign_certificate(
        cmd_ctx, cpc_name, imageprofile_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    imageprofile = find_imageprofile(
        cmd_ctx, client, cpc_name, imageprofile_name)

    cert_name = options['certificate']
    cert = find_certificate(cmd_ctx, client, cert_name)

    try:
        imageprofile.assign_certificate(cert)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Certificate '{cert}' was assigned to image activation "
               "profile '{ip}' for CPC '{c}.".
               format(cert=cert_name, ip=imageprofile_name, c=cpc_name))


def cmd_imageprofile_unassign_certificate(
        cmd_ctx, cpc_name, imageprofile_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    imageprofile = find_imageprofile(
        cmd_ctx, client, cpc_name, imageprofile_name)

    cert_name = options['certificate']
    cert = find_certificate(cmd_ctx, client, cert_name)

    try:
        imageprofile.unassign_certificate(cert)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Certificate '{cert}' was unassigned from image activation "
               "profile '{ip}' for CPC '{c}.".
               format(cert=cert_name, ip=imageprofile_name, c=cpc_name))
