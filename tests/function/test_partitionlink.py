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
Function tests for 'zhmc partitionlink' commands, using a faked HMC
(zhmcclient mock).
"""

import pytest
from zhmcclient.mock import FakedSession
from zhmcclient.mock import _urihandler

from .utils import call_zhmc_inline, assert_rc

# The mock support for partition links is not available in older zhmcclient
# versions.
pytestmark = pytest.mark.skipif(
    not hasattr(_urihandler, 'PartitionLinksHandler'),
    reason="The installed zhmcclient mock does not support partition links")


def setup_faked_hmc():
    """
    Set up a faked HMC with one CPC in DPM mode, two partitions and two FICON
    adapters with one port each.

    Returns:
      FakedSession: The faked session.
    """
    session = FakedSession(
        'fake-host', 'hmc1', '2.16', '4.10', userid='fake-user')
    session.hmc.consoles.add({
        'object-id': None,
        'parent': None,
        'class': 'console',
        'name': 'fake-console1',
        'description': 'Console #1',
    })
    cpc = session.hmc.cpcs.add({
        'object-id': 'fake-cpc1-oid',
        'parent': None,
        'class': 'cpc',
        'name': 'CPC1',
        'description': 'CPC 1 (DPM mode)',
        'status': 'active',
        'dpm-enabled': True,
        'se-version': '2.16',
        'machine-type': '3931',
        'machine-model': 'LA1',
        'machine-serial-number': 'SN-CPC1',
    })
    for name in ('P1', 'P2'):
        cpc.partitions.add({
            'object-id': name.lower(),
            'name': name,
            'status': 'stopped',
            'description': '',
        })
    for name in ('FICON1', 'FICON2'):
        adapter = cpc.adapters.add({
            'object-id': name.lower(),
            'name': name,
            'type': 'fc',
            'adapter-family': 'ficon',
            'status': 'active',
            'state': 'online',
            'description': '',
        })
        adapter.ports.add({
            'element-id': name.lower() + '-p0',
            'name': 'Port 0',
            'index': 0,
            'description': '',
        })
    return session


def run(session, *args):
    """Run the zhmc command with the faked session."""
    return call_zhmc_inline(list(args), faked_session=session)


CTC_CREATE_ARGS = [
    'partitionlink', 'create', 'CPC1', '--name', 'L1', '--type', 'ctc',
    '--partition', 'P1', '--partition', 'P2',
    '--path', '[FICON1, 0, FICON2, 0]',
]


def test_partitionlink_create_ctc():
    """Test 'partitionlink create --type ctc' with list and show."""
    session = setup_faked_hmc()

    rc, stdout, stderr = run(session, *CTC_CREATE_ARGS)
    assert_rc(0, rc, stdout, stderr)
    assert "New partition link 'L1' has been created." in stdout

    rc, stdout, stderr = run(session, 'partitionlink', 'list')
    assert_rc(0, rc, stdout, stderr)
    assert 'L1' in stdout
    assert 'ctc' in stdout

    rc, stdout, stderr = run(session, 'partitionlink', 'show', 'L1')
    assert_rc(0, rc, stdout, stderr)
    assert '/api/adapters/ficon1/' in stdout
    assert '/api/adapters/ficon2/' in stdout

    # The partitions and the path must have been passed to the HMC
    link = session.hmc.consoles.console.partition_links.list()[0]
    assert link.properties['partitions'] == [
        '/api/partitions/p1', '/api/partitions/p2']
    assert len(link.properties['paths']) == 1


@pytest.mark.parametrize(
    "extra_args, exp_msg",
    [
        (['--type', 'ctc', '--path', '[FICON1, 0, FICON2, 0]'],
         "'--partition' is required"),
        (['--type', 'ctc', '--partition', 'P1', '--partition', 'P2'],
         "'--path' is required"),
        (['--type', 'ctc', '--partition', 'P1', '--partition', 'P2',
          '--path', '[FICON1, 0, FICON2]'],
         "Value must be a list of 4 items"),
        (['--type', 'ctc', '--partition', 'P1', '--partition', 'P2',
          '--path', '[FICON9, 0, FICON2, 0]'],
         "Could not find Adapter 'FICON9'"),
        (['--type', 'ctc', '--partition', 'PX', '--partition', 'P2',
          '--path', '[FICON1, 0, FICON2, 0]'],
         "Could not find Partition 'PX'"),
        (['--type', 'hipersockets', '--partition', 'P1'],
         "valid only for partition links of type ctc"),
    ])
def test_partitionlink_create_invalid(extra_args, exp_msg):
    """Test 'partitionlink create' with invalid option combinations."""
    session = setup_faked_hmc()

    rc, stdout, stderr = run(
        session, 'partitionlink', 'create', 'CPC1', '--name', 'L1',
        *extra_args)

    assert_rc(1, rc, stdout, stderr)
    assert exp_msg in stderr
    assert not session.hmc.consoles.console.partition_links.list()


def test_partitionlink_attach_detach_ctc():
    """Test 'partitionlink attach-partition' / 'detach-partition' for CTC."""
    session = setup_faked_hmc()
    rc, stdout, stderr = run(session, *CTC_CREATE_ARGS)
    assert_rc(0, rc, stdout, stderr)

    rc, stdout, stderr = run(
        session, 'partitionlink', 'detach-partition', 'L1',
        '--partition', 'P1')
    assert_rc(0, rc, stdout, stderr)
    assert "Partition 'P1' was detached from partition link 'L1'." in stdout

    rc, stdout, stderr = run(
        session, 'partitionlink', 'attach-partition', 'L1',
        '--partition', 'P1')
    assert_rc(0, rc, stdout, stderr)
    assert "Partition 'P1' was attached to partition link 'L1'." in stdout


@pytest.mark.parametrize("pl_type", ['hipersockets', 'smc-d'])
def test_partitionlink_attach_detach_network(pl_type):
    """
    Test 'partitionlink attach-partition' / 'detach-partition' for
    Hipersockets and SMC-D.
    """
    session = setup_faked_hmc()
    rc, stdout, stderr = run(
        session, 'partitionlink', 'create', 'CPC1', '--name', 'L1',
        '--type', pl_type)
    assert_rc(0, rc, stdout, stderr)

    rc, stdout, stderr = run(
        session, 'partitionlink', 'attach-partition', 'L1',
        '--partition', 'P1')
    assert_rc(0, rc, stdout, stderr)
    assert "Partition 'P1' was attached to partition link 'L1'." in stdout

    rc, stdout, stderr = run(
        session, 'partitionlink', 'detach-partition', 'L1',
        '--partition', 'P1')
    assert_rc(0, rc, stdout, stderr)
    assert "Partition 'P1' was detached from partition link 'L1'." in stdout


def test_plink_create_ctc_multi_paths():
    """
    Test 'partitionlink create --type ctc' with two --path options, where the
    ports are specified by index and by name, and with --devices-per-path.
    """
    session = setup_faked_hmc()

    rc, stdout, stderr = run(
        session, 'partitionlink', 'create', 'CPC1', '--name', 'L1',
        '--type', 'ctc', '--partition', 'P1', '--partition', 'P2',
        '--path', '[FICON1, 0, FICON2, 0]',
        '--path', "[FICON2, 'Port 0', FICON1, 'Port 0']",
        '--devices-per-path', '3')
    assert_rc(0, rc, stdout, stderr)

    link = session.hmc.consoles.console.partition_links.list()[0]
    port1 = '/api/adapters/ficon1/storage-ports/ficon1-p0'
    port2 = '/api/adapters/ficon2/storage-ports/ficon2-p0'
    assert link.properties['paths'] == [
        {'adapter-port-uri': port1, 'connecting-adapter-port-uri': port2},
        {'adapter-port-uri': port2, 'connecting-adapter-port-uri': port1},
    ]
    assert link.properties['devices-per-path'] == 3


def test_plink_update_ctc_devs_per_path():
    """Test 'partitionlink update --devices-per-path' on a CTC link."""
    session = setup_faked_hmc()
    rc, stdout, stderr = run(session, *CTC_CREATE_ARGS)
    assert_rc(0, rc, stdout, stderr)

    rc, stdout, stderr = run(
        session, 'partitionlink', 'update', 'L1', '--devices-per-path', '2')
    assert_rc(0, rc, stdout, stderr)
    assert "Partition link 'L1' has been updated." in stdout

    link = session.hmc.consoles.console.partition_links.list()[0]
    assert link.properties['devices-per-path'] == 2


def test_plink_delete_ctc():
    """Test 'partitionlink delete' on a CTC link."""
    session = setup_faked_hmc()
    rc, stdout, stderr = run(session, *CTC_CREATE_ARGS)
    assert_rc(0, rc, stdout, stderr)
    assert session.hmc.consoles.console.partition_links.list()

    rc, stdout, stderr = run(
        session, 'partitionlink', 'delete', 'L1', '-y')
    assert_rc(0, rc, stdout, stderr)
    assert "Partition link 'L1' has been deleted." in stdout
    assert not session.hmc.consoles.console.partition_links.list()
