# Copyright 2021 IBM Corp. All Rights Reserved.
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
Commands for HMC user role management.
"""

from __future__ import absolute_import
from __future__ import print_function

import re

import click

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_resources, abort_if_false, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS, ObjectByUriCache


PERMISSION_OPTIONS = [
    click.option('--task', type=str, metavar='TASK', required=False,
                 help='Permission: Task permission to the task with the '
                 'specified name.'),
    click.option('--view-only', type=bool, required=False,
                 help='If --task was specified, indicates whether the task\'s '
                 'view-only version is subject of the permission. Only certain '
                 'tasks have a view-only version. Default: True.'),
    click.option('--class', type=str, metavar='CLASS', required=False,
                 help='Permission: Object permission to all objects of the '
                 'specified resource class (= value of "class" property).'),
    click.option('--group', type=str, metavar='GROUP', required=False,
                 help='Permission: Object permission to the group with the '
                 'specified name and optionally to its members.'),
    click.option('--include-members', type=bool, required=False,
                 help='If --group was specified, indicates whether the group '
                 'members are included in the permission. Default: False.'),
    click.option('--cpc', type=str, metavar='CPC', required=False,
                 help='Permission: Object permission to the CPC with the '
                 'specified name.'),
    click.option('--partition', type=str,
                 metavar='CPC PARTITION', nargs=2, required=False,
                 help='Permission: Object permission to the partition on the '
                 'CPC with the specified names.'),
    click.option('--lpar', type=str,
                 metavar='CPC LPAR', nargs=2, required=False,
                 help='Permission: Object permission to the LPAR on the CPC '
                 'with the specified names.'),
    click.option('--adapter', type=str,
                 metavar='CPC ADAPTER', nargs=2, required=False,
                 help='Permission: Object permission to the adapter on the CPC '
                 'with the specified names.'),
    click.option('--storage-group', type=str,
                 metavar='CPC STORAGEGROUP', nargs=2, required=False,
                 help='Permission: Object permission to the storage group '
                 'associated with the CPC with the specified names.'),
    click.option('--storage-group-template', type=str,
                 metavar='CPC STORAGEGROUPTEMPLATE', nargs=2, required=False,
                 help='Permission: Object permission to the storage group '
                 'template associated with the CPC with the specified names.'),
]


def find_user_role(cmd_ctx, console, user_role_name):
    """
    Find a user role by name and return its resource object.
    """
    try:
        user_role = console.user_roles.find(name=user_role_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return user_role


def permission_str(obj_cache, permission_info):
    """
    Return a permission-info item as a string for displaying
    """
    obj = permission_info['permitted-object']
    obj_type = permission_info['permitted-object-type']
    if obj_type == 'object-class':
        perm_str = 'class {}'.format(obj)
    else:
        assert obj_type == 'object'
        if obj.startswith('/api/console/tasks/'):
            task = obj_cache.task_by_uri(obj)
            perm_str = "task '{}'".format(task.name)
        elif obj.startswith('/api/groups/'):
            # TODO: Display name, once zhmcclient.Group implemented
            # group = obj_cache.group_by_uri(obj)
            # perm_str = "group '{}'".format(group.name)
            perm_str = "group '{}'".format(obj)
        elif re.match(r'^/api/cpcs/[^/]+/adapters/[^/]+$', obj):
            adapter = obj_cache.adapter_by_uri(obj)
            cpc = adapter.manager.parent
            perm_str = "adapter '{}' on cpc '{}'". \
                format(adapter.name, cpc.name)
        elif re.match(r'^/api/cpcs/[^/]+/lpars/[^/]+$', obj):
            lpar = obj_cache.lpar_by_uri(obj)
            cpc = lpar.manager.parent
            perm_str = "lpar '{}' on cpc '{}'". \
                format(lpar.name, cpc.name)
        elif re.match(r'^/api/cpcs/[^/]+/partitions/[^/]+$', obj):
            partition = obj_cache.partition_by_uri(obj)
            cpc = partition.manager.parent
            perm_str = "partition '{}' on cpc '{}'". \
                format(partition.name, cpc.name)
        elif re.match(r'^/api/cpcs/[^/]+$', obj):
            cpc = obj_cache.cpc_by_uri(obj)
            perm_str = "cpc '{}'".format(cpc.name)
        elif re.match(r'^/api/storage-groups/[^/]+$', obj):
            storage_group = obj_cache.storage_group_by_uri(obj)
            cpc = storage_group.cpc
            perm_str = "storage group '{}' associated with cpc '{}'". \
                format(storage_group.name, cpc.name)
        elif re.match(r'^/api/storage-templates/[^/]+$', obj):
            # TODO: Display name, once zhmcclient list templates implemented
            # perm_str = "group '{}'".format(obj)
            # storage_template = obj_cache.storage_template_by_uri(obj)
            # cpc = storage_template.cpc
            # perm_str = "storage group template '{}' assoc. with cpc '{}'". \
            #     format(storage_template.name, cpc.name)
            perm_str = "storage group template '{}'".format(obj)
        else:
            perm_str = 'object {}'.format(obj)
    return perm_str


def permission_options_to_kwargs(cmd_ctx, client, options):
    """
    Convert the permission options to a kwargs dict of arguments for the
    respective zhmcclient methods.
    """
    opts = dict(options)
    kwargs = {}
    kwargs['include_members'] = options.pop('include_members')
    kwargs['view_only'] = options.pop('view_only')
    num_options = \
        bool(opts['task']) + \
        bool(opts['class']) + \
        bool(opts['group']) + \
        bool(opts['cpc']) + \
        bool(opts['partition']) + \
        bool(opts['adapter']) + \
        bool(opts['storage_group']) + \
        bool(opts['storage_group_template'])

    if num_options > 1:
        raise click.ClickException(
            "More than one permission option specified: {}".
            format(', '.join(opts.keys())))

    if opts['task']:
        raise NotImplementedError  # pylint: disable=no-else-raise
        # TODO: Implement once zhmccli task is implemented
        # # pylint: disable=import-outside-toplevel,cyclic-import
        # from ._cmd_task import find_task
        # task_name = opts['task']
        # task = find_task(cmd_ctx, client, task_name)
        # kwargs['permitted_object'] = task
    if opts['class']:
        class_name = opts['class']
        kwargs['permitted_object'] = class_name
    elif opts['group']:
        raise NotImplementedError  # pylint: disable=no-else-raise
        # TODO: Implement once zhmcclient.Group is implemented
        # # pylint: disable=import-outside-toplevel,cyclic-import
        # from ._cmd_group import find_group
        # group_name = opts['group']
        # group = find_group(cmd_ctx, client, group_name)
        # kwargs['permitted_object'] = group
    elif opts['cpc']:
        # pylint: disable=import-outside-toplevel,cyclic-import
        from ._cmd_cpc import find_cpc
        cpc_name = opts['cpc']
        cpc = find_cpc(cmd_ctx, client, cpc_name)
        kwargs['permitted_object'] = cpc
    elif opts['partition']:
        # pylint: disable=import-outside-toplevel,cyclic-import
        from ._cmd_partition import find_partition
        cpc_name, partition_name = opts['partition']
        partition = find_partition(cmd_ctx, client, cpc_name, partition_name)
        kwargs['permitted_object'] = partition
    elif opts['adapter']:
        # pylint: disable=import-outside-toplevel,cyclic-import
        from ._cmd_adapter import find_adapter
        cpc_name, adapter_name = opts['adapter']
        adapter = find_adapter(cmd_ctx, client, cpc_name, adapter_name)
        kwargs['permitted_object'] = adapter
    elif opts['storage_group']:
        # pylint: disable=import-outside-toplevel,cyclic-import
        from ._cmd_storagegroup import find_storagegroup
        cpc_name, stogrp_name = opts['storage_group']
        # TODO: Fix find_storagegroup() to take cpc_name
        stogrp = find_storagegroup(cmd_ctx, client, stogrp_name)
        kwargs['permitted_object'] = stogrp
    elif opts['storage_group_template']:
        raise NotImplementedError  # pylint: disable=no-else-raise
        # TODO: Implement once zhmccli storage-group-template is implemented
        # # pylint: disable=import-outside-toplevel,cyclic-import
        # from ._cmd_storagegrouptemplate import find_storagegrouptemplate
        # cpc_name, stogrptpl_name = opts['storage_group_template']
        # stogrptpl = find_storagegrouptemplate(
        #     cmd_ctx, client, cpc_name, stogrptpl_name)
        # kwargs['permitted_object'] = stogrptpl
    else:
        raise click.ClickException("No permission option specified.")

    return kwargs


@cli.group('userrole', options_metavar=COMMAND_OPTIONS_METAVAR)
def user_role_group():
    """
    Command group for managing HMC user roles.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@user_role_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@add_options(LIST_OPTIONS)
@click.option('--permissions', is_flag=True, required=False,
              help='Show additional properties for user role permissions.')
@click.pass_obj
def user_role_list(cmd_ctx, **options):
    """
    List the HMC user roles.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_user_role_list(cmd_ctx, options))


@user_role_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('USER_ROLE', type=str, metavar='USER_ROLE')
@click.pass_obj
def user_role_show(cmd_ctx, user_role):
    """
    Show the details of an HMC user role.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_user_role_show(cmd_ctx, user_role))


@user_role_group.command('create', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--name', type=str, required=True,
              help='The name of the new user role.')
@click.option('--description', type=str, required=False,
              help='The description of the new user role.')
@click.option('--associated-system-defined-user-role', type=str, required=False,
              help='The system-defined user role associated with the new '
              'user role. '
              'Default: Operator Tasks')
@click.option('--is-inheritance-enabled', type=bool, required=False,
              help='The indicator whether user role inheritance is enabled for '
              'the new user role. '
              'When enabled, if the user role permits access to a parent '
              'managed object, then all managed objects that are hosted by the '
              'parent managed object are also permitted by this role. '
              'Default: False')
@click.pass_obj
def user_role_create(cmd_ctx, **options):
    """
    Create a user-defined HMC user role.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_user_role_create(cmd_ctx, options))


@user_role_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('USER_ROLE', type=str, metavar='USER_ROLE')
@click.option('--description', type=str, required=False,
              help='The new description of the user role.')
@click.option('--associated-system-defined-user-role', type=str, required=False,
              help='The new system-defined user role associated with the '
              'user role.')
@click.option('--is-inheritance-enabled', type=bool, required=False,
              help='The new indicator whether user role inheritance is '
              'enabled for the user role. '
              'When enabled, if the user role permits access to a parent '
              'managed object, then all managed objects that are hosted by the '
              'parent managed object are also permitted by this role.')
@click.pass_obj
def user_role_update(cmd_ctx, user_role, **options):
    """
    Update the properties of an HMC user role.

    Note that HMC user roles cannot be renamed.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_user_role_update(
        cmd_ctx, user_role, options))


@user_role_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('USER_ROLE', type=str, metavar='USER_ROLE')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deletion of the user role.',
              prompt='Are you sure you want to delete this user role ?')
@click.pass_obj
def user_role_delete(cmd_ctx, user_role):
    """
    Delete a user-defined HMC user role.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_user_role_delete(cmd_ctx, user_role))


@user_role_group.command('add-permission',
                         options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('USER_ROLE', type=str, metavar='USER_ROLE')
@add_options(PERMISSION_OPTIONS)
@click.pass_obj
def user_role_add_permission(cmd_ctx, user_role, **options):
    """
    Add a permission to a user-defined HMC user role.

    The permission is specified by exactly one of the permission options,
    and optionally the --view-only or --include-members options.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_user_role_add_permission(
        cmd_ctx, user_role, options))


@user_role_group.command('remove-permission',
                         options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('USER_ROLE', type=str, metavar='USER_ROLE')
@add_options(PERMISSION_OPTIONS)
@click.pass_obj
def user_role_remove_permission(cmd_ctx, user_role, **options):
    """
    Remove a permission from a user-defined HMC user role.

    The permission is specified by exactly one of the permission options,
    and optionally the --view-only or --include-members options.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_user_role_remove_permission(
        cmd_ctx, user_role, options))


def cmd_user_role_list(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    show_list = [
        'name',
    ]
    if not options['names_only']:
        show_list.extend([
            'type',
            'description',
        ])
    if options['uri']:
        show_list.extend([
            'object-uri',
        ])
    if options['permissions']:
        show_list.extend([
            'permissions',
            'is-inheritance-enabled',
        ])

    additions = {}
    additions['permissions'] = {}

    try:
        user_roles = console.user_roles.list(full_properties=False)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    if options['permissions']:
        obj_cache = ObjectByUriCache(cmd_ctx, client)
        for role in user_roles:
            permissions = []
            for item in role.get_property('permissions'):
                permissions.append(permission_str(obj_cache, item))
            additions['permissions'][role.uri] = permissions

    try:
        print_resources(cmd_ctx, user_roles, cmd_ctx.output_format, show_list,
                        additions, all=options['all'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_user_role_show(cmd_ctx, user_role_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    user_role = find_user_role(cmd_ctx, console, user_role_name)

    try:
        user_role.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(user_role.properties)

    # Replace property 'permissions' with artificial property

    obj_cache = ObjectByUriCache(cmd_ctx, client)
    permissions = []
    for item in user_role.properties['permissions']:
        permissions.append(permission_str(obj_cache, item))
    properties['permissions'] = permissions

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def cmd_user_role_create(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    org_options = original_options(options)

    name_map = {
        'associated-system-defined-user-role': None,
    }

    properties = options_to_properties(org_options, name_map)

    if org_options['associated-system-defined-user-role'] == '':
        properties['associated-system-defined-user-role-uri'] = None
    else:
        try:
            role = console.user_roles.find_by_name(
                org_options['associated-system-defined-user-role'])
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)
        properties['associated-system-defined-user-role-uri'] = role.uri

    try:
        new_user_role = console.user_roles.create(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("New user role '{u}' has been created.".
               format(u=new_user_role.properties['name']))


def cmd_user_role_update(cmd_ctx, user_role_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    user_role = find_user_role(cmd_ctx, console, user_role_name)

    org_options = original_options(options)

    name_map = {
        'associated-system-defined-user-role': None,
    }

    properties = options_to_properties(org_options, name_map)

    if org_options['associated-system-defined-user-role'] == '':
        properties['associated-system-defined-user-role-uri'] = None
    else:
        try:
            role = console.user_roles.find_by_name(
                org_options['associated-system-defined-user-role'])
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)
        properties['associated-system-defined-user-role-uri'] = role.uri

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating user role '{u}'.".
                   format(u=user_role_name))
        return

    try:
        user_role.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("User role '{u}' has been updated.".format(u=user_role_name))


def cmd_user_role_delete(cmd_ctx, user_role_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    user_role = find_user_role(cmd_ctx, console, user_role_name)

    try:
        user_role.delete()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("User role '{u}' has been deleted.".format(u=user_role_name))


def cmd_user_role_add_permission(cmd_ctx, user_role_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    user_role = find_user_role(cmd_ctx, console, user_role_name)

    kwargs = permission_options_to_kwargs(cmd_ctx, client, options)

    try:
        user_role.add_permission(**kwargs)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("The permission has been added to user role '{r}'.".
               format(r=user_role_name))


def cmd_user_role_remove_permission(cmd_ctx, user_role_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    user_role = find_user_role(cmd_ctx, console, user_role_name)

    kwargs = permission_options_to_kwargs(cmd_ctx, client, options)

    try:
        user_role.remove_permission(**kwargs)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("The permission has been removed from user role '{r}'.".
               format(r=user_role_name))
