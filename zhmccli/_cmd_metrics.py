# Copyright 2017-2019 IBM Corp. All Rights Reserved.
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
Commands for metrics.
"""

from __future__ import absolute_import

import time
from collections import OrderedDict
import json
from tabulate import tabulate
import click

import zhmcclient
from .zhmccli import cli
from ._helper import COMMAND_OPTIONS_METAVAR, TABLE_FORMATS, \
    click_exception, InvalidOutputFormatError


# The number of seconds the client anticipates will elapse between Get
# Metrics calls against this context. The minimum accepted value is 15.
MIN_ANTICIPATED_FREQUENCY = 15

# Max number of retries in get_metrics() to obtain metrics data
GET_METRICS_MAX_RETRIES = 8

# Time in seconds between retries in get_metrics() to obtain metrics data
GET_METRICS_RETRY_TIME = 2

# Debug control: Print MetricsResponse string
DEBUG_METRICS_RESPONSE = False


def wait_for_metrics(metric_context, metric_groups):
    """
    Repeat the retrieval of the metrics of a metrics context until at least one
    of the specified metric group names has data.

    Returns the MetricGroupValues object for the metric group that has data.
    """
    retries = 0
    mg_values = None
    while mg_values is None:
        mr_str = metric_context.get_metrics()
        mr = zhmcclient.MetricsResponse(metric_context, mr_str)
        for _mg_values in mr.metric_group_values:
            if _mg_values.name in metric_groups:
                mg_values = _mg_values
                if DEBUG_METRICS_RESPONSE:
                    print("Debug: MetricsResponse:")
                    print(mr_str)
                break
        if mg_values is None:
            if retries > GET_METRICS_MAX_RETRIES:
                return None
            time.sleep(GET_METRICS_RETRY_TIME)  # avoid hot spin loop
            retries += 1
    return mg_values


def print_object_values(
        cmd_ctx, object_values_list, metric_group_definition, resource_classes,
        output_format, transposed):
    """
    Print a metric group for a list of resources in the desired output format.
    """
    if output_format in TABLE_FORMATS:
        if output_format == 'table':
            output_format = 'psql'
        print_object_values_as_table(
            cmd_ctx, object_values_list, metric_group_definition,
            resource_classes, output_format, transposed)
    elif output_format == 'json':
        print_object_values_as_json(
            cmd_ctx, object_values_list, metric_group_definition)
    else:
        raise InvalidOutputFormatError(output_format)


def print_object_values_as_table(
        cmd_ctx, object_values_list, metric_group_definition, resource_classes,
        table_format, transposed):
    """
    Print a list of object values in a tabular output format.
    """

    if object_values_list:
        metric_definitions = metric_group_definition.metric_definitions
        sorted_metric_names = [md.name for md in
                               sorted(metric_definitions.values(),
                                      key=lambda md: md.index)]

    table = []
    headers = []
    for i, ov in enumerate(object_values_list):

        row = []

        # Add resource names up to the CPC
        res = ov.resource
        while res:
            if i == 0:
                name_prop = res.manager.class_name + '-name'
                headers.insert(0, name_prop)
            row.insert(0, res.name)
            res = res.manager.parent  # CPC has None as parent

        # Add the metric values
        for name in sorted_metric_names:
            if i == 0:
                m_def = metric_definitions[name]
                header_str = name
                if m_def.unit:
                    header_str += u" [{u}]".format(u=m_def.unit)
                headers.append(header_str)
            value = ov.metrics[name]
            row.append(value)

        table.append(row)

    # Sort the table by the resource name columns
    n_sort_cols = len(resource_classes)
    table = sorted(table, key=lambda row: row[0:n_sort_cols])

    if transposed:
        table.insert(0, headers)
        table = [list(col) for col in zip(*table)]
        headers = []

    cmd_ctx.spinner.stop()
    if not table:
        click.echo("No {rc} resources with metrics data for metric group "
                   "'{mg}'.".
                   format(rc=metric_group_definition.resource_class,
                          mg=metric_group_definition.name))
    else:
        click.echo(tabulate(table, headers, tablefmt=table_format))


def print_object_values_as_json(
        cmd_ctx, object_values_list, metric_group_definition):
    """
    Print a list of object values in JSON output format.
    """

    if object_values_list:
        metric_definitions = metric_group_definition.metric_definitions
        sorted_metric_names = [md.name for md in
                               sorted(metric_definitions.values(),
                                      key=lambda md: md.index)]

    json_obj = []
    for ov in object_values_list:

        resource_obj = OrderedDict()

        # Add resource names up to the CPC
        res = ov.resource
        while res:
            name_prop = res.manager.class_name + '-name'
            resource_obj[name_prop] = res.name
            res = res.manager.parent  # CPC has None as parent

        # Add the metric values
        for name in sorted_metric_names:
            m_def = metric_definitions[name]
            value = ov.metrics[name]
            resource_obj[name] = OrderedDict(value=value, unit=m_def.unit)

        json_obj.append(resource_obj)

    json_str = json.dumps(json_obj)
    cmd_ctx.spinner.stop()
    click.echo(json_str)


def get_metric_values(client, metric_groups, resource_filter):
    """
    Retrieve and filter metric values of the specified metric groups.

    Parameters:

      client (Client): Client connected to the target HMC.

      metric_groups (string or list of strings):
        Name of the metric group(s) to be retrieved and printed.
        If more than one metrics group is specified, they must all be for the
        same resource class.

      resource_filter (list):
        Filter to narrow down the resources for which metrics are printed.
        This is a list ordered by parent resources first. Each list item is a
        tuple(class, name) where `class` is the resource class (e.g. 'cpc') and
        `name` is the resource name or `None` (for no filtering by that
        resource class). Valid combinations of resource classes are:

        * Empty list: No filter in place.
        * 'cpc': Only this CPC.
        * 'cpc','partition': Only this partition in this CPC.
        * 'cpc','logical-partition': Only this LPAR in this CPC.
        * 'cpc','adapter': Only this adapter in this CPC.
        * 'cpc','partition','nic': Only this NIC in this partition in this CPC.

    Returns:
      tuple (list(mo_values), mg_def), with:
      - mo_values (zhmcclient.MetricObjectValues): Metric values
      - mg_def (zhmcclient.MetricGroupDefinition): Metric group definition
        for these metric values
    """

    if not isinstance(metric_groups, (list, tuple)):
        metric_groups = [metric_groups]

    properties = {
        'anticipated-frequency-seconds': MIN_ANTICIPATED_FREQUENCY,
        'metric-groups': metric_groups,
    }
    mc = client.metrics_contexts.create(properties)
    mg_values = wait_for_metrics(mc, metric_groups)
    filtered_object_values = []  # of MetricObjectValues

    if not mg_values:

        mg_name = metric_groups[0]  # just pick any
        # TODO: Change this to be public in zhmcclient
        # pylint: disable=protected-access
        res_class = zhmcclient._metrics._resource_class_from_group(mg_name)
        mg_def = zhmcclient.MetricGroupDefinition(
            name=mg_name, resource_class=res_class, metric_definitions=[])

    else:

        mg_def = mc.metric_group_definitions[mg_values.name]

        filter_cpc = None
        filter_partition = None
        filter_lpar = None
        filter_adapter = None
        filter_nic = None
        for r_class, r_name in resource_filter:
            if r_class == 'cpc' and r_name:
                filter_cpc = client.cpcs.find(name=r_name)
            elif r_class == 'partition' and r_name:
                assert filter_cpc
                filter_partition = filter_cpc.partitions.find(name=r_name)
            elif r_class == 'logical-partition' and r_name:
                assert filter_cpc
                filter_lpar = filter_cpc.lpars.find(name=r_name)
            elif r_class == 'adapter' and r_name:
                assert filter_cpc
                filter_adapter = filter_cpc.adapters.find(name=r_name)
            elif r_class == 'nic' and r_name:
                assert filter_partition
                filter_nic = filter_partition.nics.find(name=r_name)

        resource_class = mg_def.resource_class

        for ov in mg_values.object_values:
            included = False
            if resource_class == 'cpc':
                if not filter_cpc:
                    included = True
                elif ov.resource_uri == filter_cpc.uri:
                    included = True
            elif resource_class == 'partition':
                if not filter_cpc:
                    included = True
                elif ov.resource.manager.cpc.uri == filter_cpc.uri:
                    if not filter_partition:
                        included = True
                    elif ov.resource_uri == filter_partition.uri:
                        included = True
            elif resource_class == 'logical-partition':
                if not filter_cpc:
                    included = True
                elif ov.resource.manager.cpc.uri == filter_cpc.uri:
                    if not filter_lpar:
                        included = True
                    elif ov.resource_uri == filter_lpar.uri:
                        included = True
            elif resource_class == 'adapter':
                if not filter_cpc:
                    included = True
                elif ov.resource.manager.cpc.uri == filter_cpc.uri:
                    if not filter_adapter:
                        included = True
                    elif ov.resource_uri == filter_adapter.uri:
                        included = True
            elif resource_class == 'nic':
                if not filter_cpc:
                    included = True
                elif ov.resource.manager.partition.manager.cpc.uri == \
                        filter_cpc.uri:
                    if not filter_partition:
                        included = True
                    elif ov.resource.manager.partition.uri == \
                            filter_partition.uri:
                        if not filter_nic:
                            included = True
                        elif ov.resource_uri == filter_nic.uri:
                            included = True
            else:
                raise ValueError(
                    "Invalid resource class: {rc}".format(rc=resource_class))

            if included:
                filtered_object_values.append(ov)

    mc.delete()

    return filtered_object_values, mg_def


def print_metric_groups(cmd_ctx, client, metric_groups, resource_filter):
    """
    Retrieve and print metric group(s).
    """
    mo_values, mg_def = get_metric_values(
        client, metric_groups, resource_filter)
    resource_classes = [f[0] for f in resource_filter]
    print_object_values(
        cmd_ctx, mo_values, mg_def, resource_classes, cmd_ctx.output_format,
        cmd_ctx.transpose)


@cli.group('metrics', options_metavar=COMMAND_OPTIONS_METAVAR)
def metrics_group():
    """
    Command group for reporting metrics.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@metrics_group.command('cpc', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='[CPC]', required=False)
@click.pass_obj
def metrics_cpc(cmd_ctx, cpc, **options):
    """
    Report usage overview metrics for CPCs.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_metrics_cpc(cmd_ctx, cpc, options))


@metrics_group.command('partition', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='[CPC]', required=False)
@click.argument('PARTITION', type=str, metavar='[PARTITION]', required=False)
@click.pass_obj
def metrics_partition(cmd_ctx, cpc, partition, **options):
    """
    Report usage metrics for active partitions of CPCs in DPM mode.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_metrics_partition(cmd_ctx, cpc, partition, options))


@metrics_group.command('lpar', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='[CPC]', required=False)
@click.argument('LPAR', type=str, metavar='[LPAR]', required=False)
@click.pass_obj
def metrics_lpar(cmd_ctx, cpc, lpar, **options):
    """
    Report usage metrics for active LPARs of CPCs in classic mode.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_metrics_lpar(cmd_ctx, cpc, lpar, options))


@metrics_group.command('adapter', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='[CPC]', required=False)
@click.argument('ADAPTER', type=str, metavar='[ADAPTER]', required=False)
@click.pass_obj
def metrics_adapter(cmd_ctx, cpc, adapter, **options):
    """
    Report usage metrics for active adapters of CPCs in DPM mode.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_metrics_adapter(cmd_ctx, cpc, adapter, options))


@metrics_group.command('channel', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='[CPC]', required=False)
@click.pass_obj
def metrics_channel(cmd_ctx, cpc, **options):
    """
    Report usage metrics for all channels of CPCs in classic mode.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_metrics_channel(cmd_ctx, cpc, options))


@metrics_group.command('env', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='[CPC]', required=False)
@click.pass_obj
def metrics_env(cmd_ctx, cpc, **options):
    """
    Report environmental and power consumption metrics for CPCs.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_metrics_env(cmd_ctx, cpc, options))


@metrics_group.command('proc', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='[CPC]', required=False)
@click.pass_obj
def metrics_proc(cmd_ctx, cpc, **options):
    """
    Report processor usage metrics for CPCs.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_metrics_proc(cmd_ctx, cpc, options))


@metrics_group.command('crypto', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='[CPC]', required=False)
@click.pass_obj
def metrics_crypto(cmd_ctx, cpc, **options):
    """
    Report usage metrics for all active Crypto Express adapters of CPCs.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_metrics_crypto(cmd_ctx, cpc, options))


@metrics_group.command('flash', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='[CPC]', required=False)
@click.pass_obj
def metrics_flash(cmd_ctx, cpc, **options):
    """
    Report usage metrics for all active Flash Express adapters of CPCs.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_metrics_flash(cmd_ctx, cpc, options))


@metrics_group.command('roce', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='[CPC]', required=False)
@click.pass_obj
def metrics_roce(cmd_ctx, cpc, **options):
    """
    Report usage metrics for all active RoCE adapters of CPCs.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_metrics_roce(cmd_ctx, cpc, options))


@metrics_group.command('networkport', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='[CPC]', required=False)
@click.argument('ADAPTER', type=str, metavar='[ADAPTER]', required=False)
@click.pass_obj
def metrics_networkport(cmd_ctx, cpc, adapter, **options):
    """
    Report usage metrics for the ports of network adapters of CPCs in DPM mode.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_metrics_networkport(cmd_ctx, cpc, adapter, options))


@metrics_group.command('nic', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='[CPC]', required=False)
@click.argument('PARTITION', type=str, metavar='[PARTITION]', required=False)
@click.argument('NIC', type=str, metavar='[NIC]', required=False)
@click.pass_obj
def metrics_nic(cmd_ctx, cpc, partition, nic, **options):
    """
    Report usage metrics for the NICs of partitions of CPCs in DPM mode.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_metrics_nic(cmd_ctx, cpc, partition, nic, options))


def cmd_metrics_cpc(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring,unused-argument

    try:
        client = zhmcclient.Client(cmd_ctx.session)

        metric_groups = ['dpm-system-usage-overview', 'cpc-usage-overview']
        resource_filter = [
            ('cpc', cpc_name),
        ]
        print_metric_groups(cmd_ctx, client, metric_groups, resource_filter)

    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_metrics_partition(cmd_ctx, cpc_name, partition_name, options):
    # pylint: disable=missing-function-docstring,unused-argument

    try:
        client = zhmcclient.Client(cmd_ctx.session)

        metric_group = 'partition-usage'
        resource_filter = [
            ('cpc', cpc_name),
            ('partition', partition_name),
        ]
        print_metric_groups(cmd_ctx, client, metric_group, resource_filter)

    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_metrics_lpar(cmd_ctx, cpc_name, lpar_name, options):
    # pylint: disable=missing-function-docstring,unused-argument

    try:
        client = zhmcclient.Client(cmd_ctx.session)

        metric_group = 'logical-partition-usage'
        resource_filter = [
            ('cpc', cpc_name),
            ('logical-partition', lpar_name),
        ]
        print_metric_groups(cmd_ctx, client, metric_group, resource_filter)

    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_metrics_adapter(cmd_ctx, cpc_name, adapter_name, options):
    # pylint: disable=missing-function-docstring,unused-argument

    try:
        client = zhmcclient.Client(cmd_ctx.session)

        metric_group = 'adapter-usage'
        resource_filter = [
            ('cpc', cpc_name),
            ('adapter', adapter_name),
        ]
        print_metric_groups(cmd_ctx, client, metric_group, resource_filter)

    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_metrics_channel(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring,unused-argument

    try:
        client = zhmcclient.Client(cmd_ctx.session)

        metric_group = 'channel-usage'
        resource_filter = [
            ('cpc', cpc_name),
        ]
        print_metric_groups(cmd_ctx, client, metric_group, resource_filter)

    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_metrics_env(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring,unused-argument

    try:
        client = zhmcclient.Client(cmd_ctx.session)

        metric_group = 'zcpc-environmentals-and-power'
        resource_filter = [
            ('cpc', cpc_name),
        ]
        print_metric_groups(cmd_ctx, client, metric_group, resource_filter)

    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_metrics_proc(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring,unused-argument

    try:
        client = zhmcclient.Client(cmd_ctx.session)

        metric_group = 'zcpc-processor-usage'
        resource_filter = [
            ('cpc', cpc_name),
        ]
        print_metric_groups(cmd_ctx, client, metric_group, resource_filter)

    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_metrics_crypto(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring,unused-argument

    try:
        client = zhmcclient.Client(cmd_ctx.session)

        metric_group = 'crypto-usage'
        resource_filter = [
            ('cpc', cpc_name),
        ]
        print_metric_groups(cmd_ctx, client, metric_group, resource_filter)

    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_metrics_flash(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring,unused-argument

    try:
        client = zhmcclient.Client(cmd_ctx.session)

        metric_group = 'flash-memory-usage'
        resource_filter = [
            ('cpc', cpc_name),
        ]
        print_metric_groups(cmd_ctx, client, metric_group, resource_filter)

    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_metrics_roce(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring,unused-argument

    try:
        client = zhmcclient.Client(cmd_ctx.session)

        metric_group = 'roce-usage'
        resource_filter = [
            ('cpc', cpc_name),
        ]
        print_metric_groups(cmd_ctx, client, metric_group, resource_filter)

    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_metrics_networkport(cmd_ctx, cpc_name, adapter_name, options):
    # pylint: disable=missing-function-docstring,unused-argument

    try:
        client = zhmcclient.Client(cmd_ctx.session)

        metric_group = 'network-physical-adapter-port'
        resource_filter = [
            ('cpc', cpc_name),
            ('adapter', adapter_name),
        ]
        print_metric_groups(cmd_ctx, client, metric_group, resource_filter)

    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_metrics_nic(cmd_ctx, cpc_name, partition_name, nic_name, options):
    # pylint: disable=missing-function-docstring,unused-argument

    try:
        client = zhmcclient.Client(cmd_ctx.session)

        metric_group = 'partition-attached-network-interface'
        resource_filter = [
            ('cpc', cpc_name),
            ('partition', partition_name),
            ('nic', nic_name),
        ]
        print_metric_groups(cmd_ctx, client, metric_group, resource_filter)

    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
