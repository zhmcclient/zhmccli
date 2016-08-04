# Copyright 2016 IBM Corp. All Rights Reserved.
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
Session class: A session to the HMC, optionally in context of an HMC user.
"""

from __future__ import absolute_import

import json
import time
import requests

from ._exceptions import HTTPError, AuthError, ConnectionError
from ._timestats import TimeStatsKeeper

__all__ = ['Session']

_HMC_PORT = 6794
_HMC_SCHEME = "https"
_STD_HEADERS = {
    'Content-type': 'application/json',
    'Accept': '*/*'
}


class Session(object):
    """
    A session to the HMC, optionally in context of an HMC user.

    The session supports operations that require to be authenticated, as well
    as operations that don't (e.g. obtaining the API version).

    The session can keep statistics about the elapsed time for issuing HTTP
    requests against the HMC API. Instance variable
    :attr:`~zhmcclient.Session.time_stats_keeper` is used to enable/disable the
    measurements, and to print the statistics.
    """

    def __init__(self, host, userid=None, password=None):
        """
        Creating a session object will not immediately cause a logon to be
        attempted; the logon is deferred until needed.

        Parameters:

          host (:term:`string`):
            HMC host. For valid formats, see the
            :attr:`~zhmcclient.Session.host` property.
            Must not be `None`.

          userid (:term:`string`):
            Userid of the HMC user to be used.
            If `None`, only operations that do not require authentication, can
            be performed.

          password (:term:`string`):
            Password of the HMC user to be used.

        TODO: Add support for client-certificate-based authentication.
        """
        self._host = host
        self._userid = userid
        self._password = password
        self._base_url = "{scheme}://{host}:{port}".format(
            scheme=_HMC_SCHEME,
            host=self._host,
            port=_HMC_PORT)
        self._headers = _STD_HEADERS  # dict with standard HTTP headers
        self._session_id = None  # HMC session ID
        self._session = None  # requests.Session() object
        self._time_stats_keeper = TimeStatsKeeper()

    @property
    def host(self):
        """
        :term:`string`: HMC host, in one of the following formats:

          * a short or fully qualified DNS hostname
          * a literal (= dotted) IPv4 address
          * a literal IPv6 address, formatted as defined in :term:`RFC3986`
            with the extensions for zone identifiers as defined in
            :term:`RFC6874`, supporting ``-`` (minus) for the delimiter
            before the zone ID string, as an additional choice to ``%25``
        """
        return self._host

    @property
    def userid(self):
        """
        :term:`string`: Userid of the HMC user to be used.

        If `None`, only operations that do not require authentication, can be
        performed.
        """
        return self._userid

    @property
    def base_url(self):
        """
        :term:`string`: Base URL of the HMC in this session.

        Example:

        ::

            https://myhmc.acme.com:6794
        """
        return self._base_url

    @property
    def headers(self):
        """
        :term:`header dict`: HTTP headers to be used in each request.

        Initially, this is the following set of headers:

        ::

            Content-type: application/json
            Accept: */*

        When the session is logged on to the HMC, the session token is added
        to these headers:

        ::

            X-API-Session: ...
        """
        return self._headers

    @property
    def time_stats_keeper(self):
        """
        The time statistics keeper (for a usage example, see section
        :ref:`Time Statistics`).
        """
        return self._time_stats_keeper

    def session_id(self):
        """
        :term:`string`: Session ID for this session, returned by the HMC.
        """
        return self._session_id

    @property
    def session(self):
        """
        :term:`string`: :class:`requests.Session` object for this session.
        """
        return self._session

    def logon(self):
        """
        Make sure the session is logged on to the HMC.

        After successful logon to the HMC, the following is stored in this
        session object for reuse in subsequent operations:

        * the HMC session ID, in order to avoid extra userid authentications,
        * a :class:`requests.Session` object, in order to enable connection
          pooling. Connection pooling avoids repetitive SSL/TLS handshakes.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        if not self.is_logon():
            self._do_logon()

    def logoff(self):
        """
        Make sure the session is logged off from the HMC.

        After successful logoff, the HMC session ID and
        :class:`requests.Session` object stored in this object are reset.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        if self.is_logon():
            self._do_logoff()

    def is_logon(self):
        """
        Return a boolean indicating whether the session is currently logged on
        to the HMC.
        """
        return self._session_id is not None

    def _do_logon(self):
        """
        Log on, unconditionally. This can be used to re-logon.
        This requires credentials to be provided.
        """
        if self._userid is None or self._password is None:
            raise AuthError("Userid or password not provided.")
        logon_uri = '/api/sessions'
        logon_body = {
            'userid': self._userid,
            'password': self._password
        }
        self._headers.pop('X-API-Session', None)  # Just in case
        self._session = requests.Session()
        logon_res = self.post(logon_uri, logon_body, logon_required=False)
        self._session_id = logon_res['api-session']
        self._headers['X-API-Session'] = self._session_id

    def _do_logoff(self):
        """
        Log off, unconditionally.
        """
        session_uri = '/api/sessions/this-session'
        self.delete(session_uri, logon_required=False)
        self._session_id = None
        self._session = None
        self._headers.pop('X-API-Session', None)

    def get(self, uri, logon_required=True):
        """
        Perform the HTTP GET method against the resource identified by a URI.

        A set of standard HTTP headers is automatically part of the request.

        If the HMC session token is expired, this method re-logs on and retries
        the operation.

        Parameters:

          uri (:term:`string`):
            Relative URI path of the resource, e.g. "/api/session".
            This URI is relative to the base URL of the session (see
            the :attr:`~zhmcclient.Session.base_url` property).
            Must not be `None`.

          logon_required (bool):
            Boolean indicating whether the operation requires that the session
            is logged on to the HMC. For example, the API version retrieval
            operation does not require that.

        Returns:

          :term:`json object` with the operation result.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        if logon_required:
            self.logon()
        url = self.base_url + uri
        stats = self.time_stats_keeper.get_stats('get ' + uri)
        stats.begin()
        req = self._session or requests
        try:
            result = req.get(url, headers=self.headers, verify=False)
        except requests.exceptions.RequestException as exc:
            raise ConnectionError(str(exc))
        finally:
            stats.end()

        if result.status_code == 200:
            return result.json()
        elif result.status_code == 403:
            reason = result.json().get('reason', None)
            if reason == 5:
                # API session token expired: re-logon and retry
                if logon_required:
                    self._do_logon()
                else:
                    raise AuthError("API session token unexpectedly expired "
                                    "for GET on resource that does not "
                                    "require authentication: {}".
                                    format(uri))
                return self.get(uri, logon_required)
            else:
                exc = HTTPError(result.json())
                raise AuthError("HTTP authentication failed: {}".
                                format(str(exc)))
        else:
            raise HTTPError(result.json())

    def post(self, uri, body=None, logon_required=True, wait_for_completion=True):
        """
        Perform the HTTP POST method against the resource identified by a URI,
        using a provided request body.

        A set of standard HTTP headers is automatically part of the request.

        If the HMC performs the operation asynchronously, this method polls
        until the operation result is available.

        If the HMC session token is expired, this method re-logs on and retries
        the operation.

        Parameters:

          uri (:term:`string`):
            Relative URI path of the resource, e.g. "/api/session".
            This URI is relative to the base URL of the session (see the
            :attr:`~zhmcclient.Session.base_url` property).
            Must not be `None`.

          body (:term:`json object`):
            JSON object to be used as the HTTP request body (payload).
            `None` means the same as an empty dictionary, namely that no HTTP
            body is included in the request.

          logon_required (bool):
            Boolean indicating whether the operation requires that the session
            is logged on to the HMC. For example, the logon operation does not
            require that.

          wait_for_completion (bool):
            Boolean indicating whether the method should wait until
            the operation/job has completed.
            If wait_for_completion is 'False' the status of the operation/job
            has to be retrieved via the method 'query_job_status' method.

        Returns:

          :term:`json object` with the operation result.

            In the default case of a synchronous operation
            (wait_for_completion=True) the return value is a JSON object with
            members like status, job-status-code and job-reason-code.
            See the respective sections in :term:`HMC API` for a description
            of the response body contents of the Query Job Status operation.

            In case of an asynchronous operation (wait_for_completion=False),
            the return value is a JSON object with a member job-id whose value
            needs to be used for query_job_status().

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        if logon_required:
            self.logon()
        url = self.base_url + uri
        if body is None:
            body = {}
        data = json.dumps(body)
        stats = self.time_stats_keeper.get_stats('post ' + uri)
        stats.begin()
        req = self._session or requests
        try:
            result = req.post(url, data=data, headers=self.headers,
                              verify=False)
        except requests.exceptions.RequestException as exc:
            raise ConnectionError(str(exc))
        finally:
            stats.end()

        if result.status_code in (200, 204):
            return result.json()
        elif result.status_code == 202:
            job_uri = result.json()['job-uri']
            job_url = self.base_url + job_uri
            if not wait_for_completion:
                return result.json()
            while 1:
                stats = self.time_stats_keeper.get_stats('get ' + job_uri)
                stats.begin()
                try:
                    result = req.get(job_url, headers=self.headers,
                                     verify=False)
                except requests.exceptions.RequestException as exc:
                    raise ConnectionError(str(exc))
                finally:
                    stats.end()
                if result.status_code in (200, 204):
                    if result.json()['status'] == 'complete':
                        return result.json()
                    else:
                        # TODO: Add support for timeout
                        time.sleep(1)  # Avoid hot spin loop
                else:
                    raise HTTPError(result.json())
        elif result.status_code == 403:
            reason = result.json().get('reason', None)
            if reason == 5:
                # API session token expired: re-logon and retry
                if logon_required:
                    self._do_logon()
                else:
                    raise AuthError("API session token unexpectedly expired "
                                    "for POST on resource that does not "
                                    "require authentication: {}".
                                    format(uri))
                return self.post(uri, body, logon_required)
            else:
                exc = HTTPError(result.json())
                raise AuthError("HTTP authentication failed: {}".
                                format(str(exc)))
        else:
            raise HTTPError(result.json())

    def delete(self, uri, logon_required=True):
        """
        Perform the HTTP DELETE method against the resource identified by a
        URI.

        A set of standard HTTP headers is automatically part of the request.

        If the HMC session token is expired, this method re-logs on and retries
        the operation.

        Parameters:

          uri (:term:`string`):
            Relative URI path of the resource, e.g.
            "/api/session/{session-id}".
            This URI is relative to the base URL of the session (see
            the :attr:`~zhmcclient.Session.base_url` property).
            Must not be `None`.

          logon_required (bool):
            Boolean indicating whether the operation requires that the session
            is logged on to the HMC. For example, for the logoff operation, it
            does not make sense to first log on.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        if logon_required:
            self.logon()
        url = self.base_url + uri
        stats = self.time_stats_keeper.get_stats('delete ' + uri)
        stats.begin()
        req = self._session or requests
        try:
            result = req.delete(url, headers=self.headers, verify=False)
        except requests.exceptions.RequestException as exc:
            raise ConnectionError(str(exc))
        finally:
            stats.end()

        if result.status_code in (200, 204):
            return
        elif result.status_code == 403:
            reason = result.json().get('reason', None)
            if reason == 5:
                # API session token expired: re-logon and retry
                if logon_required:
                    self._do_logon()
                else:
                    raise AuthError("API session token unexpectedly expired "
                                    "for DELETE on resource that does not "
                                    "require authentication: {}".
                                    format(uri))
                self.delete(uri, logon_required)
                return
            else:
                exc = HTTPError(result.json())
                raise AuthError("HTTP authentication failed: {}".
                                format(str(exc)))
        else:
            raise HTTPError(result.json())

    def query_job_status(self, job_uri):
        """
        The Query Job Status operation returns the status associated
        with an asynchronous job.

        A set of standard HTTP headers is automatically part of the request.

        If the HMC session token is expired, this method re-logs on and retries
        the operation.

        Parameters:

          job_uri (:term:`string`):
            Relative Job URI path of the operation, e.g.
            "/api/jobs/{job-id}".
            This URI is relative to the base URL of the session (see
            the :attr:`~zhmcclient.Session.base_url` property).
            Must not be `None`.

        Returns:

          :term:`json object` with the operation result.

            The return value is a JSON object with members like status,
            job-status-code and job-reason-code.
            See the respective sections in :term:`HMC API` for a description
            of the response body contents of the Query Job Status operation.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.get(job_uri)
        return result
