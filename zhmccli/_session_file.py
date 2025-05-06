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
Support for an HMC session file in YAML format.

An HMC session file stores session-related data about logged-in HMC sessions.
"""

import os
import stat
from copy import deepcopy
from datetime import datetime
import yaml
import jsonschema

__all__ = ['HMCSessionFile', 'HMCSessionException',
           'HMCSessionNotFound', 'HMCSessionAlreadyExists',
           'HMCSessionFileNotFound', 'HMCSessionFileError',
           'HMCSessionFileFormatError', 'DEFAULT_SESSION_NAME']

# datetime format for creation time in HMC session file
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

BLANKED_OUT_STRING = '********'

DEFAULT_SESSION_NAME = 'default'

HMC_SESSION_FILE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "JSON schema for an HMC session file in YAML format",
    "description": "List of logged-in HMC sessions",
    "type": "object",
    "additionalProperties": False,
    "patternProperties": {
        "^[a-z0-9_]+$": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "host",
                "userid",
                "session_id",
                "ca_verify",
                "ca_cert_path",
                "creation_time",
            ],
            "properties": {
                # Top-level group name:
                "host": {
                    "description": "HMC host, as hostname or IP address",
                    "type": "string",
                },
                "userid": {
                    "description": "HMC userid",
                    "type": "string",
                },
                "session_id": {
                    "description": "HMC session ID",
                    "type": "string",
                },
                "ca_verify": {
                    "description": "CA certificate validation is performed",
                    "type": "boolean",
                },
                "ca_cert_path": {
                    "description": "Path name of CA certificate file or "
                    "directory",
                    "type": ["string", "null"],
                },
                "creation_time": {
                    "description": "Creation time of the HMC session, in "
                    "'YYYY-MM-DD hh:mm:ss' format in the UTC timezone",
                    "type": "string",
                },
            },
        },
    },
}


class HMCSessionException(Exception):
    """
    Base class for errors with the HMC session file.
    """
    pass


class HMCSessionNotFound(HMCSessionException):
    """
    The HMC session with the specified name was not found in the HMC session
    file.
    """
    pass


class HMCSessionAlreadyExists(HMCSessionException):
    """
    The HMC session with the specified name already exists in the HMC session
    file.
    """
    pass


class HMCSessionFileNotFound(HMCSessionException):
    """
    The HMC session file was not found.
    """
    pass


class HMCSessionFileError(HMCSessionException):
    """
    Error reading or writing the HMC session file.
    """
    pass


class HMCSessionFileFormatError(HMCSessionException):
    """
    Error in the format of the content of the HMC session file.
    """
    pass


def now_str():
    """
    Return the current time as a string in 'YYYY-MM-DD hh:mm:ss' format
    in the UTC timezone, suitable for use in the HMC session file."
    """
    return datetime.utcnow().strftime(TIME_FORMAT)


class HMCSession:
    """
    Representation of an HMC session in the HMC session file.
    """

    def __init__(self, host, userid, session_id, ca_verify, ca_cert_path,
                 creation_time=None):
        """
        Parameters:
          host (str): HMC host, as hostname or IP address.
          userid (str): HMC userid.
          session_id (str): HMC session ID.
          ca_verify (bool): CA certificate validation is performed.
          ca_cert_path (str): Path name of CA certificate file or directory,
            or None if the default CA chain is used.
          creation_time (str): Creation time of the HMC session, in
            'YYYY-MM-DD hh:mm:ss' format in the UTC timezone. If `None`, it
            defaults to the current time.
        """
        self.host = host
        self.userid = userid
        self.session_id = session_id
        self.ca_verify = ca_verify
        self.ca_cert_path = ca_cert_path
        if creation_time is None:
            creation_time = now_str()
        self.creation_time = creation_time

    def __repr__(self):
        return (
            "HMCSession("
            f"host={self.host!r}, "
            f"userid={self.userid!r}, "
            f"session_id={BLANKED_OUT_STRING}, "
            f"ca_verify={self.ca_verify!r}, "
            f"ca_cert_path={self.ca_cert_path!r}, "
            f"creation_time={self.creation_time!r})")

    @staticmethod
    def from_zhmcclient_session(zhmcclient_session):
        """
        Return new HMCSession object from a zhmcclient Session.

        Parameters:
          zhmcclient_session (zhmcclient.Session): The zhmcclient session.

        Returns:
          HMCSession: new HMCSession object.
        """
        if zhmcclient_session.verify_cert is False:
            ca_verify = False
            ca_cert_path = None
        elif zhmcclient_session.verify_cert is True:
            ca_verify = True
            ca_cert_path = None
        else:
            ca_verify = True
            ca_cert_path = zhmcclient_session.verify_cert
        return HMCSession(
            zhmcclient_session.host,
            zhmcclient_session.userid,
            zhmcclient_session.session_id,
            ca_verify,
            ca_cert_path)

    def as_dict(self):
        """
        Return the HMC session properties as a dict.
        """
        return {
            "host": self.host,
            "userid": self.userid,
            "session_id": self.session_id,
            "ca_verify": self.ca_verify,
            "ca_cert_path": self.ca_cert_path,
            "creation_time": self.creation_time,
        }


def session_file_opener(path, flags):
    """
    Python opener function for the HMC session file.
    """
    return os.open(path, flags, mode=stat.S_IRUSR | stat.S_IWUSR)


class DictDot(dict):
    """Dict with dot representation."""

    def __repr__(self):
        return '{...}'


# The HMC session file that is normally used.
# Some unit/function tests specify another path name by passing the 'filepath'
# parameter to HMCSessionFile().
# Some end2end tests specify another path name by setting the
# _ZHMC_TEST_SESSION_FILEPATH env. var.
SESSION_FILEPATH = '~/.zhmc_sessions.yml'


class HMCSessionFile:
    """
    Access to an HMC session file.
    """

    def __init__(self, filepath=None):
        """
        Parameters:

          filepath (str): Path name of the HMC session file. If None, the
            path name in the env var _ZHMC_TEST_SESSION_FILEPATH is used. If
            not set, the path in SESSION_FILEPATH is used.
        """
        if filepath is None:
            filepath = os.environ.get('_ZHMC_TEST_SESSION_FILEPATH', None)
            if filepath is None:
                filepath = SESSION_FILEPATH
        self._filepath = os.path.expanduser(filepath)
        self._data = None  # File content, deferred loading

    def __repr__(self):
        if self._data is None:
            self._data = self._load()
        session_dict = {}
        for session_name in self._data.keys():
            session_dict[session_name] = DictDot()
        return (
            "HMCSessionFile("
            f"filepath={self.filepath!r}, "
            f"data={session_dict!r})")

    @property
    def filepath(self):
        """
        string: Path name of the HMC session file.
        """
        return self._filepath

    def list(self):
        """
        List all HMC sessions in the HMC session file.

        Returns:
          dict of session name, HMCSession

        Raises:
          HMCSessionFileError: HMC session file could not be created.
          HMCSessionFileFormatError: Invalid YAML syntax in HMC session file.
          HMCSessionFileFormatError: Invalid data format in HMC session file.
        """
        if self._data is None:
            self._data = self._load()
        sessions = {}
        for session_name, session_item in self._data.items():
            sessions[session_name] = HMCSession(**session_item)
        return sessions

    def get(self, name=DEFAULT_SESSION_NAME):
        """
        Get the HMC session with the specified name from the HMC session file.

        Parameters:
          name (str): Name of the HMC session.

        Returns:
          HMCSession: HMC session.

        Raises:
          HMCSessionNotFound: Session not found in HMC session file.
          HMCSessionFileError: HMC session file could not be created.
          HMCSessionFileFormatError: Invalid YAML syntax in HMC session file.
          HMCSessionFileFormatError: Invalid data format in HMC session file.
        """
        if self._data is None:
            self._data = self._load()
        try:
            session_item = self._data[name]
        except KeyError:
            raise HMCSessionNotFound(
                f"Session not found in HMC session file: {name}")
        return HMCSession(**session_item)

    def add(self, name, session):
        """
        Add the specified HMC session with the specified name to the HMC
        session file, and update the file.

        Parameters:
          name (str): Name of the HMC session.
          session (HMCSession): The HMC session to be added. The `creation_time`
            property is ignored if present, and is set to the current time in
            the HMC session file.

        Raises:
          HMCSessionAlreadyExists: HMC session already exists in session file.
          HMCSessionFileError: HMC session file could not be created.
          HMCSessionFileFormatError: Invalid YAML syntax in HMC session file.
          HMCSessionFileFormatError: Invalid data format in HMC session file.
        """
        if self._data is None:
            self._data = self._load()
        if name in self._data:
            raise HMCSessionAlreadyExists(
                f"Session already exists in HMC session file: {name}")
        self._data[name] = session.as_dict()
        self._data[name].update({'creation_time': now_str()})
        self._save(self._data)

    def remove(self, name):
        """
        Remove the specified HMC session from the HMC session file, and update
        the file.

        Parameters:
          name (str): Name of the HMC session.

        Raises:
          HMCSessionNotFound: Session not found in HMC session file.
          HMCSessionFileError: HMC session file could not be created.
          HMCSessionFileFormatError: Invalid YAML syntax in HMC session file.
          HMCSessionFileFormatError: Invalid data format in HMC session file.
        """
        if self._data is None:
            self._data = self._load()
        try:
            del self._data[name]
        except KeyError:
            raise HMCSessionNotFound(
                f"Session not found in HMC session file: {name}")
        self._save(self._data)

    def update(self, name, updates):
        """
        Update the specified HMC session with the provided keyword arguments,
        and update the file.

        Parameters:
          name (str): Name of the HMC session.
          updates (dict): Properties of the HMC session to be updated.
            The `creation_time` property is ignored if present, and is set to
            the current time in the HMC session file.

        Raises:
          HMCSessionNotFound: Session not found in HMC session file.
          HMCSessionFileError: HMC session file could not be created.
          HMCSessionFileFormatError: Invalid YAML syntax in HMC session file.
          HMCSessionFileFormatError: Invalid data format in HMC session file.
        """
        if self._data is None:
            self._data = self._load()
        data = deepcopy(self._data)
        try:
            session_data = data[name]
        except KeyError:
            raise HMCSessionNotFound(
                f"Session not found in HMC session file: {name}")
        session_data.update(updates)
        session_data.update({'creation_time': now_str()})
        self._save(data)
        self._data = data

    def _create(self):
        """
        Create an empty HMC session file and return its empty data.

        Raises:
          HMCSessionFileError: HMC session file could not be created.
        """
        try:
            with open(self._filepath, 'w', encoding="utf-8",
                      opener=session_file_opener) as fp:
                fp.write("{}")
            os.chmod(self._filepath, stat.S_IRUSR | stat.S_IWUSR)
        except OSError as exc:
            raise HMCSessionFileError(
                f"The HMC session file {self._filepath!r} could not be "
                f"created: {exc}")
        return {}

    def _load(self):
        """
        Load the HMC session file, validate it and return its data.

        Raises:
          HMCSessionFileError: HMC session file could not be created.
          HMCSessionFileFormatError: Invalid YAML syntax in HMC session file.
          HMCSessionFileFormatError: Invalid data format in HMC session file.
        """
        try:
            # pylint: disable=unspecified-encoding
            with open(self._filepath) as fp:
                try:
                    data = yaml.load(fp, Loader=yaml.SafeLoader)
                except (yaml.parser.ParserError,
                        yaml.scanner.ScannerError) as exc:
                    raise HMCSessionFileFormatError(
                        "Invalid YAML syntax in HMC session file "
                        f"{self._filepath!r}: {exc.__class__.__name__} {exc}")
        except OSError:
            data = self._create()
        self._validate(data)
        return data

    def _save(self, data):
        """
        Validate and save the data to the HMC session file.

        Raises:
          HMCSessionFileError: HMC session file could not be written.
        """
        self._validate(data)
        try:
            with open(self._filepath, 'w', encoding="utf-8",
                      opener=session_file_opener) as fp:
                yaml.dump(data, fp, indent=4, default_flow_style=False)
            os.chmod(self._filepath, stat.S_IRUSR | stat.S_IWUSR)
        except OSError as exc:
            raise HMCSessionFileError(
                f"The HMC session file {self._filepath!r} could not be "
                f"written: {exc}")

    def _validate(self, data):
        """
        Validate that the data conforms to the schema for the HMC session file.

        Raises:
          HMCSessionFileFormatError: Invalid data format in HMC session file.
        """
        try:
            jsonschema.validate(data, HMC_SESSION_FILE_SCHEMA)
        except jsonschema.exceptions.ValidationError as exc:
            elem = '.'.join(str(e) for e in exc.absolute_path)
            schemaitem = '.'.join(str(e) for e in exc.absolute_schema_path)
            raise HMCSessionFileFormatError(
                "Invalid data format in HMC session file "
                f"{self._filepath}: {exc.message}; "
                f"Offending element: {elem}; "
                f"Schema item: {schemaitem}; "
                f"Validator: {exc.validator}={exc.validator_value}")
