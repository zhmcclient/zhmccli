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
End2end tests for global options.
"""


import urllib3
import pytest

from ..function.utils import call_zhmc_child, assert_rc, assert_patterns

urllib3.disable_warnings()

URLLIB3_VERSION = [int(v) for v in urllib3.__version__.split('.')]

if URLLIB3_VERSION < [2, 0]:
    INVALID_HOST_MSG = "Failed to establish a new connection:"
else:
    INVALID_HOST_MSG = "Failed to resolve"


@pytest.mark.parametrize(
    "err_format, exp_stderr_patterns", [
        (None,  # default format: msg
         [r"Error: ConnectionError: .*" + INVALID_HOST_MSG + r".*"]),
        ('msg',
         [r"Error: ConnectionError: .*" + INVALID_HOST_MSG + r".*"]),
        ('def',
         [r"Error: classname='ConnectionError'; message=['\"].*"
          + INVALID_HOST_MSG + r".*['\"];"]),  # noqa: W503
    ]
)
@pytest.mark.parametrize(
    "err_opt", ['-e', '--error-format']
)
def test_option_errorformat(err_opt, err_format, exp_stderr_patterns):
    """
    Test global option (-e, --error-format).
    """

    if err_format is None:
        err_args = []
    else:
        err_args = [err_opt, err_format]

    # Invoke the command to be tested
    rc, stdout, stderr = call_zhmc_child(
        err_args + ['info'],
        {'ZHMC_HOST': 'invalid_host', 'ZHMC_USERID': 'user'}
    )

    assert_rc(1, rc, stdout, stderr)
    assert stdout == ""
    assert_patterns(exp_stderr_patterns, stderr.splitlines(), 'stderr')
