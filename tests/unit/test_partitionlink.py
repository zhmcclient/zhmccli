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
Unit tests for the 'zhmc partitionlink' command group, using mocked
zhmcclient objects.
"""

from unittest import mock
import pytest
import click

from zhmccli import _cmd_partitionlink as pl_mod


def make_cmd_ctx():
    """Return a mocked command context."""
    cmd_ctx = mock.MagicMock()
    cmd_ctx.error_format = 'msg'
    return cmd_ctx


def make_port(uri):
    """Return a mocked port with the specified URI."""
    port = mock.MagicMock()
    port.uri = uri
    return port


TESTCASES_ATTACH_DETACH = [
    # pl_type, exp_attach_method, exp_detach_method
    ('ctc', 'attach_ctc_link', 'detach_ctc_link'),
    ('hipersockets', 'attach_network_link', 'detach_network_link'),
    ('smc-d', 'attach_network_link', 'detach_network_link'),
]


@pytest.mark.parametrize(
    "pl_type, exp_attach_method, exp_detach_method",
    TESTCASES_ATTACH_DETACH)
@pytest.mark.parametrize("attach", [True, False])
def test_attach_detach_partition(
        pl_type, exp_attach_method, exp_detach_method, attach):
    """
    Test that 'attach-partition' and 'detach-partition' use the Partition
    method that matches the type of the partition link.
    """
    cmd_ctx = make_cmd_ctx()
    partition = mock.MagicMock()
    partitionlink = mock.MagicMock()
    partitionlink.name = 'pl1'
    partitionlink.get_property.side_effect = \
        lambda name: pl_type if name == 'type' else 'cpc-uri1'
    cpc = mock.MagicMock()
    cpc.partitions.find.return_value = partition

    with mock.patch.object(pl_mod.zhmcclient, 'Client') as client_cls, \
            mock.patch.object(pl_mod, 'find_partitionlink',
                              return_value=partitionlink):
        client_cls.return_value.cpcs.find.return_value = cpc
        if attach:
            pl_mod.cmd_partitionlink_attach_partition(
                cmd_ctx, 'pl1', {'partition': 'part1'})
            exp_method, other_method = exp_attach_method, exp_detach_method
        else:
            pl_mod.cmd_partitionlink_detach_partition(
                cmd_ctx, 'pl1', {'partition': 'part1'})
            exp_method, other_method = exp_detach_method, exp_attach_method

    # The CPC is found via the CPC URI of the partition link, the partition is
    # looked up by name in that CPC, and the Partition method receives exactly
    # the partition link object.
    client_cls.return_value.cpcs.find.assert_called_once_with(
        **{'object-uri': 'cpc-uri1'})
    cpc.partitions.find.assert_called_once_with(name='part1')
    getattr(partition, exp_method).assert_called_once_with(partitionlink)
    getattr(partition, other_method).assert_not_called()
    other_type_methods = {
        'attach_ctc_link', 'detach_ctc_link',
        'attach_network_link', 'detach_network_link'}
    for name in other_type_methods - {exp_method}:
        getattr(partition, name).assert_not_called()


def test_build_ctc_paths():
    """
    Test build_ctc_paths() with valid --path values, with ports specified by
    name and by index.
    """
    cmd_ctx = make_cmd_ctx()
    client = mock.MagicMock()
    ports = {
        ('FICON1', '0'): make_port('/p/f1-0'),
        ('FICON2', 'Port 1'): make_port('/p/f2-1'),
    }

    def find_port(*args):
        # args: cmd_ctx, client, cpc_name, adapter_name, port_name
        return ports[(args[3], args[4])]

    with mock.patch.object(pl_mod, 'find_port', side_effect=find_port):
        paths = pl_mod.build_ctc_paths(
            cmd_ctx, client, 'CPC1', ["[FICON1, 0, FICON2, 'Port 1']"])

    assert paths == [{
        'adapter-port-uri': '/p/f1-0',
        'connecting-adapter-port-uri': '/p/f2-1',
    }]


@pytest.mark.parametrize(
    "value",
    ['[FICON1, 0, FICON2]', '[FICON1, 0, FICON2, 0, X]', 'FICON1', '{a: b}'])
def test_build_ctc_paths_invalid(value):
    """
    Test build_ctc_paths() with values that are not a list of 4 items.
    """
    cmd_ctx = make_cmd_ctx()
    client = mock.MagicMock()

    with mock.patch.object(pl_mod, 'find_port') as find_port:
        with pytest.raises(click.ClickException) as exc_info:
            pl_mod.build_ctc_paths(cmd_ctx, client, 'CPC1', [value])
        find_port.assert_not_called()

    assert "'--path'" in exc_info.value.message


def create_options(**kwargs):
    """Return click-style options for cmd_partitionlink_create()."""
    options = {
        'name': 'pl1',
        'type': 'ctc',
        'description': None,
        'starting_devno': None,
        'mtu_size': None,
        'starting_fid': None,
        'partition': (),
        'path': (),
        'devices_per_path': None,
    }
    options.update(kwargs)
    return options


def test_create_ctc():
    """
    Test that 'partitionlink create --type ctc' passes the partition URIs and
    the paths to the create operation, and does not pass the options that are
    not set.
    """
    cmd_ctx = make_cmd_ctx()
    cpc = mock.MagicMock()
    cpc.uri = '/api/cpcs/c1'
    part1 = mock.MagicMock()
    part1.uri = '/api/partitions/p1'
    part2 = mock.MagicMock()
    part2.uri = '/api/partitions/p2'
    cpc.partitions.find.side_effect = [part1, part2]
    paths = [{'adapter-port-uri': '/a1', 'connecting-adapter-port-uri': '/a2'}]
    console = mock.MagicMock()
    console.partition_links.create.return_value.properties = {'name': 'pl1'}

    with mock.patch.object(pl_mod.zhmcclient, 'Client') as client_cls, \
            mock.patch.object(pl_mod, 'find_cpc', return_value=cpc), \
            mock.patch.object(pl_mod, 'build_ctc_paths',
                              return_value=paths) as build_paths:
        client_cls.return_value.consoles.console = console
        pl_mod.cmd_partitionlink_create(
            cmd_ctx, 'CPC1',
            create_options(
                partition=('P1', 'P2'), path=('[A, 0, B, 0]',),
                devices_per_path=2))

    build_paths.assert_called_once()
    console.partition_links.create.assert_called_once_with({
        'name': 'pl1',
        'type': 'ctc',
        'devices-per-path': 2,
        'cpc-uri': '/api/cpcs/c1',
        'partitions': ['/api/partitions/p1', '/api/partitions/p2'],
        'paths': paths,
    })


@pytest.mark.parametrize(
    "pl_type, partition, path, exp_msg",
    [
        ('ctc', (), ('[A, 0, B, 0]',), "'--partition' is required"),
        ('ctc', ('P1',), (), "'--path' is required"),
        ('hipersockets', ('P1',), (), "valid only for partition links of "
         "type ctc"),
        ('smc-d', (), ('[A, 0, B, 0]',), "valid only for partition links of "
         "type ctc"),
    ])
def test_create_invalid_options(pl_type, partition, path, exp_msg):
    """
    Test that 'partitionlink create' rejects missing or misplaced
    --partition and --path options, without calling the create operation.
    """
    cmd_ctx = make_cmd_ctx()
    cpc = mock.MagicMock()
    console = mock.MagicMock()

    with mock.patch.object(pl_mod.zhmcclient, 'Client') as client_cls, \
            mock.patch.object(pl_mod, 'find_cpc', return_value=cpc):
        client_cls.return_value.consoles.console = console
        with pytest.raises(click.ClickException) as exc_info:
            pl_mod.cmd_partitionlink_create(
                cmd_ctx, 'CPC1',
                create_options(type=pl_type, partition=partition, path=path))

    assert exp_msg in exc_info.value.message
    console.partition_links.create.assert_not_called()


def test_create_hipersockets_unchanged():
    """
    Test that creating a non-CTC partition link does not pass 'partitions' or
    'paths' to the create operation.
    """
    cmd_ctx = make_cmd_ctx()
    cpc = mock.MagicMock()
    cpc.uri = '/api/cpcs/c1'
    console = mock.MagicMock()
    console.partition_links.create.return_value.properties = {'name': 'pl1'}

    with mock.patch.object(pl_mod.zhmcclient, 'Client') as client_cls, \
            mock.patch.object(pl_mod, 'find_cpc', return_value=cpc):
        client_cls.return_value.consoles.console = console
        pl_mod.cmd_partitionlink_create(
            cmd_ctx, 'CPC1',
            create_options(type='hipersockets', mtu_size=16))

    console.partition_links.create.assert_called_once_with({
        'name': 'pl1',
        'type': 'hipersockets',
        'maximum-transmission-unit-size': 16,
        'cpc-uri': '/api/cpcs/c1',
    })
