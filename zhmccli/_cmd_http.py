# Copyright 2026 IBM Corp. All Rights Reserved.
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
Commands for making direct HTTP requests to the HMC WS-API.
"""

import json
import click

import zhmcclient
from .zhmccli import cli
from ._helper import COMMAND_OPTIONS_METAVAR, click_exception, add_options, \
    print_properties, print_dicts, print_list


# Click options for unpacking response bodies
UNPACK_OPTIONS = [
    click.option('--unpack', '-u', is_flag=True, required=False, default=False,
                 help="Unpack a single top-level property in the result when "
                 "its value is an array of objects. Unpacking causes the "
                 "value of the top-level property to be displayed instead of "
                 "the entire response payload. "
                 "This is useful for List operations. "
                 "The option has no effect if the response payload does not "
                 "have that structure.")
]


@cli.group('http', options_metavar=COMMAND_OPTIONS_METAVAR)
def http_group():
    """
    Command group for direct HTTP requests to the HMC WS-API.

    This can be used as a fallback for HMC WS-API operations that are not yet
    supported with proper zhmc CLI commands.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@http_group.command('get', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('URI', type=str, metavar='URI')
@add_options(UNPACK_OPTIONS)
@click.pass_obj
def http_get(cmd_ctx, uri, **options):
    """
    Perform an HTTP GET request against the HMC WS-API and display the response.

    URI is the canonical URI starting with '/api/', including any query
    parameters.

    The response payload will be displayed in the selected output format.
    Depending on its data structure, the response payload is shown as a single
    resource with properties, as a list of resources with properties or as a
    plain text string.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_http_get(cmd_ctx, uri, options))


@http_group.command('post', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('URI', type=str, metavar='URI')
@click.argument('REQUEST_BODY', type=str, metavar='[REQUEST_BODY]',
                required=False)
@add_options(UNPACK_OPTIONS)
@click.pass_obj
def http_post(cmd_ctx, uri, request_body, **options):
    """
    Perform an HTTP POST request against the HMC WS-API and display the
    response.

    URI is the canonical URI starting with '/api/', including any query
    parameters.

    REQUEST_BODY is the request body for the WS-API operation, in JSON format.

    The response payload will be displayed in the selected output format.
    Depending on its data structure, the response payload is shown as a single
    resource with properties, as a list of resources with properties or as a
    plain text string.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_http_post(cmd_ctx, uri, request_body, options))


@http_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('URI', type=str, metavar='URI')
@click.pass_obj
def http_delete(cmd_ctx, uri):
    """
    Perform an HTTP DELETE request against the HMC WS-API and display the
    response.

    URI is the canonical URI starting with '/api/', including any query
    parameters.

    Note that DELETE operations typically have no response body.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_http_delete(cmd_ctx, uri))


def determine_unpack(unpack, result):
    """
    Determine whether the result should be unpacked and return a tuple
    tuple(unpack, result).

    Unpacking is only done for single top-level properties whose value is an
    array of dicts (the array can be empty).
    """
    if unpack:

        if len(result) != 1:
            return False, result

        value = next(iter(result.values()))  # Value of top-level property
        if not isinstance(value, list):
            return False, result

        if len(value) > 0 and not isinstance(value[0], dict):
            return False, result

        # Unpack the result
        return True, value

    return False, result


def print_result(cmd_ctx, result, output_format, unpack=False):
    """
    Print the response body of a WS-API operation.
    """
    if isinstance(result, list):
        if len(result) == 0 or isinstance(result[0], dict):
            # Print as list of dicts
            print_dicts(cmd_ctx, result, output_format)
        else:
            # Print as list of values
            print_list(cmd_ctx, result, output_format)
    elif isinstance(result, dict):
        unpack, result = determine_unpack(unpack, result)
        if unpack:
            print_dicts(cmd_ctx, result, output_format)
        else:
            print_properties(cmd_ctx, result, output_format)
    elif isinstance(result, str):
        cmd_ctx.spinner.stop()
        click.echo(result)
    elif result is None:
        pass
    else:
        raise click.ClickException(f"Unknown result type: {type(result)}")


def cmd_http_get(cmd_ctx, uri, options):
    # pylint: disable=missing-function-docstring
    unpack = options['unpack']

    try:
        result = cmd_ctx.session.get(uri)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    print_result(cmd_ctx, result, cmd_ctx.output_format, unpack)


def cmd_http_post(cmd_ctx, uri, request_body, options):
    # pylint: disable=missing-function-docstring
    unpack = options['unpack']

    if request_body:
        # Try to parse the specified string as JSON. That needs to be done
        # to get the correct Content-Type set.
        try:
            request_body = json.loads(request_body)
            # It is JSON -> use Content-Type: application/json
        except json.JSONDecodeError:
            pass
            # It remains a string -> use Content-Type: application/octet-string

    try:
        result = cmd_ctx.session.post(
            uri, body=request_body, wait_for_completion=True)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    print_result(cmd_ctx, result, cmd_ctx.output_format, unpack)


def cmd_http_delete(cmd_ctx, uri):
    # pylint: disable=missing-function-docstring

    try:
        result = cmd_ctx.session.delete(uri)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    print_result(cmd_ctx, result, cmd_ctx.output_format)
