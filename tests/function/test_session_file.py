# Copyright 2024 IBM Corp. All Rights Reserved.
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
Function tests for _session_file.py module.
"""

import os
import re
from datetime import datetime, timezone
import tempfile
import pytest
from zhmcclient_mock import FakedSession

from zhmccli._session_file import HMCSession, HMCSessionFile, \
    HMCSessionException, HMCSessionNotFound, HMCSessionAlreadyExists, \
    HMCSessionFileNotFound, HMCSessionFileError, HMCSessionFileFormatError, \
    BLANKED_OUT_STRING, TIME_FORMAT, now_str


def create_session_file(sf_str):
    """
    Create an HMC session file with the specified content.

    The content string does not need to be valid according to the HMC session
    file schema, in order to be able to provoke format errors.
    The HMC session file is closed upon return.

    If the 'sf_str' parameter is None, no session file is created, and the
    path name of a non-existing file is returned.

    Parameters:
      sf_str (str): Content. May be None.

    Returns:
      HMCSessionFile: HMC session file.
    """
    home_dir = os.path.expanduser('~')
    # pylint: disable=consider-using-with
    file = tempfile.NamedTemporaryFile(
        mode='w', encoding="utf-8", delete=False,
        suffix='yaml', prefix='.test_zhmc_sessions_', dir=home_dir)
    filepath = file.name
    if sf_str is None:
        file.close()
        os.remove(filepath)
    else:
        file.write(sf_str)
        file.close()
    return HMCSessionFile(filepath)


def delete_session_file(session_file):
    """
    Delete an HMC session file, if it exists.

    Parameters:
      session_file (HMCSessionFile): HMC session file.
    """
    filepath = session_file.filepath
    if os.path.exists(filepath):
        os.remove(filepath)


def session_file_content(session_file):
    """
    Return the content of an HMC session file, if it exists.

    If it does not exist, return None.

    Parameters:
      session_file (HMCSessionFile): HMC session file.

    Returns:
      str: Content of HMC session file, or None.
    """
    filepath = session_file.filepath
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as fp:
            sf_str = fp.read()
        return sf_str
    return None


def assert_session_equal(act_session, exp_session, session_name):
    """
    Assert that two HMCSession objects are equal.
    """
    assert isinstance(act_session, HMCSession)
    assert isinstance(exp_session, HMCSession)
    for attr in ("host", "userid", "session_id", "ca_verify", "ca_cert_path",):
        act_value = getattr(act_session, attr)
        exp_value = getattr(exp_session, attr)
        assert act_value == exp_value, (
            f"Unexpected value of HMCSession {session_name!r} attribute "
            f"{attr!r}:\n"
            f"  Actual value: {act_value!r}\n"
            f"  Expected value: {exp_value!r}")
    assert_time_str(act_session.creation_time, exp_session.creation_time, 5)


def assert_session_file_content(session_file, exp_sf_str):
    """
    Assert that the HMC session file has the expected content.

    Because loading an HMC session file changes a non-existing file to exist
    with content '{}', this needs to be considered (they are considered
    equal).
    """
    act_sf_str = session_file_content(session_file)
    if exp_sf_str is None and act_sf_str == "{}":
        return
    assert act_sf_str == exp_sf_str, (
        f"HMC session file {session_file.filepath!r} has unexpected content:\n"
        f"  Actual content:\n{act_sf_str}\n"
        f"  Expected content:\n{exp_sf_str}\n")


@pytest.mark.parametrize(
    "exc_type",
    [
        HMCSessionNotFound,
        HMCSessionAlreadyExists,
        HMCSessionFileNotFound,
        HMCSessionFileError,
        HMCSessionFileFormatError
    ]
)
def test_session_file_exception(exc_type):
    """
    Test session file exception.
    """
    message = "Message"

    # The code to be tested
    exc = exc_type(message)

    assert isinstance(exc, Exception)
    assert isinstance(exc, HMCSessionException)
    assert str(exc) == message
    assert exc.args[0] == message


def test_session_repr():
    """
    Test HMCSession.__repr__().
    """
    host = "my_host"
    userid = "my_userid"
    session_id = "my_session_id"
    ca_verify = False
    ca_cert_path = None

    session = HMCSession(
        host=host,
        userid=userid,
        session_id=session_id,
        ca_verify=ca_verify,
        ca_cert_path=ca_cert_path)

    # The code to be tested
    repr_str = repr(session)

    exp_repr_pattern = (
        re.escape(
            "HMCSession("
            f"host={host!r}, "
            f"userid={userid!r}, "
            f"session_id={BLANKED_OUT_STRING}, "
            f"ca_verify={ca_verify!r}, "
            f"ca_cert_path={ca_cert_path!r}, "
            f"creation_time=") + r"'(.*)'\)")

    m = re.match(exp_repr_pattern, repr_str)
    assert m is not None, (
        "Unexpected repr string:\n"
        f"Actual: {repr_str}\n"
        f"Expected pattern: {exp_repr_pattern}")

    # Verify creation_time value
    creation_time = m.group(1)
    assert_time_str(creation_time, datetime.utcnow(), 5)


def assert_time_str(time_str, exp_time, delta):
    """
    Assert for time_str:
    * that it has the required format.
    * That it is within a delta of the expected point in time.

    Parameters:
      time_str (str): The point in time to be checked.
      exp_time (datetime or str): The expected point in time.
      delta (int): The allowed time delta, in seconds
    """
    if isinstance(exp_time, str):
        exp_time = datetime.strptime(exp_time, TIME_FORMAT)
        exp_time.replace(tzinfo=timezone.utc)
    assert isinstance(exp_time, datetime)

    try:
        time_dt = datetime.strptime(time_str, TIME_FORMAT)
    except ValueError:
        raise AssertionError(
            f"Time string does not have the required format: {time_str!r}")
    time_dt.replace(tzinfo=timezone.utc)

    assert abs((exp_time - time_dt).total_seconds()) <= delta, (
        f"Unexpected time: {time_str} - expected was {exp_time} with a "
        f"delta of {delta} s")


def test_session_as_dict():
    """
    Test HMCSession.as_dict().
    """
    host = "my_host"
    userid = "my_userid"
    session_id = "my_session_id"
    ca_verify = False
    ca_cert_path = None

    session = HMCSession(
        host=host,
        userid=userid,
        session_id=session_id,
        ca_verify=ca_verify,
        ca_cert_path=ca_cert_path)

    # The code to be tested
    session_dict = session.as_dict()

    assert isinstance(session_dict, dict)
    assert len(session_dict) == 6
    assert session_dict['host'] == host
    assert session_dict['userid'] == userid
    assert session_dict['session_id'] == session_id
    assert session_dict['ca_verify'] == ca_verify
    assert session_dict['ca_cert_path'] == ca_cert_path
    assert_time_str(session_dict['creation_time'], datetime.utcnow(), 5)


TESTCASES_SESSION_FROM_ZHMCCLIENT = [

    # Each item is a testcase for testing HMCSession.from_zhmcclient_session(),
    # with the following items:
    #
    # * verify_cert (bool/str): Input parameter for zhmcclient session.
    # * exp_ca_verify (bool): Expected property from function result.
    # * exp_ca_cert_path (str): Expected property from function result.

    (
        False,
        False,
        None
    ),
    (
        True,
        True,
        None
    ),
    (
        'dir/file.pem',
        True,
        'dir/file.pem'
    ),
]


@pytest.mark.parametrize(
    "verify_cert, exp_ca_verify, exp_ca_cert_path",
    TESTCASES_SESSION_FROM_ZHMCCLIENT
)
def test_session_from_zhmcclient(verify_cert, exp_ca_verify, exp_ca_cert_path):
    """
    Test HMCSession.from_zhmcclient_session().
    """
    host = "my_host"
    userid = "my_userid"
    session_id = "my_session_id"

    faked_session = FakedSession(host, 'hmc1', '2.16', '4.10', userid=userid)
    faked_session._session_id = session_id  # pylint: disable=protected-access
    faked_session._verify_cert = verify_cert  # pylint: disable=protected-access

    # The code to be tested
    hmc_session = HMCSession.from_zhmcclient_session(faked_session)

    assert hmc_session.host == host
    assert hmc_session.userid == userid
    assert hmc_session.session_id == session_id
    assert hmc_session.ca_verify == exp_ca_verify
    assert hmc_session.ca_cert_path == exp_ca_cert_path
    assert_time_str(hmc_session.creation_time, datetime.utcnow(), 5)


TESTCASES_SESSION_FILE_REPR = [

    # Each item is a testcase for testing HMCSessionFile.__repr__(),
    # with the following items:
    #
    # * sf_str (str/None): Content for HMC session file, or None for an empty
    #   HMC session file.
    # * exp_repr_data (str): Expected data shown in repr string.

    (
        None,
        "{}"
    ),
    (
        """
default:
  host: my_host
  userid: my_userid
  session_id: my_session_id
  ca_verify: false
  ca_cert_path: null
  creation_time: "2025-05-06 07:14:58"
""",
        "{'default': {...}}"
    ),
]


@pytest.mark.parametrize(
    "sf_str, exp_repr_data",
    TESTCASES_SESSION_FILE_REPR
)
def test_session_file_repr(sf_str, exp_repr_data):
    """
    Test HMCSessionFile.__repr__().
    """
    session_file = create_session_file(sf_str)
    filepath = session_file.filepath

    try:

        # The code to be tested
        repr_str = repr(session_file)

        # pylint: disable=protected-access
        exp_repr_str = (
            "HMCSessionFile("
            f"filepath={filepath!r}, "
            f"data={exp_repr_data})")

        assert repr_str == exp_repr_str

    finally:
        delete_session_file(session_file)


TESTCASES_SESSION_FILE_LIST = [

    # Each item is a testcase for testing HMCSessionFile.list(), with the
    # following items:
    #
    # * desc (str): Testcase description.
    # * initial_content (str): Content of initial HMC session file that is
    #   created before calling the function to be tested. None means there is
    #   no initial HMC session file.
    # * exp_result (dict): Expected result from the function to be tested.
    #   Key(str): Session name, Value(dict): HMC session kwargs.
    # * exp_exc_type (exc): Expected exception class. None for no exception.
    # * exp_exc_msg (str): Expected pattern for exception message. None for
    #   no exception.

    (
        "no session file",
        None,
        {},
        None, None
    ),
    (
        "invalid YAML format",
        "{\n",
        None,
        HMCSessionFileFormatError,
        "Invalid YAML syntax in HMC session file"
    ),
    (
        "invalid schema",
        "42\n",
        None,
        HMCSessionFileFormatError,
        "Invalid data format in HMC session file"
    ),
    (
        "empty session file",
        "{}\n",
        {},
        None, None
    ),
    (
        "session file with one valid session",
        """
default:
  host: my_host
  userid: my_userid
  session_id: my_session_id
  ca_verify: false
  ca_cert_path: null
  creation_time: "2025-05-06 07:14:58"
        """,
        {
            'default': dict(
                host="my_host",
                userid="my_userid",
                session_id="my_session_id",
                ca_verify=False,
                ca_cert_path=None,
                creation_time="2025-05-06 07:14:58")
        },
        None, None
    ),
    (
        "session file with two valid sessions",
        """
default:
  host: my_host
  userid: my_userid
  session_id: my_session_id
  ca_verify: false
  ca_cert_path: null
  creation_time: "2025-05-06 07:14:58"
s2:
  host: my_host2
  userid: my_userid2
  session_id: my_session_id2
  ca_verify: false
  ca_cert_path: null
  creation_time: "2025-05-06 07:20:58"
        """,
        {
            'default': dict(
                host="my_host",
                userid="my_userid",
                session_id="my_session_id",
                ca_verify=False,
                ca_cert_path=None,
                creation_time="2025-05-06 07:14:58"),
            's2': dict(
                host="my_host2",
                userid="my_userid2",
                session_id="my_session_id2",
                ca_verify=False,
                ca_cert_path=None,
                creation_time="2025-05-06 07:20:58")
        },
        None, None
    ),
    (
        "session file with one valid session with missing properties",
        """
default:
  host: my_host
  userid: my_userid
  session_id: my_session_id
  ca_verify: false
        """,
        None,
        HMCSessionFileFormatError,
        "Invalid data format in HMC session file"
    ),
]


@pytest.mark.parametrize(
    "desc, initial_content, exp_result, exp_exc_type, exp_exc_msg",
    TESTCASES_SESSION_FILE_LIST
)
def test_session_file_list(
        desc, initial_content, exp_result, exp_exc_type, exp_exc_msg):
    # pylint: disable=unused-argument
    """
    Test HMCSessionFile.list().
    """
    session_file = create_session_file(initial_content)

    try:
        if exp_exc_type:
            with pytest.raises(exp_exc_type) as exc_info:

                # The code to be tested
                session_file.list()

            exc = exc_info.value
            msg = str(exc)
            m = re.match(exp_exc_msg, msg)
            assert m, \
                "Unexpected exception message:\n" \
                "  expected pattern: {!r}\n" \
                "  actual message: {!r}".format(exp_exc_msg, msg)
        else:

            # The code to be tested
            result = session_file.list()

            assert isinstance(result, dict)
            assert set(result.keys()) == set(exp_result.keys())
            for name, act_session in result.items():
                assert name in exp_result
                exp_session = HMCSession(**exp_result[name])
                assert_session_equal(act_session, exp_session, name)

        assert_session_file_content(session_file, initial_content)

    finally:
        delete_session_file(session_file)


TESTCASES_SESSION_FILE_GET = [

    # Each item is a testcase for testing HMCSessionFile.get(), with the
    # following items:
    #
    # * desc (str): Testcase description.
    # * initial_content (str): Content of initial HMC session file that is
    #   created before calling the function to be tested. None means there is
    #   no initial HMC session file.
    # * session_name (str): Session name to be retrieved.
    # * exp_session_kwargs (dict): Expected HMC session, or None for exception.
    # * exp_exc_type (exc): Expected exception class. None for no exception.
    # * exp_exc_msg (str): Expected pattern for exception message. None for
    #   no exception.

    (
        "no session file",
        None,
        "foo",
        None,
        HMCSessionNotFound,
        "Session not found in HMC session file"
    ),
    (
        "invalid YAML format",
        "{\n",
        "foo",
        None,
        HMCSessionFileFormatError,
        "Invalid YAML syntax in HMC session file"
    ),
    (
        "invalid schema",
        "42\n",
        "foo",
        None,
        HMCSessionFileFormatError,
        "Invalid data format in HMC session file"
    ),
    (
        "empty session file",
        "{}\n",
        "foo",
        None,
        HMCSessionNotFound,
        "Session not found in HMC session file"
    ),
    (
        "session file with two valid sessions, one of those requested",
        """
default:
  host: my_host
  userid: my_userid
  session_id: my_session_id
  ca_verify: false
  ca_cert_path: null
  creation_time: "2025-05-06 07:18:58"
s2:
  host: my_host2
  userid: my_userid2
  session_id: my_session_id2
  ca_verify: false
  ca_cert_path: null
  creation_time: "2025-05-06 07:20:58"
        """,
        "s2",
        dict(
            host="my_host2",
            userid="my_userid2",
            session_id="my_session_id2",
            ca_verify=False,
            ca_cert_path=None,
            creation_time="2025-05-06 07:20:58",
        ),
        None, None
    ),
    (
        "session file with two valid sessions, none of those requested",
        """
default:
  host: my_host
  userid: my_userid
  session_id: my_session_id
  ca_verify: false
  ca_cert_path: null
  creation_time: "2025-05-06 07:18:58"
s2:
  host: my_host2
  userid: my_userid2
  session_id: my_session_id2
  ca_verify: false
  ca_cert_path: null
  creation_time: "2025-05-06 07:20:58"
        """,
        "foo",
        None,
        HMCSessionNotFound,
        "Session not found in HMC session file"
    ),
]


@pytest.mark.parametrize(
    "desc, initial_content, session_name, exp_session_kwargs, exp_exc_type, "
    "exp_exc_msg",
    TESTCASES_SESSION_FILE_GET
)
def test_session_file_get(
        desc, initial_content, session_name, exp_session_kwargs, exp_exc_type,
        exp_exc_msg):
    # pylint: disable=unused-argument
    """
    Test HMCSessionFile.get().
    """
    session_file = create_session_file(initial_content)

    try:
        if exp_exc_type:
            with pytest.raises(exp_exc_type) as exc_info:

                # The code to be tested
                session_file.get(session_name)

            exc = exc_info.value
            msg = str(exc)
            m = re.match(exp_exc_msg, msg)
            assert m, \
                "Unexpected exception message:\n" \
                "  expected pattern: {!r}\n" \
                "  actual message: {!r}".format(exp_exc_msg, msg)
        else:

            # The code to be tested
            session = session_file.get(session_name)
            exp_session = HMCSession(**exp_session_kwargs)

            assert isinstance(session, HMCSession)
            assert_session_equal(session, exp_session, session_name)

        assert_session_file_content(session_file, initial_content)

    finally:
        delete_session_file(session_file)


TESTCASES_SESSION_FILE_ADD = [

    # Each item is a testcase for testing HMCSessionFile.add(), with the
    # following items:
    #
    # * desc (str): Testcase description.
    # * initial_content (str): Content of initial HMC session file that is
    #   created before calling the function to be tested. None means there is
    #   no initial HMC session file.
    # * session_name (str): Session name to be added.
    # * session_kwargs (dict): Input args for session to be added.
    # * exp_exc_type (exc): Expected exception class. None for no exception.
    # * exp_exc_msg (str): Expected pattern for exception message. None for
    #   no exception.

    (
        "no session file",
        None,
        "foo",
        dict(
            host="my_host",
            userid="my_userid",
            session_id="my_session_id",
            ca_verify=False,
            ca_cert_path=None,
        ),
        None, None
    ),
    (
        "empty session file",
        "{}\n",
        "foo",
        dict(
            host="my_host",
            userid="my_userid",
            session_id="my_session_id",
            ca_verify=False,
            ca_cert_path=None,
        ),
        None, None
    ),
    (
        "session file with one valid session, new session does not exist",
        """
default:
  host: my_host_def
  userid: my_userid_def
  session_id: my_session_id_def
  ca_verify: false
  ca_cert_path: null
  creation_time: "2025-05-06 07:18:58"
        """,
        "foo",
        dict(
            host="my_host",
            userid="my_userid",
            session_id="my_session_id",
            ca_verify=False,
            ca_cert_path=None,
        ),
        None, None
    ),
    (
        "session file with one valid session, new session exists",
        """
foo:
  host: my_host_def
  userid: my_userid_def
  session_id: my_session_id_def
  ca_verify: false
  ca_cert_path: null
  creation_time: "2025-05-06 07:20:58"
        """,
        "foo",
        dict(
            host="my_host",
            userid="my_userid",
            session_id="my_session_id",
            ca_verify=False,
            ca_cert_path=None,
        ),
        HMCSessionAlreadyExists,
        "Session already exists in HMC session file"
    ),
]


@pytest.mark.parametrize(
    "desc, initial_content, session_name, session_kwargs, exp_exc_type, "
    "exp_exc_msg",
    TESTCASES_SESSION_FILE_ADD
)
def test_session_file_add(
        desc, initial_content, session_name, session_kwargs, exp_exc_type,
        exp_exc_msg):
    # pylint: disable=unused-argument
    """
    Test HMCSessionFile.add().
    """
    session_file = create_session_file(initial_content)
    session = HMCSession(**session_kwargs)

    try:
        if exp_exc_type:
            with pytest.raises(exp_exc_type) as exc_info:

                # The code to be tested
                session_file.add(session_name, session)

            exc = exc_info.value
            msg = str(exc)
            m = re.match(exp_exc_msg, msg)
            assert m, \
                "Unexpected exception message:\n" \
                "  expected pattern: {!r}\n" \
                "  actual message: {!r}".format(exp_exc_msg, msg)

            assert_session_file_content(session_file, initial_content)

        else:

            # The code to be tested
            session_file.add(session_name, session)

            retrieved_session = session_file.get(session_name)

            assert_session_equal(session, retrieved_session, session_name)

    finally:
        delete_session_file(session_file)


TESTCASES_SESSION_FILE_REMOVE = [

    # Each item is a testcase for testing HMCSessionFile.remove(), with the
    # following items:
    #
    # * desc (str): Testcase description.
    # * initial_content (str): Content of initial HMC session file that is
    #   created before calling the function to be tested. None means there is
    #   no initial HMC session file.
    # * session_name (str): Session name to be removed.
    # * exp_exc_type (exc): Expected exception class. None for no exception.
    # * exp_exc_msg (str): Expected pattern for exception message. None for
    #   no exception.

    (
        "no session file",
        None,
        "foo",
        HMCSessionNotFound,
        "Session not found in HMC session file"
    ),
    (
        "empty session file",
        "{}\n",
        "foo",
        HMCSessionNotFound,
        "Session not found in HMC session file"
    ),
    (
        "session file with one valid session that is session to be removed",
        """
foo:
  host: my_host_def
  userid: my_userid_def
  session_id: my_session_id_def
  ca_verify: false
  ca_cert_path: null
  creation_time: "2025-05-06 07:20:58"
        """,
        "foo",
        None, None
    ),
    (
        "session file with one valid session that is not session to be removed",
        """
default:
  host: my_host_def
  userid: my_userid_def
  session_id: my_session_id_def
  ca_verify: false
  ca_cert_path: null
  creation_time: "2025-05-06 07:20:58"
        """,
        "foo",
        HMCSessionNotFound,
        "Session not found in HMC session file"
    ),
]


@pytest.mark.parametrize(
    "desc, initial_content, session_name, exp_exc_type, exp_exc_msg",
    TESTCASES_SESSION_FILE_REMOVE
)
def test_session_file_remove(
        desc, initial_content, session_name, exp_exc_type, exp_exc_msg):
    # pylint: disable=unused-argument
    """
    Test HMCSessionFile.remove().
    """
    session_file = create_session_file(initial_content)

    try:
        if exp_exc_type:
            with pytest.raises(exp_exc_type) as exc_info:

                # The code to be tested
                session_file.remove(session_name)

            exc = exc_info.value
            msg = str(exc)
            m = re.match(exp_exc_msg, msg)
            assert m, \
                "Unexpected exception message:\n" \
                "  expected pattern: {!r}\n" \
                "  actual message: {!r}".format(exp_exc_msg, msg)

            assert_session_file_content(session_file, initial_content)

        else:

            # The code to be tested
            session_file.remove(session_name)

            with pytest.raises(HMCSessionNotFound):
                session_file.get(session_name)

    finally:
        delete_session_file(session_file)


TESTCASES_SESSION_FILE_UPDATE = [

    # Each item is a testcase for testing HMCSessionFile.update(), with the
    # following items:
    #
    # * desc (str): Testcase description.
    # * initial_content (str): Content of initial HMC session file that is
    #   created before calling the function to be tested. None means there is
    #   no initial HMC session file.
    # * session_name (str): Session name to be removed.
    # * updates (dict): Dict with updates to the session.
    # * exp_exc_type (exc): Expected exception class. None for no exception.
    # * exp_exc_msg (str): Expected pattern for exception message. None for
    #   no exception.

    (
        "no session file",
        None,
        "foo",
        {},
        HMCSessionNotFound,
        "Session not found in HMC session file"
    ),
    (
        "empty session file",
        "{}\n",
        "foo",
        {},
        HMCSessionNotFound,
        "Session not found in HMC session file"
    ),
    (
        "update nothing",
        """
foo:
  host: my_host
  userid: my_userid
  session_id: my_session_id
  ca_verify: false
  ca_cert_path: null
  creation_time: "2025-05-06 07:20:58"
        """,
        "foo",
        {},  # creation_time gets updated automatically
        None, None
    ),
    (
        "update everything",
        """
foo:
  host: my_host
  userid: my_userid
  session_id: my_session_id
  ca_verify: false
  ca_cert_path: null
  creation_time: "2025-05-06 07:20:58"
        """,
        "foo",
        {
            "host": "my_host_2",
            "userid": "my_userid_2",
            "session_id": "my_session_id_2",
            "ca_verify": True,
            "ca_cert_path": "foo",
            # creation_time gets updated automatically
        },
        None, None
    ),
]


@pytest.mark.parametrize(
    "desc, initial_content, session_name, updates, exp_exc_type, exp_exc_msg",
    TESTCASES_SESSION_FILE_UPDATE
)
def test_session_file_update(
        desc, initial_content, session_name, updates, exp_exc_type,
        exp_exc_msg):
    # pylint: disable=unused-argument
    """
    Test HMCSessionFile.update().
    """
    session_file = create_session_file(initial_content)

    try:
        if exp_exc_type:
            with pytest.raises(exp_exc_type) as exc_info:

                # The code to be tested
                session_file.update(session_name, updates)

            exc = exc_info.value
            msg = str(exc)
            m = re.match(exp_exc_msg, msg)
            assert m, \
                "Unexpected exception message:\n" \
                "  expected pattern: {!r}\n" \
                "  actual message: {!r}".format(exp_exc_msg, msg)

            assert_session_file_content(session_file, initial_content)

        else:

            original_session = session_file.get(session_name)

            # The code to be tested
            session_file.update(session_name, updates)

            updated_session = session_file.get(session_name)
            exp_session = original_session
            exp_session.creation_time = now_str()

            def _update_exp_session(attr):
                if attr in updates:
                    setattr(exp_session, attr, updates[attr])

            _update_exp_session('host')
            _update_exp_session('userid')
            _update_exp_session('session_id')
            _update_exp_session('ca_verify')
            _update_exp_session('ca_cert_path')
            _update_exp_session('creation_time')
            assert_session_equal(updated_session, exp_session, session_name)

    finally:
        delete_session_file(session_file)
