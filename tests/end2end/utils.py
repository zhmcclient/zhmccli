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
import tempfile
import pytest
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import
from zhmcclient.testutils import setup_hmc_session, teardown_hmc_session

from zhmccli._session_file import HMCSessionFile, HMCSession, \
    DEFAULT_SESSION_NAME


# Prefix used for names of resources that are created during tests
TEST_PREFIX = 'zhmcclient_tests_end2end'


def setup_session_file(hd):
    """
    Setup an HMC session file with a logged-on session to the HMC in the
    HMC definition.

    Parameters:
      hd (:class:`~zhmcclient.testutils.HMCDefinition`): The HMC definition of
        the HMC the test runs against.

    Returns:
      tuple(session, filepath): With:
      * session (zhmcclient.Session): Logged-on session.
      * filepath (str): Path name of HMC session file.
    """
    # Create an empty temporary file for use as the HMC session file
    home_dir = os.path.expanduser('~')
    # pylint: disable=consider-using-with
    file = tempfile.NamedTemporaryFile(
        mode='w', encoding="utf-8", delete=False,
        suffix='.yaml', prefix='.test_zhmc_', dir=home_dir)
    filepath = file.name
    file.write("{}")
    file.close()

    session_file = HMCSessionFile(filepath)

    # Make the zhmc commands use this session file
    os.environ['_ZHMC_TEST_SESSION_FILEPATH'] = filepath

    session = setup_hmc_session(hd)
    hmc_session = HMCSession.from_zhmcclient_session(session)
    session_file.add(DEFAULT_SESSION_NAME, hmc_session)

    return session, filepath


def teardown_session_file(session, filepath):
    """
    Tear down an HMC session file and its HMC session.

    Parameters:
      session (:class:`~zhmcclient.Session`): Logged-on session.
      filepath (str): Path name of HMC session file.
    """
    del os.environ['_ZHMC_TEST_SESSION_FILEPATH']
    teardown_hmc_session(session)
    os.remove(filepath)


@pytest.fixture(scope='module')
def zhmc_session(request, hmc_definition):  # noqa: F811
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Pytest fixture that provides a logged-on zhmc session for an end2end test
    function.

    This function logs on to the HMC and creates an HMC session file with the
    logged on session.

    Using this fixture as an argument in a test function resolves to that
    session.

    Returns:
        zhmcclient.Session: Logged-on session.
    """
    session, filepath = setup_session_file(hmc_definition)

    yield session

    teardown_session_file(session, filepath)


def run_zhmc(args, pdb=False, log=False):
    """
    Run the zhmc command and return its exit code, stdout and stderr.

    Parameters:

      args (list/tuple of str): List of command line arguments, not including
        the 'zhmc' command name itself.

      pdb (bool): If True, debug the zhmc command. This is done by inserting
        the '--pdb' option to the command arguments, and by not capturing
        stdout/stderr.

      log (bool): If True and pdb is False, enable HMC logging for the zhmc
        command. This is done by inserting the '--log hmc=debug' option to the
        command arguments.

    Returns:
      tuple (rc, stdout, stderr) as follows:
      - rc (int): zhmc exit code
      - stdout (str): stdout string, or None if debugging the zhmc command
      - stderr (str): stderr string, or None if debugging the zhmc command
    """
    assert isinstance(args, (list, tuple))

    p_args = ['zhmc'] + args

    # Set up output capturing, dependent on pdb flag
    p_kwargs = {}
    if pdb:
        p_args.insert(1, '--pdb')
    else:
        p_kwargs['stdout'] = subprocess.PIPE
        p_kwargs['stderr'] = subprocess.PIPE
        if log:
            p_args.insert(1, 'all=debug')
            p_args.insert(1, '--log')

    # pylint: disable=consider-using-with
    proc = subprocess.Popen(p_args, **p_kwargs)

    stdout, stderr = proc.communicate()
    rc = proc.returncode
    if not pdb:
        stdout = stdout.decode()
        stderr = stderr.decode()

    return rc, stdout, stderr


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
