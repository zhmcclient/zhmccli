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
Helper functions.
"""

from __future__ import absolute_import

import json
from collections import OrderedDict
import sys
import threading
import re
import jsonschema
import six
import click
import click_spinner
from tabulate import tabulate

import zhmcclient
import zhmcclient_mock

# Display of options in usage line
GENERAL_OPTIONS_METAVAR = '[GENERAL-OPTIONS]'
COMMAND_OPTIONS_METAVAR = '[COMMAND-OPTIONS]'

# File path of history file for interactive mode.
# If the file name starts with tilde (which is handled by the shell, not by
# the file system), it is properly expanded.
REPL_HISTORY_FILE = '~/.zhmc_history'

REPL_PROMPT = u'zhmc> '  # Must be Unicode

TABLE_FORMATS = ['table', 'plain', 'simple', 'psql', 'rst', 'mediawiki',
                 'html', 'latex']

LOG_DESTINATIONS = ['stderr', 'syslog', 'none']

LOG_LEVELS = ['error', 'warning', 'info', 'debug']

LOG_COMPONENTS = ['api', 'hmc', 'console', 'all']

SYSLOG_FACILITIES = ['user', 'local0', 'local1', 'local2', 'local3', 'local4',
                     'local5', 'local6', 'local7']

# Inner table format for each outer table format, when tables are nested for
# complex property types (arrays, nested objects). If a format is not mapped
# here, the outer table format will be used for the inner table.
# The table formats are the format indicators of the "tabulate" package (not
# the formats supported by zhmccli). In addition, the inner table formats may
# be 'repr' which indicates to use the repr() string on the input data for
# the inner table.
INNER_TABLE_FORMAT = {
    'psql': 'plain',
    'simple': 'plain',
    'rst': 'grid',
    'grid': 'grid',
    'latex': 'repr',
    # TODO on latex: Use latex_raw once "tabulate" can better control escaping
    # mediawiki: uses nested mediawiki tables
    # html: uses nested html tables
}

# Common Click options for list commands
LIST_OPTIONS = [
    click.option('--names-only', is_flag=True, required=False,
                 help='Restrict properties shown to only the names of the '
                 'resource and its parents'),
    click.option('--uri', is_flag=True, required=False,
                 help='Add the resource URI to the properties shown'),
    click.option('--all', is_flag=True, required=False,
                 help='Show all properties'),
]

# Click options for email notification (used for storagegroup and storagevolume
# commands)
EMAIL_OPTIONS = [
    click.option('--email-to-address', type=str, required=False, multiple=True,
                 help='An email address for the people that are to be notified '
                 'via email of any fulfillment actions caused by this '
                 'command. These email addresses will appear in the "to:" '
                 'address list in the email that is sent. '
                 'Can be specified multiple times. '
                 'Default: No email will be sent'),
    click.option('--email-cc-address', type=str, required=False, multiple=True,
                 help='An email address for the people that are to be notified '
                 'via email of any fulfillment actions caused by this '
                 'command. These email addresses will appear in the "cc:" '
                 'address list in the email that is sent. '
                 'Can be specified multiple times. '
                 'Default: The "cc:" address list of the email will be empty'),
    click.option('--email-insert', type=str, required=False,
                 help='Text that is to be inserted in the email notification '
                 'of any fulfillment actions caused by this command. '
                 'The text can include HTML formatting tags. '
                 'Default: The email will have no special text insert'),
]

# Click options use for commands that wait for completion of asynchronous HMC
# oprations
ASYNC_TIMEOUT_OPTIONS = [
    click.option('-T', '--operation-timeout', type=int, required=False,
                 help='Operation timeout in seconds when waiting for '
                 'completion of asynchronous HMC operations. '
                 'Default: {def_ot}'.
                 format(def_ot=zhmcclient.DEFAULT_OPERATION_TIMEOUT)),
]


def abort_if_false(ctx, param, value):
    """
    Click callback function that aborts the current command if the option
    value is false.

    Because this used as a reaction to an interactive confirmation question,
    we issue the error message always in a human readable format (i.e. ignore
    the specified error format).

    Note that abortion mechanisms such as ctx.abort() or raising click.Abort
    terminate the CLI completely, and not just the current command. This makes
    a difference in the interactive mode.

    Parameters:

      ctx (:class:`click.Context`): The click context object. Created by the
        ``@click.pass_context`` decorator.

      param (class:`click.Option`): The click option that used this callback.

      value: The option value to be tested.
    """
    # pylint: disable=unused-argument
    if not value:
        # click.ClickException seems to be the only reasonable exception we
        # can raise here, but it prefixes the error text with 'Error: ', which
        # is confusing in this case, because the user simply decided to abort.
        raise click.ClickException("Aborted!")


class InvalidOutputFormatError(click.ClickException):
    """
    Exception indicating an invalid output format for zhmc.
    """

    def __init__(self, output_format):
        msg = "Invalid output format: {of}".format(of=output_format)
        super(InvalidOutputFormatError, self).__init__(msg)


class CmdContext(object):
    """
    A context object we attach to the :class:`click.Context` object in its
    ``obj`` attribute. It is used to provide command line options and other
    data.
    """

    def __init__(self, host, userid, password, no_verify, ca_certs,
                 output_format, transpose, error_format, timestats, session_id,
                 get_password):
        self._host = host
        self._userid = userid
        self._password = password
        self._no_verify = no_verify
        self._ca_certs = ca_certs
        self._output_format = output_format
        self._transpose = transpose
        self._error_format = error_format
        self._timestats = timestats
        self._session_id = session_id
        self._get_password = get_password
        self._session = None
        self._spinner = click_spinner.Spinner()

    def __repr__(self):
        ret = "CmdContext(at 0x{ctx:08x}, host={s._host!r}, " \
            "userid={s._userid!r}, password={pw!r}, " \
            "no_verify={s._no_verify!r}, ca_certs={s._ca_certs!r}, " \
            "output_format={s._output_format!r}, transpose={s._transpose!r}, " \
            "error_format={s._error_format!r}, timestats={s._timestats!r}," \
            "session_id={s._session_id!r}, session={s._session!r}, ...)". \
            format(ctx=id(self), s=self, pw='...' if self._password else None)
        return ret

    @property
    def host(self):
        """
        :term:`string`: Hostname or IP address of the HMC.
        """
        return self._host

    @property
    def userid(self):
        """
        :term:`string`: Userid on the HMC.
        """
        return self._userid

    @property
    def no_verify(self):
        """
        bool: Do not verify the server certificate presented by the HMC
        during SSL/TLS handshake.
        """
        return self._no_verify

    @property
    def ca_certs(self):
        """
        :term:`string`: Path name of certificate file or directory with CA
        certificates for verifying the HMC certificate. If `None`, the
        zhmcclient will be set up to use the 'certifi' package.
        """
        return self._ca_certs

    @property
    def output_format(self):
        """
        :term:`string`: Output format to be used.
        """
        return self._output_format

    @property
    def transpose(self):
        """
        bool: Transpose the output table.
        """
        return self._transpose

    @property
    def error_format(self):
        """
        :term:`string`: Error message format to be used.
        """
        return self._error_format

    @property
    def timestats(self):
        """
        bool: Indicates whether time statistics should be printed.
        """
        return self._timestats

    @property
    def session_id(self):
        """
        :term:`string` or :class:`~zhmcclient_mock.FakedSession`:
          If string: Session-id of real session to be used.
          If `None`: Create a new real session using host, userid, password.
          If FakedSession: Faked session to be used.
        """
        return self._session_id

    @property
    def get_password(self):
        """
        :term:`callable`: Password retrieval function, or `None`.
        """
        return self._get_password

    @property
    def session(self):
        """
        The session to be used, or `None` if a session has not yet been
        created. The session may be a :class:`zhmcclient.Session` or
        :class:`zhmcclient_mock.FakedSession` object.
        """
        return self._session

    @property
    def spinner(self):
        """
        :class:`~click_spinner.Spinner` object.

        Since click_spinner 0.1.5, the Spinner object takes care of suppressing
        the spinner when not on a tty, and is able to suspend/resume the
        spinner via its stop() and start() methods.
        """
        return self._spinner

    def execute_cmd(self, cmd):
        """
        Execute the command.
        """
        if self._session is None:
            if isinstance(self._session_id, zhmcclient_mock.FakedSession):
                self._session = self._session_id
            else:
                if self._host is None:
                    raise click_exception("No HMC host provided",
                                          self._error_format)
                if self._no_verify:
                    verify_cert = False
                elif self._ca_certs is None:
                    verify_cert = True  # Use 'certifi' package
                else:
                    verify_cert = self._ca_certs
                self._session = zhmcclient.Session(
                    self._host, self._userid, self._password,
                    session_id=self._session_id,
                    get_password=self._get_password,
                    verify_cert=verify_cert)
        if self.timestats:
            self._session.time_stats_keeper.enable()
        self.spinner.start()
        try:
            cmd()
        except zhmcclient.Error as exc:
            raise click_exception(exc, self.error_format)
        finally:
            self.spinner.stop()
            if self._session.time_stats_keeper.enabled:
                click.echo(self._session.time_stats_keeper)


def original_options(options):
    """
    Return the input options with their original names.

    This is used to undo the name change the click package applies
    automatically before passing the options to the function that was decorated
    with 'click.option()'. The original names are needed in case there is
    special processing of the options on top of 'options_to_properties()'.

    The original names are constructed by replacing any underscores '_' with
    hyphens '-'. This approach may not be perfect in general, but it works for
    the zhmc CLI because the original option names do not have any underscores.

    Parameters:

      options (dict): The click options dictionary as passed to the decorated
        function by click (key: option name as changed by click, value: option
        value).

    Returns:

      dict: Options with their original names.
    """
    org_options = {}
    for name, value in six.iteritems(options):
        org_name = name.replace('_', '-')
        org_options[org_name] = value
    return org_options


def options_to_properties(options, name_map=None):
    """
    Convert click options into HMC resource properties.

    The click option names in input parameters to this function are the
    original option names (e.g. as produced by `original_options()`.

    Options with a value of `None` are not added to the returned resource
    properties.

    If a name mapping dictionary is specified, the option names are mapped
    using that dictionary. If an option name is mapped to `None`, it is not
    going to be added to the set of returned resource properties.

    Parameters:

      options (dict): The options dictionary (key: original option name,
        value: option value).

      name_map (dict): `None` or name mapping dictionary (key: original
        option name, value: property name, or `None` to not add this option to
        the returned properties).

    Returns:

      dict: Resource properties (key: property name, value: option value)
    """
    properties = {}
    for name, value in six.iteritems(options):
        if value is None:
            continue
        if name_map:
            name = name_map.get(name, name)
        if name is not None:
            properties[name] = value
    return properties


def print_properties(cmd_ctx, properties, output_format, show_list=None):
    """
    Print properties in the desired output format.

    The spinner is stopped just before printing.

    Parameters:

      cmd_ctx (CmdContext): Context object of the command.

      properties (dict): The properties.

      output_format (string): Output format from the command line.

      show_list (iterable of string): The property names to be shown.
        If `None`, all properties are shown.
    """
    if output_format in TABLE_FORMATS:
        if output_format == 'table':
            output_format = 'psql'
        print_properties_as_table(cmd_ctx, properties, output_format, show_list)
    elif output_format == 'json':
        print_properties_as_json(cmd_ctx, properties, show_list)
    else:
        raise InvalidOutputFormatError(output_format)


def print_resources(
        cmd_ctx, resources, output_format, show_list=None, additions=None,
        all=False):
    # pylint: disable=redefined-builtin
    """
    Print the properties of a list of resources in the desired output format.

    While accessing the properties of the resources, they are fetched from
    the HMC as needed.
    The spinner is stopped just before printing.

    Parameters:

      cmd_ctx (CmdContext): Context object of the command.

      resources (iterable of BaseResource):
        The resources.

      output_format (string): Output format from command line.

      show_list (iterable of string):
        The property names to be shown. If a property is not in the resource
        object, it will be retrieved from the HMC. This iterable also defines
        the order of columns in the table, from left to right in iteration
        order.
        If `None`, all properties in the resource objects are shown, and their
        column order is ascending by property name.

      additions (dict of dict of values): Additional properties,
        as a dict keyed by the property name (which also needs to be listed in
        `show_list`),
        whose value is a dict keyed by the resource URI,
        whose value is the value to be shown.
        If `None`, no additional properties are defined.

      all (bool): Add all remaining properties in sorted order.

    Raises:
        InvalidOutputFormatError
        zhmcclient.HTTPError
        zhmcclient.ParseError
        zhmcclient.AuthError
        zhmcclient.ConnectionError
    """
    if output_format in TABLE_FORMATS:
        if output_format == 'table':
            output_format = 'psql'
        print_resources_as_table(
            cmd_ctx, resources, output_format, show_list, additions, all)
    elif output_format == 'json':
        print_resources_as_json(cmd_ctx, resources, show_list, additions, all)
    else:
        raise InvalidOutputFormatError(output_format)


def print_dicts(
        cmd_ctx, dicts, output_format, show_list=None, additions=None,
        all=False):
    # pylint: disable=redefined-builtin
    """
    Print the properties of a list of dicts in the desired output format.

    The spinner is stopped just before printing.

    Parameters:

      cmd_ctx (CmdContext): Context object of the command.

      dicts (iterable of dict):
        The dicts.

      output_format (string): Output format from command line.

      show_list (iterable of string):
        The property names to be shown. If a property is not in the dict
        object, its value defaults to None. This iterable also defines
        the order of columns in the table, from left to right in iteration
        order.
        If `None`, all properties in the dict objects are shown, and their
        column order is ascending by property name.

      additions (dict of dict of values): Additional properties,
        as a dict keyed by the property name (which also needs to be listed in
        `show_list`),
        whose value is a dict keyed by the resource URI,
        whose value is the value to be shown.
        If `None`, no additional properties are defined.

      all (bool): Add all remaining properties in sorted order.

    Raises:
        InvalidOutputFormatError
    """
    if output_format in TABLE_FORMATS:
        if output_format == 'table':
            output_format = 'psql'
        print_dicts_as_table(
            cmd_ctx, dicts, output_format, show_list, additions, all)
    elif output_format == 'json':
        print_dicts_as_json(cmd_ctx, dicts, show_list, additions, all)
    else:
        raise InvalidOutputFormatError(output_format)


def print_properties_as_table(
        cmd_ctx, properties, table_format, show_list=None):
    """
    Print properties in tabular output format.

    The order of rows is ascending by property name.
    The spinner is stopped just before printing.

    Parameters:

      cmd_ctx (CmdContext): Context object of the command.

      properties (dict): The properties.

      table_format (string): Supported table formats are:
         - "table" -> same like "psql"
         - "plain"
         - "simple"
         - "psql"
         - "rst"
         - "mediawiki"
         - "html"
         - "latex"

      show_list (iterable of string): The property names to be shown.
        If `None`, all properties are shown.
    """
    headers = ['Field Name', 'Value']
    out_str = dict_as_table(properties, headers, table_format, show_list)
    cmd_ctx.spinner.stop()
    click.echo(out_str)


def print_resources_as_table(
        cmd_ctx, resources, table_format, show_list=None, additions=None,
        all=False):
    # pylint: disable=redefined-builtin
    """
    Print resources in tabular output format.

    While accessing the properties of the resources, they are fetched from
    the HMC as needed.
    The spinner is stopped just before printing.

    Parameters:

      cmd_ctx (CmdContext): Context object of the command.

      resources (iterable of BaseResource):
        The resources.

      table_format (string): Supported table formats are:
         - "table" -> same like "psql"
         - "plain"
         - "simple"
         - "psql"
         - "rst"
         - "mediawiki"
         - "html"
         - "latex"

      show_list (iterable of string):
        The property names to be shown. If a property is not in the resource
        object, it will be retrieved from the HMC. This iterable also defines
        the order of columns in the table, from left to right in iteration
        order.
        If `None`, all properties in the resource objects are shown, and their
        column order is ascending by property name.

      additions (dict of dict of values): Additional properties,
        as a dict keyed by the property name (which also needs to be listed in
        `show_list`),
        whose value is a dict keyed by the resource URI,
        whose value is the value to be shown.
        If `None`, no additional properties are defined.

      all (bool): Add all remaining properties in sorted order.

    Raises:
        zhmcclient.HTTPError
        zhmcclient.ParseError
        zhmcclient.AuthError
        zhmcclient.ConnectionError
    """
    inner_format = INNER_TABLE_FORMAT.get(table_format, table_format)
    prop_names = OrderedDict()  # key: property name, value: None
    remaining_prop_names = OrderedDict()  # key: property name, value: None
    resource_props_list = []
    for resource in resources:
        resource_props = {}
        if show_list:
            for name in show_list:
                if additions and name in additions:
                    value = additions[name][resource.uri]
                else:
                    # May raise zhmcclient exceptions
                    value = resource.prop(name)
                resource_props[name] = value
                prop_names[name] = None
        else:
            for name in sorted(resource.properties):
                # May raise zhmcclient exceptions
                resource_props[name] = resource.prop(name)
                prop_names[name] = None
        if all:
            resource.pull_full_properties()
            for name in resource.properties:
                if name not in prop_names:
                    # May raise zhmcclient exceptions
                    resource_props[name] = resource.prop(name)
                    remaining_prop_names[name] = None
        resource_props_list.append(resource_props)

    prop_names = list(prop_names.keys()) + sorted(remaining_prop_names)
    table = []
    for resource_props in resource_props_list:
        row = []
        for name in prop_names:
            value = resource_props.get(name, None)
            value = value_as_table(value, inner_format)
            row.append(value)
        table.append(row)

    cmd_ctx.spinner.stop()
    if not table:
        click.echo("No resources.")
    else:
        sorted_table = sorted(table, key=lambda row: row[0])
        out_str = tabulate(sorted_table, prop_names, tablefmt=table_format)
        click.echo(out_str)


def print_dicts_as_table(
        cmd_ctx, dicts, table_format, show_list=None, additions=None,
        all=False):
    # pylint: disable=redefined-builtin
    """
    Print a list of dictionaries in tabular output format.

    The spinner is stopped just before printing.

    Parameters:

      cmd_ctx (CmdContext): Context object of the command.

      dicts (iterable of dict):
        The dictionaries.

      table_format (string): Supported table formats are:
         - "table" -> same like "psql"
         - "plain"
         - "simple"
         - "psql"
         - "rst"
         - "mediawiki"
         - "html"
         - "latex"

      show_list (iterable of string):
        The property names to be shown. If a property is not in the dict
        object, its value defaults to None. This iterable also defines
        the order of columns in the table, from left to right in iteration
        order.
        If `None`, all properties in the dict objects are shown, and their
        column order is ascending by property name.

      additions (dict of dict of values): Additional properties,
        as a dict keyed by the property name (which also needs to be listed in
        `show_list`),
        whose value is a dict keyed by the index in dicts,
        whose value is the value to be shown.
        If `None`, no additional properties are defined.

      all (bool): Add all remaining properties in sorted order.
    """
    inner_format = INNER_TABLE_FORMAT.get(table_format, table_format)
    prop_names = OrderedDict()  # key: property name, value: None
    remaining_prop_names = OrderedDict()  # key: property name, value: None
    dict_props_list = []
    for index, _dict in enumerate(dicts):
        dict_props = {}
        if show_list:
            for name in show_list:
                if additions and name in additions:
                    value = additions[name][index]
                else:
                    value = _dict[name]
                dict_props[name] = value
                prop_names[name] = None
        else:
            for name in sorted(_dict):
                # May raise zhmcclient exceptions
                dict_props[name] = _dict[name]
                prop_names[name] = None
        if all:
            for name in _dict:
                if name not in prop_names:
                    # May raise zhmcclient exceptions
                    dict_props[name] = _dict[name]
                    remaining_prop_names[name] = None
        dict_props_list.append(dict_props)

    prop_names = list(prop_names.keys()) + sorted(remaining_prop_names)
    table = []
    for dict_props in dict_props_list:
        row = []
        for name in prop_names:
            value = dict_props.get(name, None)
            value = value_as_table(value, inner_format)
            row.append(value)
        table.append(row)

    cmd_ctx.spinner.stop()
    if not table:
        click.echo("No items.")
    else:
        sorted_table = sorted(table, key=lambda row: row[0])
        out_str = tabulate(sorted_table, prop_names, tablefmt=table_format)
        click.echo(out_str)


def dict_as_table(data, headers, table_format, show_list=None):
    """
    Return a string with the dictionary data in tabular output format.

    The order of rows is ascending by dictionary key.

    Parameters:

      data (dict): The dictionary data.

      headers (list): The text for the header row. `None` means no header row.

      table_format: Table format, see print_resources_as_table().

      show_list (iterable of string): The dict keys to be shown.
        If `None`, all dict keys are shown.
    """
    if table_format == 'repr':
        ret_str = repr(data)
    else:
        table = []
        inner_format = INNER_TABLE_FORMAT.get(table_format, table_format)
        sorted_fields = sorted(data)
        for field in sorted_fields:
            if show_list is None or field in show_list:
                value = value_as_table(data[field], inner_format)
                table.append((field, value))
        ret_str = tabulate(table, headers, tablefmt=table_format)
    return ret_str


def list_as_table(data, table_format):
    """
    Return a string with the list data in tabular output format.

    The order of rows is the order of items in the list.

    Parameters:

      data (list): The list data.

      table_format: Table format, see print_resources_as_table().
    """
    if table_format == 'repr':
        ret_str = repr(data)
    else:
        table = []
        inner_format = INNER_TABLE_FORMAT.get(table_format, table_format)
        for value in data:
            value = value_as_table(value, inner_format)
            table.append((value,))
        ret_str = tabulate(table, headers=[], tablefmt=table_format)
    return ret_str


def value_as_table(value, table_format):
    """
    Return the value in the table format.

    Parameters:

      value (dict or list or simple type): The value to be converted.

      table_format (string): The table format to be used.

    Returns:
      string or simple type: The value in the table format.
    """
    if isinstance(value, list):
        value = list_as_table(value, table_format)
    elif isinstance(value, (dict, OrderedDict)):
        value = dict_as_table(value, [], table_format)
    else:
        # format the single value
        # TODO: Make the formatting less hard coded.
        if isinstance(value, float):
            value = '{0:.2f}'.format(value)
    return value


def print_properties_as_json(cmd_ctx, properties, show_list=None):
    """
    Print properties in JSON output format.

    The spinner is stopped just before printing.

    Parameters:

      cmd_ctx (CmdContext): Context object of the command.

      properties (dict): The properties.

      show_list (iterable of string):
        The property names to be shown. The property name must be in the
        `properties` dict.
        If `None`, all properties in the `properties` dict are shown.
    """
    show_properties = OrderedDict()
    for pname in sorted(properties):
        if show_list is None or pname in show_list:
            show_properties[pname] = properties[pname]
    json_str = json.dumps(show_properties)
    cmd_ctx.spinner.stop()
    click.echo(json_str)


def print_resources_as_json(
        cmd_ctx, resources, show_list=None, additions=None, all=False):
    # pylint: disable=redefined-builtin
    """
    Print resources in JSON output format.

    While accessing the properties of the resources, they are fetched from
    the HMC as needed.
    The spinner is stopped just before printing.

    Parameters:

      cmd_ctx (CmdContext): Context object of the command.

      resources (iterable of BaseResource):
        The resources.

      show_list (iterable of string):
        The property names to be shown. If a property is not in a resource
        object, it will be retrieved from the HMC.
        If `None`, all properties in the input resource objects are shown.

      additions (dict of dict of values): Additional properties,
        as a dict keyed by the property name (which also needs to be listed in
        `show_list`),
        whose value is a dict keyed by the resource URI,
        whose value is the value to be shown.
        If `None`, no additional properties are defined.

      all (bool): Add all remaining properties in sorted order.

    Raises:
        zhmcclient.HTTPError
        zhmcclient.ParseError
        zhmcclient.AuthError
        zhmcclient.ConnectionError
    """
    prop_names = OrderedDict()  # key: property name, value: None
    resource_props_list = []
    for resource in resources:
        resource_props = {}
        if show_list:
            for name in show_list:
                if additions and name in additions:
                    value = additions[name][resource.uri]
                else:
                    # May raise zhmcclient exceptions
                    value = resource.prop(name)
                resource_props[name] = value
                prop_names[name] = None
        else:
            for name in resource.properties:
                # May raise zhmcclient exceptions
                resource_props[name] = resource.prop(name)
                prop_names[name] = None
        if all:
            resource.pull_full_properties()
            for name in resource.properties:
                if name not in prop_names:
                    # May raise zhmcclient exceptions
                    resource_props[name] = resource.prop(name)
                    prop_names[name] = None
        resource_props_list.append(resource_props)

    json_obj = []
    for resource_props in resource_props_list:
        json_res = OrderedDict()
        for name in sorted(prop_names):
            value = resource_props.get(name, None)
            json_res[name] = value
        json_obj.append(json_res)

    json_str = json.dumps(json_obj)
    cmd_ctx.spinner.stop()
    click.echo(json_str)


def print_dicts_as_json(
        cmd_ctx, dicts, show_list=None, additions=None, all=False):
    # pylint: disable=redefined-builtin
    """
    Print dicts in JSON output format.

    The spinner is stopped just before printing.

    Parameters:

      cmd_ctx (CmdContext): Context object of the command.

      dicts (iterable of dict):
        The dicts.

      show_list (iterable of string):
        The property names to be shown. If a property is not in a resource
        object, its value will default to None.
        If `None`, all properties in the input resource objects are shown.

      additions (dict of dict of values): Additional properties,
        as a dict keyed by the property name (which also needs to be listed in
        `show_list`),
        whose value is a dict keyed by the index in dicts,
        whose value is the value to be shown.
        If `None`, no additional properties are defined.

      all (bool): Add all remaining properties in sorted order.
    """
    prop_names = OrderedDict()  # key: property name, value: None
    dict_props_list = []
    for index, _dict in enumerate(dicts):
        dict_props = {}
        if show_list:
            for name in show_list:
                if additions and name in additions:
                    value = additions[name][index]
                else:
                    # May raise zhmcclient exceptions
                    value = _dict[name]
                dict_props[name] = value
                prop_names[name] = None
        else:
            for name in _dict:
                # May raise zhmcclient exceptions
                dict_props[name] = _dict[name]
                prop_names[name] = None
        if all:
            for name in _dict:
                if name not in prop_names:
                    # May raise zhmcclient exceptions
                    dict_props[name] = _dict[name]
                    prop_names[name] = None
        dict_props_list.append(dict_props)

    json_obj = []
    for dict_props in dict_props_list:
        json_res = OrderedDict()
        for name in sorted(prop_names):
            value = dict_props.get(name, None)
            json_res[name] = value
        json_obj.append(json_res)

    json_str = json.dumps(json_obj)
    cmd_ctx.spinner.stop()
    click.echo(json_str)


class ExceptionThread(threading.Thread):
    """
    A thread class derived from :class:`py:threading.Thread` that handles
    exceptions that are raised in the started thread, by re-raising them in
    the thread that joins the started thread.

    The thread function needs to be specified with the 'target' init argument.
    """

    def __init__(self, *args, **kwargs):
        super(ExceptionThread, self).__init__(*args, **kwargs)
        self.exc_info = None

    def run(self):
        """
        Call inherited run() and save exception info.
        """
        try:
            super(ExceptionThread, self).run()
        except Exception:  # noqa: E722 pylint: disable=broad-except
            self.exc_info = sys.exc_info()

    def join(self, timeout=None):
        """
        Call inherited join() and reraise exception if exception info was saved.
        """
        super(ExceptionThread, self).join(timeout)
        if self.exc_info:
            six.reraise(*self.exc_info)


def console_log(logger, prefix, message, *args, **kwargs):
    """
    Log a message after prepending it with a prefix, to the specified logger
    using the debug log level.
    """
    message = prefix + message
    logger.debug(message, *args, **kwargs)


def display_messages(receiver, logger, prefix):
    """
    Receive the OS message notifications in the specified receiver and
    print them to stdout. The function returns when the receiver is
    exhausted (which happens when it is closed).

    Due to inconsistencies in the message text w.r.t. newline, some processing
    is performed regarding trailing newlines.
    """
    console_log(logger, prefix, "Message display thread has started")
    for headers, message in receiver.notifications():
        console_log(logger, prefix,
                    "Received OS message notification "
                    "session-sequence-nr=%s", headers['session-sequence-nr'])
        for msg_info in message['os-messages']:
            msg_txt = msg_info['message-text']
            console_log(logger, prefix,
                        "Message id=%s, os=%r, refresh=%r, prompt=%r: %r",
                        msg_info['message-id'], msg_info['os-name'],
                        msg_info['is-refresh'], msg_info['prompt-text'],
                        msg_txt)
            is_prompt = re.match(r'^.*[\$#] ?$', msg_txt)
            is_login = re.match(r'^.*[Ll]ogin: ?$', msg_txt)
            is_password = re.match(r'^[Pp]assword: *$', msg_txt)
            if is_prompt or is_login or is_password:
                msg_txt = msg_txt.rstrip('\n')
            else:
                if not msg_txt.endswith('\n'):
                    msg_txt += '\n'
            click.echo(msg_txt, nl=False)
    console_log(logger, prefix, "Message display thread is ending")


def part_console(session, part, refresh, logger):
    """
    Establish an interactive shell to the console of the operating system
    running in a partition or LPAR.

    Any incoming OS messages of the console are printed concurrently with
    waiting for and sending the next command.

    The shell ends and this function returns if one of the exit commands
    is entered.

    Parameters:

      session (Session): HMC session supplying the credentials.

      part (Partition or Lpar): Resource object for the partition or LPAR.

      refresh (bool): Include refresh messages.

      logger (Logger): Python logger for any log messages.

    Raises:

      Exceptions derived from zhmcclient.Error

      AssertionError
    """

    if isinstance(part, zhmcclient.Partition):
        part_term = 'partition'
    else:
        part_term = 'LPAR'
    cpc = part.manager.parent

    prefix = "{c} {p} ".format(c=cpc.name, p=part.name)

    console_log(logger, prefix, "Operating system console session opened")
    console_log(logger, prefix, "Include refresh messages: %s", refresh)

    try:
        topic = part.open_os_message_channel(include_refresh_messages=refresh)
        console_log(logger, prefix, "Using new notification topic: %s", topic)
    except zhmcclient.HTTPError as exc:
        if exc.http_status == 409 and exc.reason == 331:
            # Notification topic for this partition already exists, use it
            topic_dicts = session.get_notification_topics()
            topic = None
            for topic_dict in topic_dicts:
                if topic_dict['topic-type'] != 'os-message-notification':
                    continue
                obj_uri = topic_dict['object-uri']
                if part.uri in (obj_uri, '/api/partitions/' + obj_uri):
                    topic = topic_dict['topic-name']
                    console_log(logger, prefix,
                                "Using existing notification topic: %s "
                                "(object-uri: %s)", topic, obj_uri)
                    break
            assert topic, \
                "An OS message notification topic for {pt} {pn} (uri={pu}) " \
                "supposedly exists, but cannot be found in the existing " \
                "topics: {t})". \
                format(pt=part_term, pn=part.name, pu=part.uri, t=topic_dicts)
        else:
            raise

    # pylint: disable=protected-access
    if not session._password:
        # pylint: disable=protected-access
        session._password = click.prompt(
            "Enter password (for user {s.userid} at HMC {s.host})"
            .format(s=session),
            hide_input=True, confirmation_prompt=False, type=str, err=True)

    # pylint: disable=protected-access
    receiver = zhmcclient.NotificationReceiver(
        topic, session.host, session.userid, session._password)

    msg_thread = ExceptionThread(
        target=display_messages, args=(receiver, logger, prefix))

    click.echo("Connected to operating system console for {pt} {pn}".
               format(pt=part_term, pn=part.name))
    click.echo("Enter ':exit' or press <CTRL-C> or <CTRL-D> to exit.")

    console_log(logger, prefix, "Starting message display thread")
    msg_thread.start()

    while True:
        try:
            # This has history/ editing support when readline is imported
            line = six.moves.input()
        except EOFError:
            # CTRL-D was pressed
            reason = "CTRL-D"
            break
        except KeyboardInterrupt:
            # CTRL-C was pressed
            reason = "CTRL-C"
            break
        if line == ':exit':
            reason = "{c} command".format(c=line)
            break
        if line == '':
            # Enter was pressed without other input.
            # The HMC requires at least one character in the command, otherwise
            # it returns an error.
            line = ' '
        part.send_os_command(line, is_priority=False)

    console_log(logger, prefix,
                "User requested to exit the console session via %s", reason)

    console_log(logger, prefix, "Closing notification receiver")
    # This causes the notification receiver to be exhausted, and in turn causes
    # the message display thread to end.
    receiver.close()

    console_log(logger, prefix, "Waiting for message display thread to end")
    msg_thread.join()

    console_log(logger, prefix, "Operating system console session closed")

    click.echo("\nConsole session closed.")


def click_exception(exc, error_format):
    """
    Return a ClickException object with the message from an input exception
    in a desired error message format.

    Parameters:

      exc (exception or string):
        The exception or the message.

      error_format (string):
        The error format (see ``--error-format`` general option).

    Returns:
      click.ClickException: The new exception.
    """
    if error_format == 'def':
        if isinstance(exc, zhmcclient.Error):
            error_str = exc.str_def()
        elif isinstance(exc, Exception):
            error_str = str(exc)
        else:
            assert isinstance(exc, six.string_types)
            error_str = "classname: None, message: {msg}".format(msg=exc)
    else:
        assert error_format == 'msg'
        if isinstance(exc, Exception):
            error_str = "{exc}: {msg}".format(
                exc=exc.__class__.__name__, msg=exc)
        else:
            assert isinstance(exc, six.string_types)
            error_str = exc
    new_exc = click.ClickException(error_str)
    new_exc.__cause__ = None
    return new_exc


def add_options(click_options):
    """
    Decorator that adds multiple Click options to the decorated function.

    The list is reversed because of the way Click processes options.

    Note: This function has its origins in the
    https://github.com/pywbem/pywbemtools project (Apache 2.0 license)

    Parameters:

      click_options (list): List of `click.option` objects.
    """

    def _add_options(func):
        """
        Apply the Click options to the function in reversed order.
        """
        for option in reversed(click_options):
            func = option(func)
        return func

    return _add_options


def storage_management_feature(cpc_or_partition):
    """
    Return a boolean indicating whether the specified CPC, or the CPC of the
    specified partition has the DPM storage management feature enabled.

    On z13 and earlier, the storage managemt feature is always disabled.
    On z14 and later, the storage managemt feature is always enabled.
    Nevertheless, this function performs the proper lookup of the feature.
    """
    features = cpc_or_partition.prop('available-features-list', [])
    for f in features:
        if f['name'] == 'dpm-storage-management':
            return f['state']
    return False


def hide_property(properties, prop_name):
    """
    Hide a property, if it exists and is not empty.

    This is done by modifying the value of the property in the 'properties'
    parameter.

    Parameters:
      properties(dict): Dict of properties (name/value). May be changed.
      prop_name(string): Property name to hide
    """
    if prop_name in properties and properties[prop_name]:
        properties[prop_name] = "... (hidden)"


class ObjectByUriCache(object):
    """
    Object cache that allows lookup of resource objects by URI.

    The cache is not automatically updated, so it can be used only for short
    periods of time, e.g. within the scope of a single zhmc command.
    """

    def __init__(self, cmd_ctx, client):
        self._cmd_ctx = cmd_ctx
        self._client = client
        self._console = client.consoles.console
        self._user_roles_by_uri = None
        self._password_rules_by_uri = None
        self._tasks_by_uri = None
        self._cpcs_by_uri = None
        self._adapters_by_uri = None
        self._partitions_by_uri = None
        self._lpars_by_uri = None
        self._storage_groups_by_uri = None

    def _get_user_roles(self):
        # pylint: disable=missing-function-docstring
        try:
            user_roles = self._console.user_roles.list(full_properties=False)
        except zhmcclient.Error as exc:
            raise click_exception(exc, self._cmd_ctx.error_format)
        result = {}
        for obj in user_roles:
            result[obj.uri] = obj
        return result

    def user_role_by_uri(self, user_role_uri):
        """
        Return UserRole object by its URI.
        Fill the cache if needed.
        """
        if self._user_roles_by_uri is None:
            self._user_roles_by_uri = self._get_user_roles()
        return self._user_roles_by_uri[user_role_uri]

    def _get_password_rules(self):
        # pylint: disable=missing-function-docstring
        try:
            password_rules = \
                self._console.password_rules.list(full_properties=False)
        except zhmcclient.Error as exc:
            raise click_exception(exc, self._cmd_ctx.error_format)
        result = {}
        for obj in password_rules:
            result[obj.uri] = obj
        return result

    def password_rule_by_uri(self, password_rule_uri):
        """
        Return PasswordRule object by its URI.
        Fill the cache if needed.
        """
        if self._password_rules_by_uri is None:
            self._password_rules_by_uri = self._get_password_rules()
        return self._password_rules_by_uri[password_rule_uri]

    def _get_tasks(self):
        # pylint: disable=missing-function-docstring
        try:
            tasks = self._console.tasks.list(full_properties=False)
        except zhmcclient.Error as exc:
            raise click_exception(exc, self._cmd_ctx.error_format)
        result = {}
        for obj in tasks:
            result[obj.uri] = obj
        return result

    def task_by_uri(self, task_uri):
        """
        Return Task object by its URI.
        Fill the cache if needed.
        """
        if self._tasks_by_uri is None:
            self._tasks_by_uri = self._get_tasks()
        return self._tasks_by_uri[task_uri]

    def _get_cpcs(self):
        # pylint: disable=missing-function-docstring
        try:
            cpcs = self._client.cpcs.list(full_properties=False)
        except zhmcclient.Error as exc:
            raise click_exception(exc, self._cmd_ctx.error_format)
        result = {}
        for obj in cpcs:
            result[obj.uri] = obj
        return result

    def cpc_by_uri(self, cpc_uri):
        """
        Return Cpc object by its URI.
        Fill the cache if needed.
        """
        if self._cpcs_by_uri is None:
            self._cpcs_by_uri = self._get_cpcs()
        return self._cpcs_by_uri[cpc_uri]

    def _get_adapters(self, cpc):
        # pylint: disable=missing-function-docstring
        try:
            adapters = cpc.adapters.list(full_properties=False)
        except zhmcclient.Error as exc:
            raise click_exception(exc, self._cmd_ctx.error_format)
        result = {}
        for obj in adapters:
            result[obj.uri] = obj
        return result

    def adapter_by_uri(self, adapter_uri):
        """
        Return Adapter object by its URI.
        Fill the cache if needed.
        """
        if self._cpcs_by_uri is None:
            self._cpcs_by_uri = self._get_cpcs()
        if self._adapters_by_uri is None:
            self._adapters_by_uri = {}
            for cpc in self._cpcs_by_uri.values():
                self._adapters_by_uri.update(self._get_adapters(cpc))
        return self._adapters_by_uri[adapter_uri]

    def _get_partitions(self, cpc):
        # pylint: disable=missing-function-docstring
        try:
            partitions = cpc.partitions.list(full_properties=False)
        except zhmcclient.Error as exc:
            raise click_exception(exc, self._cmd_ctx.error_format)
        result = {}
        for obj in partitions:
            result[obj.uri] = obj
        return result

    def partition_by_uri(self, partition_uri):
        """
        Return Partition object by its URI.
        Fill the cache if needed.
        """
        if self._cpcs_by_uri is None:
            self._cpcs_by_uri = self._get_cpcs()
        if self._partitions_by_uri is None:
            self._partitions_by_uri = {}
            for cpc in self._cpcs_by_uri.values():
                self._partitions_by_uri.update(
                    self._get_partitions(cpc))
        return self._partitions_by_uri[partition_uri]

    def _get_lpars(self, cpc):
        # pylint: disable=missing-function-docstring
        try:
            lpars = cpc.lpars.list(full_properties=False)
        except zhmcclient.Error as exc:
            raise click_exception(exc, self._cmd_ctx.error_format)
        result = {}
        for obj in lpars:
            result[obj.uri] = obj
        return result

    def lpar_by_uri(self, lpar_uri):
        """
        Return Lpar object by its URI.
        Fill the cache if needed.
        """
        if self._cpcs_by_uri is None:
            self._cpcs_by_uri = self._get_cpcs()
        if self._lpars_by_uri is None:
            self._lpars_by_uri = {}
            for cpc in self._cpcs_by_uri.values():
                self._lpars_by_uri.update(self._get_lpars(cpc))
        return self._lpars_by_uri[lpar_uri]

    def _get_storage_groups(self, cpc):
        # pylint: disable=missing-function-docstring
        try:
            storage_groups = cpc.list_associated_storage_groups()
        except zhmcclient.Error as exc:
            raise click_exception(exc, self._cmd_ctx.error_format)
        result = {}
        for obj in storage_groups:
            result[obj.uri] = obj
        return result

    def storage_group_by_uri(self, storage_group_uri):
        """
        Return StorageGroup object by its URI.
        Fill the cache if needed.
        """
        if self._cpcs_by_uri is None:
            self._cpcs_by_uri = self._get_cpcs()
        if self._storage_groups_by_uri is None:
            self._storage_groups_by_uri = {}
            for cpc in self._cpcs_by_uri.values():
                self._storage_groups_by_uri.update(
                    self._get_storage_groups(cpc))
        return self._storage_groups_by_uri[storage_group_uri]

    # TODO: Add storage_group_template_by_uri() once list() of associated
    #       templates implemented in zhmcclient


def required_option(options, option_key, unspecified_value=None):
    """
    Check if an option is specified.

    If it is specified, return the option value.

    Otherwise, raise ClickException with an according error message.
    """
    if options[option_key] != unspecified_value:
        return options[option_key]
    option_name = '--' + option_key.replace('_', '-')
    raise click.ClickException(
        "Required option not specified: {}".format(option_name))


def validate(data, schema, what):
    """
    Validate a data object (e.g. dict loaded from JSON or YAML) against a JSON
    schema object.

    Parameters:

      data (dict): Data object to be validated.

      schema (dict): JSON schema object used for the validation.

      what (string): Short string what the data represents, for messages.

    Raises:
      ValueError: Validation failed
    """
    try:
        jsonschema.validate(data, schema)
    except jsonschema.exceptions.ValidationError as exc:
        raise ValueError(
            "Validation of {what} failed: {msg}; "
            "Offending element: {elem}; "
            "Schema item: {schemaitem}; "
            "Validator: {valname}={valvalue}".
            format(what=what,
                   schemaitem='.'.join(str(e) for e in
                                       exc.absolute_schema_path),
                   msg=exc.message,
                   # need to convert to string, as when path contains a list,
                   # the list element is indicated as integer
                   elem='.'.join(str(e) for e in exc.absolute_path),
                   valname=exc.validator,
                   valvalue=exc.validator_value))
