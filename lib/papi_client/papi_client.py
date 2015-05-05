#!/usr/bin/python
"""
Basic papi user client.

Can be used as handle.

:Copyright:
     Copyright 2014 Lastline, Inc.  All Rights Reserved.
"""
# so that we don't import papi_client.papi_client instead of papi_client
from __future__ import absolute_import

import copy
import time
import urlparse
import requests


# Unused import - but used by others.
# pylint: disable=W0611
try:
    import simplejson as json
except ImportError:
    import json
# pylint: enable=W0611
import papi_client.errors


# Duplicated from llutils.llapi
LLAPI_ERROR__PERMISSION_DENIED = 3001
LLAPI_ERROR__CANNOT_SWITCH_TO_KEY = 3002
LLAPI_ERROR__NO_KEY_SELECTED = 3003
LLAPI_ERROR__AUTHENTICATION_ERROR = 3004

# We retry once if we get one of these error codes:
RETRY_ERROR_CODES = frozenset([
    LLAPI_ERROR__PERMISSION_DENIED,
    LLAPI_ERROR__CANNOT_SWITCH_TO_KEY,
    LLAPI_ERROR__NO_KEY_SELECTED,
    LLAPI_ERROR__AUTHENTICATION_ERROR,
])


class Error(papi_client.errors.Error):
    """
    Base class for all exceptions in this module
    """
    def __init__(self, *args):
        papi_client.errors.Error.__init__(self, *args)


class CommunicationError(Error):
    pass


class ApiError(Error):

    def __init__(self, error_msg, error_code=None):
        Error.__init__(self, error_msg, error_code)
        self.error_msg = error_msg
        self.error_code = error_code

    def __str__(self):
        return "%s%s" % (str(self.error_msg), " (%s)" % self.error_code if \
                        self.error_code is not None else "")


class InvalidArgument(Error):
    pass


DEFAULT_BASE_URL = "https://user.lastline.com/ll_api/ll_api.php"

class PapiClientFactory(object):
    """
    Factory to create PapiClient instances.
    """
    @staticmethod
    def client_from_config(conf, section_name, logger=None, proxies=None):
        """
        Create a new PapiClient from a config section.

        Template if section name is [papi]:
            [papi]
            url = https://user.lastline.com/papi

            # Either user-based,
            auth_method = account
            username = your_user@your_site.com
            password = ***********

            # or license/key based
            auth_method = license
            api_key = 12345...45123451234512345
            api_token = ***********

            verify_ssl = True
            timeout = 3

        :param conf: ConfigParser instance
        :param section: which section to use
        :param logger: log here
        """
        # strip trailing slash
        url = conf.get(section_name, "url").strip("/")

        verify_ssl = True
        if conf.has_option(section_name, "verify_ssl"):
            verify_ssl = conf.getboolean(section_name, "verify_ssl")

        timeout = 60
        if conf.has_option(section_name, "timeout"):
            timeout = conf.getint(section_name, "timeout")

        method = conf.get(section_name, "auth_method").lower()

        supported_methods = ["account", "license"]
        if method not in supported_methods:
            raise InvalidArgument(
                "method '%s' not in %s" % (method, ", ".join(supported_methods))
            )

        if method == "account":
            login_params = {
                "username": conf.get(section_name, "username"),
                "password": conf.get(section_name, "password")
            }
        else:
            login_params = {
                "api_key": conf.get(section_name, "api_key"),
                "api_token": conf.get(section_name, "api_token"),
            }

        return PapiClient(
            url=url,
            login_params=login_params,
            verify_ssl=verify_ssl,
            timeout=timeout,
            logger=logger,
            proxies=proxies
        )


class KeyIds(object):
    def __init__(self, key_id, subkey_id=None):
        self._key_id = key_id
        self._subkey_id = subkey_id
    
    def get_key_params(self):
        result = {"key_id":self._key_id}
        if self._subkey_id:
            result["subkey_id"] = self._subkey_id
        
        return result


class PapiClient(object):
    """"
    A very basic API client providing basic functionality
    for client modules to build upon.

    Provides:
     - login()
     - logout()
     - do_request()

    Only interprets JSON responses, but supports XML with the raw option. 
    Whenever there
    is a CommunicationError or API erros related to permissions, a *single*
    retry is attempted. This should help to transparently recover from
    interrupted TCP connections or expired sessions.

    Either inherit from this class or use it as a handle to your client - the
    latter follows the "composition over inheritance" concept and will make
    testing easier.
    """
    def __init__(self, url, login_params, verify_ssl=True, timeout=60,
                 proxies=None, logger=None):
        """
        Instantiate a PapiClient.

        :param login_params: POST parameters used during login
        """
        if not url:
            raise InvalidArgument("url missing")

        # Require http or https - anything else is an error.
        scheme = urlparse.urlparse(url).scheme  # pylint: disable=E1101
        if scheme not in ["http", "https"]:
            msg = "Invalid URL '%s': Invalid scheme '%s'" % (url, scheme)
            raise InvalidArgument(msg)

        self.__url = url

        if not login_params:
            raise InvalidArgument("no login_params")

        if "username" in login_params and not "password" in login_params:
            raise InvalidArgument("username without password")

        if "api_key" in login_params and not "api_token" in login_params:
            raise InvalidArgument("api_key without api_token")

        self.__login_params = copy.deepcopy(login_params)
        self.__session = None

        self.__verify_ssl = verify_ssl
        self.__timeout = timeout

        # Make sure we do not get bogus proxy settings.
        if proxies:
            if not proxies.get("https", None):
                raise InvalidArgument("No valid 'https' proxy in proxies")
        self.__proxies = proxies

        self.__logger = logger

    def have_logger(self):
        return not self.__logger is None

    def get_logger(self):
        return self.__logger

    def __log_request_duration(self, start, end):
        took_ms = int((end - start) * 1000)
        if self.have_logger():
            self.__logger.debug("Request took %s ms", took_ms)

    def __handle_response(self, response, raw, __fmt=None):
        """
        Check a response for issues and parse the return.

        :param: response requests.Response
        :return: if raw the data in the body, if not raw, the data field
        :raises: CommunicationError, ApiError
        """
        try:
            response.raise_for_status()
        except requests.RequestException as e:
            raise CommunicationError(e)

        if raw:
            return response.content

        try:
            ret = response.json()
            if "success" not in ret:
                raise Error("no success field in response")

            if not ret["success"]:
                error_msg = ret.get("error", "")
                error_code = ret.get("error_code", None)
                raise ApiError(error_msg, error_code)

            if "data" not in ret:
                raise Error("no data field in response")

            return ret["data"]
        except ValueError as e:
            if self.have_logger():
                self.__logger.error("Response not json: %s", str(e))
            raise Error("Response not json %s" % str(e))


    def login(self, raw=False):
        """
        Login using account-based or key-based methods.

        We *always* use a POST request and we *always* use JSON format.
        """
        if self.__session is None:
            self.__session = requests.session()

        login_url = "/".join([self.__url, "login"])

        if self.have_logger():
            self.__logger.debug("Logging in...")

        start = time.time()
        try:
            response = self.__session.request(
                method="POST",
                url=login_url,
                data=self.__login_params,
                verify=self.__verify_ssl,
                timeout=self.__timeout,
                proxies=self.__proxies
            )
        except requests.RequestException as e:
            raise CommunicationError(e)

        end = time.time()
        self.__log_request_duration(start, end)

        self.__handle_response(response, raw)

        if self.have_logger():
            self.__logger.debug("Completed.")

    def logout(self):
        """
        Log out and tear down the TCP connection.
        """
        ret = self.do_request("POST", module="", function="logout")
        self.__session = None
        return ret

    def __is_logged_in(self):
        return self.__session is not None


    def do_request(self, method, module, function, params=None, data=None,
                   files=None, url=None, fmt="JSON", raw=False):
        """
        Helper around requests.request() to provide some functionality that
        should ease writing a papi client.

        :param method: HTTP method POST|GET
        :param module: papi module to talk to (appliance_mgmt, blacklist, ...)
        :param function: function to use (ping, overview, ...)
        :param params: as for requests.request()
        :param data: as for requests.request()
        :param files: as for requests.request()
        :param url: Override the URL as given in the constructor (testing)
        :param fmt: format to be returned by the API XML|JSON
        :param raw: return the raw body (required for non-json formats)
        """

        fmt = fmt.lower().strip()
        if fmt not in ["json", "xml", "html", "pdf"]:
            raise InvalidArgument("Only json, xml, html and pdf supported")

        # Only with json we support parsing of the respnse.
        if fmt != "json" and not raw:
            raise InvalidArgument("Non-json format requires raw=True")

        if not method in ["POST", "GET"]:
            raise InvalidArgument("Only POST and GET supported")

        # We allow empty modules.
        module = module.strip(" /")
        function = function.strip(" /")
        if not function:
            raise InvalidArgument("No function provided")

        if not self.__is_logged_in():
            self.login()

        url_parts = [url or self.__url]
        if module:
            url_parts.append(module)
        url_parts.append("%s.%s" %(function, fmt))

        url = "/".join(url_parts)


        # We try at most two times! And we only retry if there is a
        # CommunicationError or an API error indicating permission issues.
        for i in range(2):
            if self.have_logger():
                self.__logger.debug("Doing %s request to %s", method, url)

            try:
                start = time.time()
                response = self.__session.request(
                    method=method,
                    url=url,
                    data=data,
                    params=params,
                    files=files,
                    verify=self.__verify_ssl,
                    timeout=self.__timeout,
                    proxies=self.__proxies
                )
                end = time.time()
                self.__log_request_duration(start, end)

                return self.__handle_response(response, raw, fmt)

            except ApiError as e:
                if self.have_logger():
                    self.__logger.error("ApiError: %s", str(e))

                # Second time around? Just raise...
                if i == 1:
                    raise e

                # Some errors say "Permission denied", but do not contain an
                # error code... Check "Permission denied explicitly.
                if e.error_code not in RETRY_ERROR_CODES and \
                        "Permission denied" not in e.error_msg:
                    raise e

                # If we received a "Permission denied" error, drop all
                # cookies and login again. This will keep the connection
                # established.
                self.__session.cookies.clear()

            except CommunicationError as e:

                # Reset the session.
                self.__session = None

                if self.have_logger():
                    self.__logger.error("CommunicationError: %s", str(e))

                # Second time around? Just raise...
                if i == 1:
                    raise e

            if self.have_logger():
                self.__logger.debug("Retrying failed request...")

            # Unconditional login for retry...
            self.login()

    @staticmethod
    def _get_key_params(key):
        if isinstance(key, basestring):
            return {"key":key}
        if hasattr(key, "get_key_params"):
            return key.get_key_params()
        raise InvalidArgument("Argument is not a license key")


    def ping(self, module="", fmt="JSON", raw=False):
        """
        Check if base API responds.
        """
        return self.do_request(
            method="GET",
            module=module,
            function="ping",
            fmt=fmt,
            raw=raw
        )

