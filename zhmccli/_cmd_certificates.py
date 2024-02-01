# Copyright 2016,2023 IBM Corp. All Rights Reserved.
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
Commands for certificates.
"""

from __future__ import absolute_import

import click

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS


def find_certificate(cmd_ctx, client, cert_name):
    """
    Find a certificate by name and return its resource object.
    """
    console = client.consoles.console
    try:
        cert = console.certificates.find(name=cert_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return cert


@cli.group('certificate', options_metavar=COMMAND_OPTIONS_METAVAR)
def certificate_group():
    """
    Command group for managing certificates.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@certificate_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--name', type=str, required=True,
              help='The name of the new certificate.')
@click.option('--cpc', type=str, required=True,
              help='The name of the CPC associated with the new certificate.')
@click.option('--certificate', type=str, required=True,
              help='The Base64 encoded string of the certificate.')
@click.option('--description', type=str, required=False,
              help='The description of the new certificate.', default="")
# at this point, only one type of certificates is supported, thus
# no user input is required
@click.pass_obj
def certificate_create(cmd_ctx, **options):
    """
    Create a certificate.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_certificate_create(cmd_ctx, options))


@certificate_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CERTIFICATE', type=str, metavar='CERTIFICATE')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the certificate.',
              prompt='Are you sure you want to delete this certificate?')
@click.pass_obj
def certificate_delete(cmd_ctx, certificate, **options):
    # pylint: disable=unused-argument
    """
    Delete a certificate.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_certificate_delete(cmd_ctx, certificate))


@certificate_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@add_options(LIST_OPTIONS)
@click.pass_obj
def certificate_list(cmd_ctx, **options):
    """
    List the certificates defined in the HMC.

    Storage groups for which the authenticated user does not have
    object-access permission will not be included.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_certificate_list(cmd_ctx, options))


@certificate_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CERTIFICATE', type=str, metavar='CERTIFICATE')
@click.pass_obj
def certificate_show(cmd_ctx, certificate):
    """
    Show the details of a certificate.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_certificate_show(cmd_ctx, certificate))


@certificate_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CERTIFICATE', type=str, metavar='storagegroup')
@click.option('--name', type=str, required=False,
              help='The new name of the certificate.')
@click.option('--description', type=str, required=False,
              help='The new description of the certificate.')
@click.pass_obj
def certificate_update(cmd_ctx, certificate, **options):
    """
    Update the properties of a certificate.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_certificate_update(cmd_ctx, certificate, options))


def cmd_certificate_create(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    try:
        cpc = client.cpcs.find(name=options['cpc'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = {
        "description": options['description'],
        "name": options['name'],
        "type": "secure-boot",
        "certificate": options['certificate'],
    }

    try:
        new_cert = console.certificates.import_certificate(cpc, properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("New certificate '{cert}' has been created.".
               format(cert=new_cert.properties['name']))


def cmd_certificate_delete(cmd_ctx, cert_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cert = find_certificate(cmd_ctx, client, cert_name)

    try:
        cert.delete()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Certificate '{cert}' has been deleted.".format(cert=cert_name))


def cmd_certificate_list(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    try:
        certificates = console.certificates.list()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    show_list = [
        'name',
    ]
    if not options['names_only']:
        show_list.extend([
            'type',
            'assigned',
            'parent-name',
            'parent',
            'sha-256-fingerprint',
            'description',
        ])
    if options['uri']:
        show_list.extend([
            'object-uri',
        ])

    try:
        print_resources(cmd_ctx, certificates, cmd_ctx.output_format, show_list,
                        None, all=options['all'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_certificate_show(cmd_ctx, cert_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cert = find_certificate(cmd_ctx, client, cert_name)

    try:
        cert.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(cert.properties)
    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def cmd_certificate_update(cmd_ctx, cert_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cert = find_certificate(cmd_ctx, client, cert_name)

    properties = options_to_properties(options, {})

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating certificate '{cert}'.".
                   format(cert=cert_name))
        return

    try:
        cert.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    if 'name' in properties and properties['name'] != cert_name:
        click.echo("Certificate '{cert}' has been renamed to '{certn}' and was "
                   "updated.".
                   format(cert=cert_name, certn=properties['name']))
    else:
        click.echo("Certificate '{cert}' has been updated.".
                   format(cert=cert_name))
