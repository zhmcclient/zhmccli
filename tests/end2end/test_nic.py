# Copyright 2025 IBM Corp. All Rights Reserved.
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
End2end tests for the 'zhmc nic' command group.
"""

import urllib3
import pytest
# pylint: disable=unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils import dpm_mode_cpcs  # noqa: F401, E501
# pylint: enable=unused-import

from .utils import run_zhmc, parse_output, pick_test_resources, fixup

urllib3.disable_warnings()


# Expected output properties for 'nic list' when --names-only option is specif.
NIC_LIST_PROPNAMES_NAMES_ONLY = [
    "cpc",
    "partition",
    "name",
]

# Expected output properties for 'nic list' when no other options are specified
NIC_LIST_PROPNAMES_DEFAULT = NIC_LIST_PROPNAMES_NAMES_ONLY + [
    "description",
    "type",
]

# Expected output properties for 'nic list' when --uri option is specified
NIC_LIST_PROPNAMES_URI = NIC_LIST_PROPNAMES_DEFAULT + [
    "element-uri",
]

# Expected output properties for 'nic list' when --all option is specified.
# Note: These are the z15 properties for a non-SSC-mgmt NIC that are common
# for all backing adapter types. Additional properties may be shown.
NIC_LIST_PROPNAMES_ALL = [
    "class",
    "description",
    "device-number",
    "element-id",
    "element-uri",
    "mac-address",
    "name",
    "parent",
    "ssc-management-nic",
    "type",
    "vlan-id",
]

# Expected output properties for 'nic show'.
# Note: These are the z15 properties for a non-SSC-mgmt NIC that are common
# for all backing adapter types. Additional properties may be shown.
NIC_SHOW_PROPNAMES = [
    "class",
    "description",
    "device-number",
    "element-id",
    "element-uri",
    "mac-address",
    "network-adapter-name",
    "network-adapter-port-index",
    "network-adapter-port-name",
    "name",
    "parent",
    "parent-name",
    "ssc-management-nic",
    "type",
    "vlan-id",
]

# Properties that should be skipped when verifying values
# (e.g. because they are volatile or have string conversion issues)
NIC_PROPNAMES_SKIP = [
    "device-number",  # CSV does not retain leading zeros
]

# Properties that need to be forced to string type in CSV tests
NIC_PROPNAMES_CSV_STR = [
    "description",  # May be empty string which by default becomes None
    "device-number",  # CSV does not retain leading zeros
]


def add_backing_adapter_properties(nic, properties):
    """
    Add artificial properties for the backing network adapter of the nic to the
    properties.
    """
    try:
        vswitch_uri = nic.get_property('virtual-switch-uri')
    except KeyError:
        pass
    else:
        vswitch_props = nic.manager.session.get(vswitch_uri)
        adapter_uri = vswitch_props['backing-adapter-uri']
        cpc = nic.manager.parent.manager.parent
        adapter = cpc.adapters.resource_object(adapter_uri)
        properties['network-adapter-name'] = adapter.name
        port_index = vswitch_props['port']
        properties['network-adapter-port-index'] = port_index
        port = adapter.ports.find(index=port_index)
        properties['network-adapter-port-name'] = port.name

    try:
        port_uri = nic.get_property('network-adapter-port-uri')
    except KeyError:
        pass
    else:
        port_props = nic.manager.session.get(port_uri)
        properties['network-adapter-port-name'] = port_props['name']
        properties['network-adapter-port-index'] = port_props['index']
        adapter_props = nic.manager.session.get(port_props['parent'])
        properties['network-adapter-name'] = adapter_props['name']


TESTCASES_NIC_LIST = [
    # Testcases for test_nic_list()
    # Each list item is a testcase, which is a tuple with items:
    # - options (list of str): Options for 'zhmc nic list' command
    # - exp_props (list of str): Expected property names in output
    # - exact (bool): If True, the output property names must be exactly the
    #   expected properties. If False, additional properties are allowed.
    (
        ['--names-only'],
        NIC_LIST_PROPNAMES_NAMES_ONLY,
        True,
    ),
    (
        [],
        NIC_LIST_PROPNAMES_DEFAULT,
        True,
    ),
    (
        ['--uri'],
        NIC_LIST_PROPNAMES_URI,
        True,
    ),
    (
        ['--all'],
        NIC_LIST_PROPNAMES_ALL,
        False,
    ),
]


@pytest.mark.parametrize(
    "options, exp_props, exact",
    TESTCASES_NIC_LIST
)
@pytest.mark.parametrize(
    "out_format",
    ['json', 'csv']
)
def test_nic_list(
        out_format, options, exp_props, exact, dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test 'nic list' command.
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        for partition in pick_test_resources(cpc.partitions.list()):

            exp_nics = partition.nics.list()
            exp_nics_props = {nic.name:
                              dict(nic.properties) for nic in exp_nics}
            # Add artificial properties
            for nic in exp_nics:
                nic_props = exp_nics_props[nic.name]
                nic_props['cpc'] = cpc.name
                nic_props['partition'] = partition.name

            args = ['-o', out_format, 'nic', 'list', cpc.name, partition.name] \
                + options
            rc, stdout, stderr = run_zhmc(args)

            assert rc == 0, (
                f"Unexpected rc={rc} (expected 0),\n"
                f"stdout:\n{stdout}\n"
                f"stderr:\n{stderr}\n"
            )
            assert stderr == ""

            nic_list = parse_output(stdout, out_format, list)

            assert len(nic_list) == len(exp_nics_props)
            for nic_item in nic_list:
                assert 'name' in nic_item
                nic_name = nic_item['name']
                assert nic_name in exp_nics_props
                exp_nic_props = exp_nics_props[nic_name]
                for pname in exp_props:
                    assert pname in nic_item
                    if pname not in NIC_PROPNAMES_SKIP:
                        exp_value = exp_nic_props.get(pname, 'undefined')
                        if out_format == 'csv':
                            force_type = \
                                str if pname in NIC_PROPNAMES_CSV_STR else None
                            value = fixup(nic_item[pname], force_type)
                        else:
                            value = nic_item[pname]
                        assert value == exp_value, (
                            f"Unexpected value for property {pname} of "
                            f"NIC {nic_name} in partition {partition.name} on "
                            f"CPC {cpc.name}:\n"
                            f"Expected: {exp_value!r}\n"
                            f"Actual: {value!r}"
                        )
                if exact:
                    assert len(nic_item) == len(exp_props)


@pytest.mark.parametrize(
    "nic_type",
    ["osd", "iqd", "cna", "roce", "osh", "neth", "netd"]
)
@pytest.mark.parametrize(
    "out_format",
    ['json', 'csv']
)
def test_nic_show(
        out_format, nic_type, dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test 'nic show' command.
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        # In the first call to this test function, list the NICs of all
        # partitions of the CPC and store the result on the CPC object,
        # for fast retrieval in the subsequent calls to this test function.
        if hasattr(cpc, 'nic_list'):
            nic_list = getattr(cpc, 'nic_list')
        else:
            nic_list = []
            for partition in cpc.partitions.list():
                for nic in partition.nics.list():
                    nic_list.append(nic)
            setattr(cpc, 'nic_list', nic_list)

        # Select the NICS of the desired type
        typed_nic_list = []
        for nic in nic_list:
            if nic.prop('type') == nic_type:
                typed_nic_list.append(nic)
        if not typed_nic_list:
            pytest.skip(f"The partitions on CPC {cpc.name} do not have any "
                        f"NICs of type {nic_type}")

        for nic in pick_test_resources(typed_nic_list):
            partition = nic.manager.parent
            cpc = partition.manager.parent

            rc, stdout, stderr = run_zhmc(
                ['-o', out_format, 'nic', 'show', cpc.name, partition.name,
                 nic.name])

            assert rc == 0, (
                f"Unexpected rc={rc} (expected 0),\n"
                f"stdout:\n{stdout}\n"
                f"stderr:\n{stderr}\n"
            )
            assert stderr == ""

            nic_props = parse_output(stdout, out_format, dict)

            exp_nic_props = dict(nic.properties)
            exp_nic_props['parent-name'] = partition.name
            add_backing_adapter_properties(nic, exp_nic_props)

            for pname in NIC_SHOW_PROPNAMES:
                assert pname in nic_props
                if pname not in NIC_PROPNAMES_SKIP:
                    exp_value = exp_nic_props.get(pname, 'undefined')
                    if out_format == 'csv':
                        force_type = \
                            str if pname in NIC_PROPNAMES_CSV_STR else None
                        value = fixup(nic_props[pname], force_type)
                    else:
                        value = nic_props[pname]
                    assert value == exp_value, (
                        f"Unexpected value for property {pname} of "
                        f"NIC {nic.name} in partition {partition.name} on "
                        f"CPC {cpc.name}:\n"
                        f"Expected: {exp_value!r}\n"
                        f"Actual: {value!r}"
                    )


# TODO: Add test function for 'nic create'
# TODO: Add test function for 'nic update'
# TODO: Add test function for 'nic delete'
