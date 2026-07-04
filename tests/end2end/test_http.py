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
End2end tests for the 'zhmc http' command group.
"""

import uuid
import urllib3
import pytest
import zhmcclient
# pylint: disable=unused-import
from zhmcclient.testutils import hmc_definition  # noqa: F401
from .utils import zhmc_session  # noqa: F401
# pylint: enable=unused-import

from .utils import run_zhmc, parse_output, fixup, pick_test_resources

# Controls whether the test CPC is picked according to the zhmc inventory file
# (if True) or the first CPC in the list result is used (if False).
PICK_CPC = False

urllib3.disable_warnings()


def assert_resource_list_top(
        out_dict, out_format, resources, top_property, skip_properties=None,
        csv_str_properties=None):
    """
    Assert the dict with a resource list in the command output that has a
    single top-level property against an expected list of resource objects
    retrieved via zhmcclient.
    """
    assert len(out_dict) == 1
    assert top_property in out_dict
    out_list = out_dict[top_property]

    assert_resource_list_unpacked(
        out_list, out_format, resources, skip_properties,
        csv_str_properties)


def assert_resource_list_unpacked(
        out_list, out_format, resources, skip_properties=None,
        csv_str_properties=None):
    """
    Assert a resource list in the command output that actually has been
    unpacked against an expected list of resource objects retrieved via
    zhmcclient.
    """
    assert len(out_list) == len(resources)
    exp_res_dict = {res.name: res for res in resources}
    for out_res in out_list:
        assert 'name' in out_res
        res_name = out_res['name']
        assert res_name in exp_res_dict
        exp_res = exp_res_dict[res_name]
        assert_resource(
            out_res, out_format, res_name, exp_res, skip_properties,
            csv_str_properties)


def assert_resource(
        out_res, out_format, res_name, exp_res, skip_properties=None,
        csv_str_properties=None):
    """
    Assert a resource in the command output against an expected resource
    object retrieved via zhmcclient.
    """
    for pname in out_res:
        if skip_properties and pname in skip_properties:
            continue
        exp_value = exp_res.prop(pname, 'undefined')
        if out_format == 'csv':
            if csv_str_properties and pname in csv_str_properties:
                force_type = str
            else:
                force_type = None
            value = fixup(out_res[pname], force_type)
        else:
            value = out_res[pname]
        assert value == exp_value, (
            f"Unexpected value for property {pname} of "
            f"resource {res_name}:\n"
            f"Expected: {exp_value!r}\n"
            f"Actual: {value!r}"
        )


def assert_success(rc, stdout, stderr):
    """
    Assert that the command succeeded.
    """
    assert rc == 0, (
        "Command failed:\n"
        f"stdout:\n{stdout}\n"
        f"stderr:\n{stderr}\n")
    assert stderr == ""


@pytest.mark.parametrize(
    "out_format", ['json', 'csv']
)
def test_http_get_list(zhmc_session, out_format):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test GET with a List operation
    """
    client = zhmcclient.Client(zhmc_session)
    console = client.consoles.console
    uroles = console.user_roles.list()

    args = ['-o', out_format, 'http', 'get',
            '/api/console/user-roles']
    rc, stdout, stderr = run_zhmc(args)

    assert_success(rc, stdout, stderr)
    out_dict = parse_output(stdout, out_format, dict)
    assert_resource_list_top(out_dict, out_format, uroles, 'user-roles')


@pytest.mark.parametrize(
    "out_format", ['json', 'csv']
)
def test_http_get_list_unpack(zhmc_session, out_format):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test GET with a List operation and unpack
    """
    client = zhmcclient.Client(zhmc_session)
    console = client.consoles.console
    uroles = console.user_roles.list()

    # Should unpack
    args = ['-o', out_format, 'http', 'get',
            '/api/console/user-roles',
            '--unpack']
    rc, stdout, stderr = run_zhmc(args)

    assert_success(rc, stdout, stderr)
    out_list = parse_output(stdout, out_format, list)
    assert_resource_list_unpacked(out_list, out_format, uroles)


@pytest.mark.parametrize(
    "out_format", ['json', 'csv']
)
def test_http_get_props(zhmc_session, out_format):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test GET that returns multiple properties
    """
    client = zhmcclient.Client(zhmc_session)
    console = client.consoles.console

    args = ['-o', out_format, 'http', 'get',
            f'{console.uri}']
    rc, stdout, stderr = run_zhmc(args)

    assert_success(rc, stdout, stderr)
    out_res = parse_output(stdout, out_format, dict)
    assert_resource(
        out_res, out_format, console.name, console,
        csv_str_properties=['description'])


@pytest.mark.parametrize(
    "out_format", ['json', 'csv']
)
def test_http_get_props_unpack(zhmc_session, out_format):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test GET that returns multiple properties and unpack
    """
    client = zhmcclient.Client(zhmc_session)
    console = client.consoles.console

    # Should not unpack
    args = ['-o', out_format, 'http', 'get',
            f'{console.uri}',
            '--unpack']
    rc, stdout, stderr = run_zhmc(args)

    assert_success(rc, stdout, stderr)
    out_res = parse_output(stdout, out_format, dict)
    assert_resource(
        out_res, out_format, console.name, console,
        csv_str_properties=['description'])


@pytest.mark.parametrize(
    "out_format", ['json', 'csv']
)
def test_http_get_prop_str(zhmc_session, out_format):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test GET that returns a single string property
    """
    client = zhmcclient.Client(zhmc_session)
    console = client.consoles.console

    args = ['-o', out_format, 'http', 'get',
            f'{console.uri}?properties=name']
    rc, stdout, stderr = run_zhmc(args)

    assert_success(rc, stdout, stderr)
    out_res = parse_output(stdout, out_format, dict)
    assert_resource(out_res, out_format, console.name, console)


@pytest.mark.parametrize(
    "out_format", ['json', 'csv']
)
def test_http_get_prop_str_unpack(zhmc_session, out_format):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test GET that returns a single string property and unpack
    """
    client = zhmcclient.Client(zhmc_session)
    console = client.consoles.console

    # Should not unpack, because name is a string, not a list of dicts.
    args = ['-o', out_format, 'http', 'get',
            f'{console.uri}?properties=name',
            '--unpack']
    rc, stdout, stderr = run_zhmc(args)

    assert_success(rc, stdout, stderr)
    out_res = parse_output(stdout, out_format, dict)
    assert_resource(out_res, out_format, console.name, console)


@pytest.mark.parametrize(
    "out_format", ['json', 'csv']
)
def test_http_get_prop_dict_unpack(zhmc_session, out_format):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test GET that returns a single dict property and unpack
    """
    client = zhmcclient.Client(zhmc_session)
    console = client.consoles.console

    # Should not unpack, because stp-configuration is a dict,
    # not a list of dicts.
    args = ['-o', out_format, 'http', 'get',
            '/api/console?properties=network-info',
            '--unpack']
    rc, stdout, stderr = run_zhmc(args)

    assert_success(rc, stdout, stderr)
    out_res = parse_output(stdout, out_format, dict)
    assert_resource(out_res, out_format, console.name, console)


@pytest.mark.parametrize(
    "out_format", ['json', 'csv']
)
def test_http_get_prop_list_dict(zhmc_session, out_format):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test GET that returns a single list-of-dict property
    """
    client = zhmcclient.Client(zhmc_session)
    cpcs = client.cpcs.list()
    if PICK_CPC:
        cpc = pick_test_resources(cpcs)[0]
    else:
        cpc = cpcs[0]

    args = ['-o', out_format, 'http', 'get',
            f'{cpc.uri}?properties=auto-start-list']
    rc, stdout, stderr = run_zhmc(args)

    assert_success(rc, stdout, stderr)
    out_res = parse_output(stdout, out_format, dict)
    assert_resource(out_res, out_format, cpc.name, cpc)


@pytest.mark.parametrize(
    "out_format", ['json', 'csv']
)
def test_http_get_prop_list_dict_unpack(zhmc_session, out_format):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test GET that returns a single list-of-dict property and unpack
    """
    client = zhmcclient.Client(zhmc_session)
    cpcs = client.cpcs.list()
    if PICK_CPC:
        cpc = pick_test_resources(cpcs)[0]
    else:
        cpc = cpcs[0]

    # Should unpack, because auto-start-list is a list of dicts.
    args = ['-o', out_format, 'http', 'get',
            f'{cpc.uri}?properties=auto-start-list',
            '--unpack']
    rc, stdout, stderr = run_zhmc(args)

    assert_success(rc, stdout, stderr)
    out_value = parse_output(stdout, out_format, list)
    assert out_value == cpc.prop('auto-start-list')


@pytest.mark.parametrize(
    "out_format", ['json', 'csv']
)
def test_http_get_prop_list_str_unpack(zhmc_session, out_format):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test GET that returns a single list-of-str property and unpack
    """
    client = zhmcclient.Client(zhmc_session)
    console = client.consoles.console

    # Should not unpack, because degraded-status is a list of strings,
    # not a list of dicts. However, when the list is empty, it is unpacked.
    args = ['-o', out_format, 'http', 'get',
            f'{console.uri}?properties=shutdown-delay-apps',
            '--unpack']
    rc, stdout, stderr = run_zhmc(args)

    assert_success(rc, stdout, stderr)
    prop_value = console.prop('shutdown-delay-apps')
    if prop_value == []:
        out_list = parse_output(stdout, out_format, list)
        assert out_list == []
    else:
        out_dict = parse_output(stdout, out_format, dict)
        assert_resource(out_dict, out_format, console.name, console)


@pytest.mark.parametrize(
    "out_format", ['json', 'csv']
)
def test_http_post_list_dict(out_format):
    """
    Test POST that returns a single list-of-dict property
    """

    args = ['-o', out_format, 'http', 'post',
            '/api/sessions/operations/list-sso-server-information',
            '{"redirect-uri": "https://sso.example.com/redir"}']
    rc, stdout, stderr = run_zhmc(args)

    assert_success(rc, stdout, stderr)
    out_dict = parse_output(stdout, out_format, dict)
    assert 'sso-servers' in out_dict


@pytest.mark.parametrize(
    "out_format", ['json', 'csv']
)
def test_http_post_list_dict_unpack(out_format):
    """
    Test POST that returns a single list-of-dict property and unpack
    """

    # Should unpack, because the response body has a single property that is a
    # list of dicts.
    args = ['-o', out_format, 'http', 'post',
            '/api/sessions/operations/list-sso-server-information',
            '{"redirect-uri": "https://sso.example.com/redir"}',
            '--unpack']
    rc, stdout, stderr = run_zhmc(args)

    assert_success(rc, stdout, stderr)
    out_list = parse_output(stdout, out_format, list)
    if len(out_list) > 0:
        first_item = out_list[0]
        assert isinstance(first_item, dict)


@pytest.mark.parametrize(
    "out_format", ['json', 'csv']
)
def test_http_delete_no(out_format):
    """
    Test DELETE that returns no content
    """
    urole_name = f"test_zhmccli_{uuid.uuid4()}"

    # Create a user role to prepare the deletion
    args = ['-o', out_format, 'http', 'post',
            '/api/console/user-roles',
            f'{{"name": "{urole_name}"}}']
    rc, stdout, stderr = run_zhmc(args)

    assert_success(rc, stdout, stderr)
    out_dict = parse_output(stdout, out_format, dict)
    urole_uri = out_dict['object-uri']

    # This is the actual test: Delete the user role
    args = ['-o', out_format, 'http', 'delete', urole_uri]
    rc, stdout, stderr = run_zhmc(args)

    assert_success(rc, stdout, stderr)
    assert stdout == ""
