# Copyright 2023 IBM Corp. All Rights Reserved.
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
End2end tests for the 'zhmc session' command group.
"""

from __future__ import absolute_import, print_function

import os
import re
from requests.packages import urllib3

# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import zhmc_session_args, run_zhmc

urllib3.disable_warnings()


def test_session_success(hmc_definition):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test successful creation and deletion of an HMC session.
    """

    # Create the session

    # Set to True to debug 'zhmc session create'
    pdb = False

    zhmc_args = zhmc_session_args(hmc_definition) + ['session', 'create']

    # The code to be tested
    rc, stdout, stderr = run_zhmc(zhmc_args, pdb=pdb)

    if not pdb:
        assert rc == 0, \
            "Unexpected exit code: {}\nstdout:\n{}\nstderr:\n{}". \
            format(rc, stdout, stderr)
        assert stderr == '', \
            "Unexpected stderr:\n{}".format(stderr)

        export_vars = {}
        unset_vars = {}
        for line in stdout.splitlines():
            m = re.match(r'^unset (ZHMC_[A-Z_]+)$', line)
            if m:
                name = m.group(1)
                unset_vars[name] = True
                continue
            m = re.match(r'^export (ZHMC_[A-Z_]+)=(.*)$', line)
            if m:
                name = m.group(1)
                value = m.group(2)
                export_vars[name] = value
                continue
            raise AssertionError("Unexpected line on stdout: {!r}".format(line))

        assert 'ZHMC_HOST' in export_vars
        zhmc_host = export_vars.pop('ZHMC_HOST')
        assert zhmc_host == hmc_definition.host

        assert 'ZHMC_USERID' in export_vars
        zhmc_userid = export_vars.pop('ZHMC_USERID')
        assert zhmc_userid == hmc_definition.userid

        assert 'ZHMC_SESSION_ID' in export_vars
        zhmc_session_id = export_vars.pop('ZHMC_SESSION_ID')

        if hmc_definition.verify:
            assert 'ZHMC_NO_VERIFY' in unset_vars
            _ = unset_vars.pop('ZHMC_NO_VERIFY')
        else:
            assert 'ZHMC_NO_VERIFY' in export_vars
            zhmc_no_verify = export_vars.pop('ZHMC_NO_VERIFY')
            assert bool(zhmc_no_verify) is True

        if hmc_definition.ca_certs is None:
            assert 'ZHMC_CA_CERTS' in unset_vars
            _ = unset_vars.pop('ZHMC_CA_CERTS')
        else:
            assert 'ZHMC_CA_CERTS' in export_vars
            zhmc_ca_certs = export_vars.pop('ZHMC_CA_CERTS')
            assert zhmc_ca_certs == hmc_definition.ca_certs

        assert not export_vars
        assert not unset_vars

    # Delete the session

    # Set to True to debug 'zhmc session delete'
    pdb = False

    zhmc_args = ['session', 'delete']

    # Setup the environment is it was returned from session create
    env = dict(os.environ)
    env['ZHMC_SESSION_ID'] = zhmc_session_id
    env['ZHMC_HOST'] = zhmc_host
    env['ZHMC_USERID'] = zhmc_userid
    if not hmc_definition.verify:
        env['ZHMC_NO_VERIFY'] = zhmc_no_verify
    if hmc_definition.ca_certs:
        env['ZHMC_CA_CERTS'] = zhmc_ca_certs

    # The code to be tested
    rc, stdout, stderr = run_zhmc(zhmc_args, env=env, pdb=pdb)

    if not pdb:
        assert rc == 0, \
            "Unexpected exit code: {}\nstdout:\n{}\nstderr:\n{}". \
            format(rc, stdout, stderr)
        assert stderr == '', \
            "Unexpected stderr:\n{}".format(stderr)

        unset_vars = {}
        for line in stdout.splitlines():
            m = re.match(r'^unset (ZHMC_[A-Z_]+)$', line)
            if m:
                name = m.group(1)
                unset_vars[name] = True
                continue
            raise AssertionError("Unexpected line on stdout: {!r}".format(line))

        assert 'ZHMC_SESSION_ID' in unset_vars
        _ = unset_vars.pop('ZHMC_SESSION_ID')

        assert not unset_vars
