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
End2end tests for the 'zhmc cpc' command group.
"""

import urllib3
import pytest
import zhmcclient
# pylint: disable=unused-import
from zhmcclient.testutils import hmc_definition  # noqa: F401
from .utils import zhmc_session  # noqa: F401
# pylint: enable=unused-import

from .utils import run_zhmc, parse_output, pick_test_resources, fixup

urllib3.disable_warnings()


# Expected output properties when --names-only option is specified
CPC_PROPS_NAMES_ONLY = [
    "name",
]

# Expected output properties when no other options are specified
CPC_PROPS_DEFAULT = CPC_PROPS_NAMES_ONLY + [
    "description",
    "dpm-enabled",
    "machine-model",
    "machine-serial-number",
    "machine-type",
    "se-version",
    "status",
]

# Expected output properties when --uri option is specified
CPC_PROPS_URI = CPC_PROPS_DEFAULT + [
    "object-uri",
]

# Expected output properties when --all option is specified
# Note: These are the z15 properties. Additional properties are allowed.
CPC_PROPS_ALL = [
    "acceptable-status",
    "additional-status",
    "auto-start-list",
    "available-features-list",
    "cbu-activation-date",
    "cbu-expiration-date",
    "cbu-number-of-tests-left",
    "class",
    "cpc-node-descriptor",
    "cpc-power-cap-allowed",
    "cpc-power-cap-current",
    "cpc-power-cap-maximum",
    "cpc-power-cap-minimum",
    "cpc-power-capping-state",
    "cpc-power-consumption",
    "cpc-power-rating",
    "cpc-power-save-allowed",
    "cpc-power-saving",
    "cpc-power-saving-state",
    "cpc-serial-number",
    "degraded-status",
    "description",
    "dpm-enabled",
    "ec-mcl-description",
    "global-primary-key-hash",
    "global-secondary-key-hash",
    "has-automatic-se-switch-enabled",
    "has-hardware-messages",
    "has-temporary-capacity-change-allowed",
    "has-unacceptable-status",
    "host-primary-key-hash",
    "host-secondary-key-hash",
    "iml-mode",
    "is-cbu-activated",
    "is-cbu-enabled",
    "is-cbu-installed",
    "is-cpacf-enabled",
    "is-global-key-installed",
    "is-host-key-installed",
    "is-locked",
    "is-on-off-cod-activated",
    "is-on-off-cod-enabled",
    "is-on-off-cod-installed",
    "is-real-cbu-available",
    "is-secure-execution-enabled",
    "is-service-required",
    "lan-interface1-address",
    "lan-interface1-type",
    "lan-interface2-address",
    "lan-interface2-type",
    "last-energy-advice-time",
    "machine-model",
    "machine-serial-number",
    "machine-type",
    "management-world-wide-port-name",
    "maximum-alternate-storage-sites",
    "maximum-fid-number",
    "maximum-hipersockets",
    "maximum-ism-vchids",
    "maximum-partitions",
    "minimum-fid-number",
    "msu-permanent",
    "msu-permanent-plus-billable",
    "msu-permanent-plus-temporary",
    "name",
    "network1-ipv4-alt-ipaddr",
    "network1-ipv4-mask",
    "network1-ipv4-pri-ipaddr",
    "network1-ipv6-info",
    "network2-ipv4-alt-ipaddr",
    "network2-ipv4-mask",
    "network2-ipv4-pri-ipaddr",
    "network2-ipv6-info",
    "object-id",
    "object-uri",
    "on-off-cod-activation-date",
    "parent",
    "processor-count-aap",
    "processor-count-defective",
    "processor-count-general-purpose",
    "processor-count-icf",
    "processor-count-ifl",
    "processor-count-iip",
    "processor-count-pending",
    "processor-count-pending-aap",
    "processor-count-pending-general-purpose",
    "processor-count-pending-icf",
    "processor-count-pending-ifl",
    "processor-count-pending-iip",
    "processor-count-pending-service-assist",
    "processor-count-service-assist",
    "processor-count-spare",
    "se-version",
    "sna-name",
    "software-model-permanent",
    "software-model-permanent-plus-billable",
    "software-model-permanent-plus-temporary",
    "status",
    "storage-customer",
    "storage-customer-available",
    "storage-customer-central",
    "storage-customer-expanded",
    "storage-hardware-system-area",
    "storage-total-installed",
    "storage-vfm-increment-size",
    "storage-vfm-total",
    "zcpc-ambient-temperature",
    "zcpc-dew-point",
    "zcpc-environmental-class",
    "zcpc-exhaust-temperature",
    "zcpc-heat-load",
    "zcpc-heat-load-forced-air",
    "zcpc-heat-load-water",
    "zcpc-humidity",
    "zcpc-maximum-inlet-air-temperature",
    "zcpc-maximum-inlet-liquid-temperature",
    "zcpc-maximum-potential-heat-load",
    "zcpc-maximum-potential-power",
    "zcpc-minimum-inlet-air-temperature",
    "zcpc-power-cap-allowed",
    "zcpc-power-cap-current",
    "zcpc-power-cap-maximum",
    "zcpc-power-cap-minimum",
    "zcpc-power-capping-state",
    "zcpc-power-consumption",
    "zcpc-power-rating",
    "zcpc-power-save-allowed",
    "zcpc-power-saving",
    "zcpc-power-saving-state",
]

# Properties that should be skipped when verifying values
# (e.g. because they are volatile or have string conversion issues)
CPC_PROPS_SKIP = [
    # Volatile properties
    "cpc-power-consumption",
    "zcpc-ambient-temperature",
    "zcpc-dew-point",
    "zcpc-exhaust-temperature",
    "zcpc-heat-load",
    "zcpc-heat-load-forced-air",
    "zcpc-heat-load-water",
    "zcpc-humidity",
    "zcpc-maximum-inlet-air-temperature",
    "zcpc-maximum-inlet-liquid-temperature",
    "zcpc-maximum-potential-heat-load",
    "zcpc-maximum-potential-power",
    "zcpc-minimum-inlet-air-temperature",
    "zcpc-power-consumption",
    # Skipped for other reasons
    "cpc-node-descriptor",  # '00' cannot be recreated from int 0
]

# Properties that need to be forced to string type in CSV tests
CPC_PROPS_CSV_STR = [
    "additional-status",  # May be empty string which by default becomes None
    "description",  # May be empty string which by default becomes None
    "machine-serial-number",  # May be all digits which by default becomes int
    "machine-type",  # May be all digits which by default becomes int
    "software-model-permanent",  # May be all digits
    "software-model-permanent-plus-billable",  # May be all digits
    "software-model-permanent-plus-temporary",  # May be all digits
    "software-model-purchased",  # May be all digits
]

TESTCASES_CPC_LIST = [
    # Testcases for test_cpc_list()
    # Each list item is a testcase, which is a tuple with items:
    # - options (list of str): Options for 'zhmc cpc list' command
    # - exp_props (list of str): Expected property names in output
    # - exact (bool): If True, the output property names must be exactly the
    #   expected properties. If False, additional properties are allowed.
    (
        ['--names-only'],
        CPC_PROPS_NAMES_ONLY,
        True,
    ),
    (
        [],
        CPC_PROPS_DEFAULT,
        True,
    ),
    (
        ['--uri'],
        CPC_PROPS_URI,
        True,
    ),
    (
        ['--all'],
        CPC_PROPS_ALL,
        False,
    ),
]


@pytest.mark.parametrize(
    "options, exp_props, exact",
    TESTCASES_CPC_LIST
)
@pytest.mark.parametrize(
    "out_format",
    ['json', 'csv']
)
def test_cpc_list(
        zhmc_session, out_format, options, exp_props, exact):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test 'cpc list' command for output formats json and csv.
    """
    client = zhmcclient.Client(zhmc_session)
    cpcs = client.cpcs.list()

    args = ['-o', out_format, 'cpc', 'list'] + options
    rc, stdout, stderr = run_zhmc(args)

    assert rc == 0
    assert stderr == ""

    out_list = parse_output(stdout, out_format, list)

    assert len(out_list) == len(cpcs)
    exp_cpc_dict = {cpc.name: cpc for cpc in cpcs}
    for out_item in out_list:
        assert 'name' in out_item
        cpc_name = out_item['name']
        assert cpc_name in exp_cpc_dict
        exp_cpc = exp_cpc_dict[cpc_name]
        for pname in exp_props:
            assert pname in out_item
            if pname not in CPC_PROPS_SKIP:
                exp_value = exp_cpc.prop(pname, 'undefined')
                if out_format == 'csv':
                    force_type = str if pname in CPC_PROPS_CSV_STR else None
                    value = fixup(out_item[pname], force_type)
                else:
                    value = out_item[pname]
                assert value == exp_value, (
                    f"Unexpected value for property {pname} of "
                    f"CPC {cpc_name}:\n"
                    f"Expected: {exp_value!r}\n"
                    f"Actual: {value!r}"
                )
        if exact:
            assert len(out_item) == len(exp_props)


@pytest.mark.parametrize(
    "out_format",
    ['json', 'csv']
)
def test_cpc_show(zhmc_session, out_format):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test 'cpc show' command in the most simple way.
    """
    client = zhmcclient.Client(zhmc_session)
    cpcs = client.cpcs.list()
    cpcs = pick_test_resources(cpcs)

    for cpc in cpcs:

        rc, stdout, stderr = run_zhmc(
            ['-o', out_format, 'cpc', 'show', cpc.name])

        assert rc == 0
        assert stderr == ""

        out_dict = parse_output(stdout, out_format, dict)

        assert out_dict['name'] == cpc.name


# TODO: Add tests for 'cpc list-api-features' command
# TODO: Add tests for 'cpc dpm-export' command
# TODO: Add tests for 'cpc list-firmware' command
# TODO: Add tests for 'cpc get-em-data' command

# Note: We do not have end2end tests for modifying commands:
# 'cpc dpm-import'
# 'cpc update'
# 'cpc upgrade'
# 'cpc install-firmware'
# 'cpc delete-uninstalled-firmware'
# 'cpc set-power-capping'
