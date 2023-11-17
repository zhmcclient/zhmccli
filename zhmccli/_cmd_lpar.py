# Copyright 2016,2019 IBM Corp. All Rights Reserved.
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
from click_option_group import optgroup

import zhmcclient
from .zhmccli import cli, CONSOLE_LOGGER_NAME
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    part_console, click_exception, add_options, LIST_OPTIONS, TABLE_FORMATS, \
    hide_property, ASYNC_TIMEOUT_OPTIONS, API_VERSION_HMC_2_14_0, \
    absolute_capping_value, parse_yaml_flow_style
from ._cmd_cpc import find_cpc
from ._cmd_certificates import find_certificate


def find_lpar(cmd_ctx, client, cpc_name, lpar_name):
    """
    Find an LPAR by name and return its resource object.
    """
    if client.version_info() >= API_VERSION_HMC_2_14_0:
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

    The following properties are shown in addition to those returned by the HMC:

    \b
      - 'parent-name' - Name of the parent CPC.

    In table output formats, the following properties are hidden by default
    but can be shown by using the --all option:

    \b
      - program-status-word-information

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_lpar_show(cmd_ctx, cpc, lpar, options))


@lpar_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('LPAR', type=str, metavar='LPAR')
@optgroup.group('General options')
@optgroup.option('--acceptable-status', type=str, required=False,
                 help='The new set of acceptable operational status values, '
                 'as a comma-separated list. The empty string specifies an '
                 'empty list.')
@optgroup.option('--next-activation-profile', type=str, required=False,
                 # Property: 'next-activation-profile-name'
                 help='The new name of the new next image or load activation '
                 'profile.')
@optgroup.group('CPU configuration')
@optgroup.option('--wlm-enabled', type=bool, required=False,
                 # Property: 'workload-manager-enabled'
                 help='The new indicator for enabling z/OS Workload Manager. '
                 'If True, z/OS Workload Manager is allowed to change '
                 'processing weight related properties of the LPAR after '
                 'activation.')
@optgroup.option('--defined-capacity', type=int, required=False,
                 help='The new defined capacity of the LPAR '
                 '(in MSU/h). This specifies how much capacity the LPAR is to '
                 'be managed to by z/OS Workload Manager for the purpose of '
                 'software pricing. 0 means that no defined capacity is '
                 'specified for this LPAR.')
#
@optgroup.option('--shared-cp-processors', type=int, required=False,
                 # Property: 'number-general-purpose-cores'
                 help='The new number of shared CP (general purpose) '
                 'processors to be allocated to the LPAR at activation.')
@optgroup.option('--reserved-shared-cp-processors', type=int, required=False,
                 # Property: 'number-reserved-general-purpose-cores'
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
                 # Property: 'absolute-processing-capping'
                 #           -> absolute-capping object
                 help='The new value for absolute CP (general purpose) '
                 'processor capping. A numeric value prevents the partition '
                 'from using any more than the specified number of physical '
                 'CP processors. An empty string disables absolute CP '
                 'processor capping.')
# Note: The LPAR object has no dedicated CP processor properties
#       'number-dedicated-cp-processors' and
#       'number-reserved-dedicated-cp-processors'
#
@optgroup.option('--shared-ifl-processors', type=int, required=False,
                 # Property: 'number-ifl-cores'
                 help='The new number of shared IFL (Integrated Facility for '
                 'Linux) processors to be allocated to the LPAR at activation.')
@optgroup.option('--reserved-shared-ifl-processors', type=int, required=False,
                 # Property: 'number-reserved-ifl-cores'
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
# Note: The LPAR object has no dedicated IFL processor properties
#       'number-dedicated-ifl-processors' and
#       'number-reserved-dedicated-ifl-processors'
#
@optgroup.option('--shared-zaap-processors', type=int, required=False,
                 # Property: 'number-aap-cores'
                 help='The new number of shared zAAP (z Application Assist '
                 'Processor) processors to be allocated to the LPAR at '
                 'activation.')
@optgroup.option('--reserved-shared-zaap-processors', type=int, required=False,
                 # Property: 'number-reserved-aap-cores'
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
# Note: The LPAR object has no dedicated zAAP processor properties
#       'number-dedicated-aap-processors' and
#       'number-reserved-dedicated-aap-processors'
#
@optgroup.option('--shared-ziip-processors', type=int, required=False,
                 # Property: 'number-ziip-cores'
                 help='The new number of shared zIIP (z Integrated '
                 'Information Processor) processors to be allocated to the '
                 'LPAR at activation.')
@optgroup.option('--reserved-shared-ziip-processors', type=int, required=False,
                 # Property: 'number-reserved-ziip-cores'
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
# Note: The LPAR object has no dedicated zIIP processor properties
#       'number-dedicated-ziip-processors' and
#       'number-reserved-dedicated-ziip-processors'
#
@optgroup.option('--shared-icf-processors', type=int, required=False,
                 # Property: 'number-icf-cores'
                 help='The new number of shared ICF (Integrated Coupling '
                 'Facility) processors to be allocated to the LPAR at '
                 'activation.')
@optgroup.option('--reserved-shared-icf-processors', type=int, required=False,
                 # Property: 'number-reserved-icf-cores'
                 help='The new number of shared ICF (Integrated Coupling '
                 'Facility) processors to be reserved for the '
                 'LPAR, which can be dynamically configured after activation.')
@optgroup.option('--initial-icf-processing-weight', type=int, required=False,
                 # Property: 'initial-cf-processing-weight'
                 help='The new initial processing weight for ICF (Integrated '
                 'Coupling Facility) processors (1-999).')
@optgroup.option('--minimum-icf-processing-weight', type=int, required=False,
                 # Property: 'minimum-cf-processing-weight'
                 help='The new minimum processing weight for ICF (Integrated '
                 'Coupling Facility) processors (0-999).')
@optgroup.option('--maximum-icf-processing-weight', type=int, required=False,
                 # Property: 'maximum-cf-processing-weight'
                 help='The new maximum processing weight for ICF (Integrated '
                 'Coupling Facility) processors (0-999).')
@optgroup.option('--icf-processing-weight-capped', type=bool, required=False,
                 # Property: 'initial-cf-processing-weight-capped'
                 help='The new indicator for whether the ICF (Integrated '
                 'Coupling Facility) processing weight is capped. '
                 'If True, the processing weight is an upper limit. If False, '
                 'the processing weight is a target that can be exceeded if '
                 'excess ICF processor resources are available.')
@optgroup.option('--absolute-icf-capping', type=str, metavar='FLOAT',
                 required=False,
                 # Property: 'absolute-cf-capping'
                 #           -> absolute-capping object
                 help='The new value for absolute ICF (Integrated Coupling '
                 'Facility) processor capping. A numeric value '
                 'prevents the partition from using any more than the '
                 'specified number of physical ICF processors. An empty '
                 'string disables absolute ICF processor capping.')
# Note: The LPAR object has no dedicated ICF processor properties
#       'number-dedicated-icf-processors' and
#       'number-reserved-dedicated-icf-processors'
@optgroup.group('zAware configuration (only applicable to zAware LPARs)')
@optgroup.option('--zaware-host-name', type=str, required=False,
                 help='The new hostname for IBM zAware. '
                 'Empty string sets no hostname.')
@optgroup.option('--zaware-master-userid', type=str, required=False,
                 help='The new master userid for IBM zAware. '
                 'Empty string sets no master userid.')
@optgroup.option('--zaware-master-password', '--zaware-master-pw', type=str,
                 # Property: 'zaware-master-pw'
                 required=False,
                 help='The new master password for IBM zAware. '
                 'Empty string sets no master password. '
                 'Use of the --zaware-master-pw option is deprecated; use the '
                 '--zaware-master-password option instead.')
# TODO: Change zAware master password option to ask for password
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
@optgroup.group('SSC configuration (only applicable to SSC LPARs and only '
                'supported on z13)')
@optgroup.option('--ssc-host-name', type=str, required=False,
                 help='The new hostname for the SSC appliance. '
                 'Empty string sets no hostname.')
@optgroup.option('--ssc-master-userid', type=str, required=False,
                 help='The new master userid for the SSC appliance. '
                 'Empty string sets no master userid.')
@optgroup.option('--ssc-master-password', '--ssc-master-pw', type=str,
                 # Property: 'ssc-master-pw'
                 required=False,
                 help='The new master password for the SSC appliance. '
                 'Empty string sets no master password. '
                 'Use of the --ssc-master-pw option is deprecated; use the '
                 '--ssc-master-password option instead.')
# TODO: Change SSC master password option to ask for password
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
@click.pass_obj
def lpar_update(cmd_ctx, cpc, lpar, **options):
    """
    Update the properties of an LPAR.

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
      * The processor capping/sharing/weight related properties cannot be
        updated.
      * The network-related properties for zaware and ssc cannot be updated.
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


@lpar_group.command('start', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('LPAR', type=str, metavar='LPAR')
@click.option('--allow-status-exceptions', is_flag=True, required=False,
              help='Allow status "exceptions" as a valid end status.')
@add_options(ASYNC_TIMEOUT_OPTIONS)
@click.pass_obj
def lpar_start(cmd_ctx, cpc, lpar, **options):
    """
    Start the processors for processing instructions of an LPAR.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_lpar_start(cmd_ctx, cpc, lpar, options))


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


@lpar_group.command('reset-clear', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('LPAR', type=str, metavar='LPAR')
@click.option('--force', is_flag=True, required=False,
              help='Controls whether this command is permitted when the '
              'LPAR is in "operating" status.')
@click.option('--os-ipl-token', type=str, required=False,
              help='Applicable only to z/OS, this parameter requests that this '
              'operation only be performed if the provided value matches '
              'the current value of the os-ipl-token property of the LPAR.')
@click.option('--allow-status-exceptions', is_flag=True, required=False,
              help='Allow status "exceptions" as a valid end status.')
@add_options(ASYNC_TIMEOUT_OPTIONS)
@click.pass_obj
def lpar_reset_clear(cmd_ctx, cpc, lpar, **options):
    """
    Resets an LPAR and clears its memory.

    This includes clearing its pending interruptions, resetting its channel
    subsystem and resetting its processors, and clearing its memory, using the
    HMC operation "Reset Clear".

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_lpar_reset_clear(cmd_ctx, cpc, lpar,
                                                     options))


@lpar_group.command('reset-normal', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('LPAR', type=str, metavar='LPAR')
@click.option('--force', is_flag=True, required=False,
              help='Controls whether this command is permitted when the '
              'LPAR is in "operating" status.')
@click.option('--os-ipl-token', type=str, required=False,
              help='Applicable only to z/OS, this parameter requests that this '
              'operation only be performed if the provided value matches '
              'the current value of the os-ipl-token property of the LPAR.')
@click.option('--allow-status-exceptions', is_flag=True, required=False,
              help='Allow status "exceptions" as a valid end status.')
@add_options(ASYNC_TIMEOUT_OPTIONS)
@click.pass_obj
def lpar_reset_normal(cmd_ctx, cpc, lpar, **options):
    """
    Resets an LPAR without clearing its memory.

    This includes clearing its pending interruptions, resetting its channel
    subsystem and resetting its processors, using the HMC operation
    "Reset Normal".

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_lpar_reset_normal(cmd_ctx, cpc, lpar,
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


@lpar_group.command('assign-certificate',
                    options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('LPAR', type=str, metavar='LPAR')
@click.option('--certificate', type=str, required=True,
              help='The name of the certificate.')
@click.pass_obj
def lpar_assign_certificate(cmd_ctx, cpc, lpar, **options):
    """
    Assign a certificate to an LPAR.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_lpar_assign_certificate(cmd_ctx, cpc, lpar, options))


@lpar_group.command('unassign-certificate',
                    options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('LPAR', type=str, metavar='LPAR')
@click.option('--certificate', type=str, required=True,
              help='The name of the certificate.')
@click.pass_obj
def lpar_unassign_certificate(cmd_ctx, cpc, lpar, **options):
    """
    Unassign a certificate from an LPAR.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_lpar_unassign_certificate(cmd_ctx, cpc, lpar,
                                              options))


def cmd_lpar_list(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)

    if cpc_name:
        # Make sure a non-existing CPC is raised as error
        cpc = client.cpcs.find(name=cpc_name)
        lpars = cpc.lpars.list()
    elif client.version_info() >= API_VERSION_HMC_2_14_0:
        # This approach is faster than looping through the CPCs.
        # In addition, this approach supports users that do not have object
        # access permission to the parent CPC of the returned LPARs.
        lpars = client.consoles.console.list_permitted_lpars()
    else:
        lpars = []
        cpcs = client.cpcs.list()
        for cpc in cpcs:
            lpars.extend(cpc.lpars.list())
    # The default exception handling is sufficient for the above.

    if options['type']:
        click.echo("The --type option is deprecated and type information "
                   "is now always shown.")

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
            'status',
            'activation-mode',
            'os-type',
            'workload-manager-enabled',
            'description',
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

    # Add artificial property 'parent-name'
    properties['parent-name'] = cpc_name

    # Hide some long or deeply nested properties in table output formats.
    if not options['all'] and cmd_ctx.output_format in TABLE_FORMATS:
        hide_property(properties, 'program-status-word-information')

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def handle_special_lpar_options(cmd_ctx, org_options, properties):
    """
    Handle special update options (i.e. those that are set to
    None in the name_map). The options are taken from org_options and
    put into properties.
    """

    if org_options['acceptable-status'] is not None:
        status_list = org_options['acceptable-status'].split(',')
        status_list = [item for item in status_list if item]
        properties['acceptable-status'] = status_list

    if org_options['absolute-cp-capping'] is not None:
        value = absolute_capping_value(
            cmd_ctx, org_options, 'absolute-cp-capping')
        properties['absolute-processing-capping'] = value

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
        properties['absolute-cf-capping'] = value

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
    if org_options['ssc-dns-info']:
        value = parse_yaml_flow_style(
            cmd_ctx, '--ssc-dns-info', org_options['ssc-dns-info'])
        properties['ssc-dns-info'] = value


def cmd_lpar_update(cmd_ctx, cpc_name, lpar_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    lpar = find_lpar(cmd_ctx, client, cpc_name, lpar_name)

    name_map = {
        'next-activation-profile': 'next-activation-profile-name',
        'acceptable-status': None,
        'wlm-enabled': 'workload-manager-enabled',

        'shared-cp-processors': 'number-general-purpose-cores',
        'reserved-shared-cp-processors':
            'number-reserved-general-purpose-cores',
        'initial-cp-processing-weight': 'initial-processing-weight',
        'minimum-cp-processing-weight': 'minimum-processing-weight',
        'maximum-cp-processing-weight': 'maximum-processing-weight',
        'cp-processing-weight-capped': 'initial-processing-weight-capped',
        'absolute-cp-capping': None,

        'shared-ifl-processors': 'number-ifl-cores',
        'reserved-shared-ifl-processors': 'number-reserved-ifl-cores',
        'initial-ifl-processing-weight': 'initial-ifl-processing-weight',
        'minimum-ifl-processing-weight': 'minimum-ifl-processing-weight',
        'maximum-ifl-processing-weight': 'maximum-ifl-processing-weight',
        'ifl-processing-weight-capped': 'initial-ifl-processing-weight-capped',
        'absolute-ifl-capping': None,

        'shared-zaap-processors': 'number-aap-cores',
        'reserved-shared-zaap-processors': 'number-reserved-aap-cores',
        'initial-zaap-processing-weight': 'initial-aap-processing-weight',
        'minimum-zaap-processing-weight': 'minimum-aap-processing-weight',
        'maximum-zaap-processing-weight': 'maximum-aap-processing-weight',
        'zaap-processing-weight-capped': 'initial-aap-processing-weight-capped',
        'absolute-zaap-capping': None,

        'shared-ziip-processors': 'number-ziip-cores',
        'reserved-shared-ziip-processors': 'number-reserved-ziip-cores',
        'initial-ziip-processing-weight': 'initial-ziip-processing-weight',
        'minimum-ziip-processing-weight': 'minimum-ziip-processing-weight',
        'maximum-ziip-processing-weight': 'maximum-ziip-processing-weight',
        'ziip-processing-weight-capped':
            'initial-ziip-processing-weight-capped',
        'absolute-ziip-capping': None,

        'shared-icf-processors': 'number-icf-cores',
        'reserved-shared-icf-processors': 'number-reserved-icf-cores',
        'initial-icf-processing-weight': 'initial-cf-processing-weight',
        'minimum-icf-processing-weight': 'minimum-cf-processing-weight',
        'maximum-icf-processing-weight': 'maximum-cf-processing-weight',
        'icf-processing-weight-capped': 'initial-cf-processing-weight-capped',
        'absolute-icf-capping': None,

        'zaware-master-password': 'zaware-master-pw',
        'zaware-network-info': None,
        'zaware-gateway-info': None,
        'zaware-dns-info': None,

        'ssc-master-password': 'ssc-master-pw',
        'ssc-network-info': None,
        'ssc-gateway-info': None,
        'ssc-dns-info': None,
    }
    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    handle_special_lpar_options(cmd_ctx, org_options, properties)

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


def cmd_lpar_start(cmd_ctx, cpc_name, lpar_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    lpar = find_lpar(cmd_ctx, client, cpc_name, lpar_name)

    try:
        lpar.start(wait_for_completion=True, **options)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Starting of LPAR '{p}' is complete.".format(p=lpar_name))


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


def cmd_lpar_reset_clear(cmd_ctx, cpc_name, lpar_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    lpar = find_lpar(cmd_ctx, client, cpc_name, lpar_name)

    try:
        lpar.reset_clear(wait_for_completion=True, **options)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Reset clear of LPAR '{p}' is complete.".format(p=lpar_name))


def cmd_lpar_reset_normal(cmd_ctx, cpc_name, lpar_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    lpar = find_lpar(cmd_ctx, client, cpc_name, lpar_name)

    try:
        lpar.reset_normal(wait_for_completion=True, **options)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Reset normal of LPAR '{p}' is complete.".format(p=lpar_name))


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


def cmd_lpar_assign_certificate(cmd_ctx, cpc_name, lpar_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    lpar = find_lpar(cmd_ctx, client, cpc_name, lpar_name)

    cert_name = options['certificate']
    cert = find_certificate(cmd_ctx, client, cert_name)

    try:
        lpar.assign_certificate(cert)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Certificate '{cert}' was assigned to LPAR '{p}'.".
               format(cert=cert_name, p=lpar_name))


def cmd_lpar_unassign_certificate(cmd_ctx, cpc_name, lpar_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    lpar = find_lpar(cmd_ctx, client, cpc_name, lpar_name)

    cert_name = options['certificate']
    cert = find_certificate(cmd_ctx, client, cert_name)

    try:
        lpar.unassign_certificate(cert)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Certificate '{cert}' was unassigned from LPAR '{p}'.".
               format(cert=cert_name, p=lpar_name))
