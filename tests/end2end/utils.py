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
Utility functions for end2end tests.
"""


import os
import re
import subprocess
import random
import warnings
import pytest
import zhmcclient

# Prefix used for names of resources that are created during tests
TEST_PREFIX = 'zhmcclient_tests_end2end'


def env2bool(name):
    """
    Evaluate the (string) value of the specified environment variable as a
    boolean value and return the result as a bool.

    The following variable values are considered True: 'true', 'yes', '1'.
    Any other value or if the variable is not set, is considered False.
    """
    return os.getenv(name, 'false').lower() in ('true', 'yes', '1')


class End2endTestWarning(UserWarning):
    """
    Python warning indicating an issue with an end2end test.
    """
    pass


def zhmc_session_args(hmc_definition):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Return the session related command line options for zhmc from an HMC
    definition.

    Parameters:

      hmc_definition(zhmcclient.testutils.HMCDefiniton): HMC definition.

    Returns:
      list of str: zhmc session related command line options.
    """
    ret = []
    if not hmc_definition.verify:
        ret.append('-n')
    ret.extend(['-h', hmc_definition.host])
    ret.extend(['-u', hmc_definition.userid])
    ret.extend(['-p', hmc_definition.password])
    if hmc_definition.ca_certs:
        ret.extend(['-c', hmc_definition.ca_certs])
    return ret


def create_hmc_session(hmc_definition):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Create a valid HMC session.

    Returns the session ID of the HMC session.

    Raises zhmcclient exceptions if the HMC logon fails.
    """
    host = hmc_definition.host
    userid = hmc_definition.userid
    password = hmc_definition.password
    if not hmc_definition.verify:
        verify_cert = False
    elif hmc_definition.ca_certs:
        verify_cert = hmc_definition.ca_certs
    else:
        verify_cert = True
    session = zhmcclient.Session(host, userid, password,
                                 verify_cert=verify_cert)
    session.logon()
    return session.session_id


def delete_hmc_session(hmc_definition, session_id):
    """
    Delete a valid HMC session.

    Raises zhmcclient exceptions if the session ID is not valid.
    """
    host = hmc_definition.host
    userid = hmc_definition.userid
    if not hmc_definition.verify:
        verify_cert = False
    elif hmc_definition.ca_certs:
        verify_cert = hmc_definition.ca_certs
    else:
        verify_cert = True
    session = zhmcclient.Session(host, userid, session_id=session_id,
                                 verify_cert=verify_cert)
    session.logoff()


def is_valid_hmc_session(hmc_definition, session_id):
    """
    Return a boolean indicating whether an HMC session is valid.

    Raises zhmcclient exceptions if the validity cannot be determined.
    """
    host = hmc_definition.host
    userid = hmc_definition.userid
    if not hmc_definition.verify:
        verify_cert = False
    elif hmc_definition.ca_certs:
        verify_cert = hmc_definition.ca_certs
    else:
        verify_cert = True
    session = zhmcclient.Session(host, userid, session_id=session_id,
                                 verify_cert=verify_cert)
    try:
        # This simply performs the GET with the session header set to the
        # session_id.
        session.get('/api/cpcs', logon_required=False, renew_session=False)
    except zhmcclient.ServerAuthError as exc:
        if re.search(r'x-api-session header did not map to a known session',
                     str(exc)):
            return False
        raise
    return True


def run_zhmc(args, env=None, pdb_=False, log=False):
    """
    Run the zhmc command and return its exit code, stdout and stderr.

    Parameters:

      args(list/tuple of str): List of command line arguments, not including
        the 'zhmc' command name itself.

      env(dict of str/str): Environment variables to be used instead of the
        current process' variables.

      pdb_(bool): If True, debug the zhmc command. This is done by inserting
        the '--pdb' option to the command arguments, and by not capturing the
        stdout/stderr.

        If both log and pdb_ are set, only pdb_ is performed.

      log(bool): If True, enable HMC logging for the zhmc command. This is done
        by inserting the '--log hmc=debug' option to the command arguments,
        and by not capturing the stdout/stderr.

        If both log and pdb_ are set, only pdb_ is performed.

    Returns:
      tuple (rc, stdout, stderr) as follows:
      - rc(int): zhmc exit code
      - stdout(str): stdout string, or None if debugging the zhmc command
      - stderr(str): stderr string, or None if debugging the zhmc command
    """
    assert isinstance(args, (list, tuple))
    if env is not None:
        assert isinstance(env, dict)

    p_args = ['zhmc'] + args

    # Set up output capturing, dependent on pdb_ flag
    if pdb_:
        kwargs = {}
        p_args.insert(1, '--pdb')
    else:
        if log:
            p_args.insert(1, 'all=debug')
            p_args.insert(1, '--log')
        kwargs = {
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
        }

    # pylint: disable=consider-using-with
    proc = subprocess.Popen(p_args, env=env, **kwargs)

    stdout, stderr = proc.communicate()
    rc = proc.returncode
    if not pdb_:
        stdout = stdout.decode()
        stderr = stderr.decode()

    return rc, stdout, stderr


def _res_name(item):
    """Return the resource name, used by pick_test_resources()"""
    if isinstance(item, (tuple, list)):
        return item[0].name
    return item.name


def pick_test_resources(res_list):
    """
    Return the list of resources to be tested.

    The env.var "TESTRESOURCES" controls which resources are picked for the
    test, as follows:

    * 'random': (default) one random choice from the input list of resources.
    * 'all': the complete input list of resources.
    * '<pattern>': The resources with names matching the regexp pattern.

    Parameters:
      res_list (list of zhmcclient.BaseResource or tuple thereof):
        List of resources to pick from. Tuple items are a resource and its
        parent resources.

    Returns:
      list of zhmcclient.BaseResource: Picked list of resources.
    """

    test_res = os.getenv('TESTRESOURCES', 'random')

    if test_res == 'random':
        return [random.choice(res_list)]  # nosec: B311

    if test_res == 'all':
        return sorted(res_list, key=_res_name)

    # match the pattern
    ret_list = []
    for item in res_list:
        if re.search(test_res, _res_name(item)):
            ret_list.append(item)
    return sorted(ret_list, key=_res_name)


def skipif_no_storage_mgmt_feature(cpc):
    """
    Skip the test if the "DPM Storage Management" feature is not enabled for
    the specified CPC, or if the CPC does not yet support it.
    """
    try:
        smf = cpc.feature_enabled('dpm-storage-management')
    except ValueError:
        smf = False
    if not smf:
        skip_warn("DPM Storage Mgmt feature not enabled or not supported "
                  "on CPC {c}".format(c=cpc.name))


def skipif_storage_mgmt_feature(cpc):
    """
    Skip the test if the "DPM Storage Management" feature is enabled for
    the specified CPC.
    """
    try:
        smf = cpc.feature_enabled('dpm-storage-management')
    except ValueError:
        smf = False
    if smf:
        skip_warn("DPM Storage Mgmt feature enabled on CPC {c}".
                  format(c=cpc.name))


def skip_warn(msg):
    """
    Issue an End2endTestWarning and skip the current pytest testcase with the
    specified message.
    """
    warnings.warn(msg, End2endTestWarning, stacklevel=2)
    pytest.skip(msg)
