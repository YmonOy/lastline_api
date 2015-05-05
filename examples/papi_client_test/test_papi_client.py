#!/usr/bin/python
"""
Some smoke tests for the papi_client.

We mock requests.request() and requests.session(), these test are not supposed
to do real network connections.

:Copyright:
     Copyright 2014 Lastline, Inc.  All Rights Reserved.
"""
import ConfigParser
import ddt
import logging
import mox
import unittest

from papi_client import papi_client
from papi_client.papi_client import requests
import requests.cookies


class TestPapiClientFactory(unittest.TestCase):

    def setUp(self):
        self.mock = mox.Mox()
        self.conf = ConfigParser.ConfigParser()
        self.conf.add_section("papi")
        self.conf.set("papi", "url", "https://xyz.not.reachable.local")

        self.mock.StubOutClassWithMocks(papi_client, "PapiClient")

    def tearDown(self):
        self.mock.UnsetStubs()
        self.mock.ResetAll()

    def test_license_auth(self):
        self.conf.set("papi", "auth_method", "license")
        self.conf.set("papi", "api_key", "E" * 20)
        self.conf.set("papi", "api_token", "TickTock")
        mock = papi_client.PapiClient(
            url="https://xyz.not.reachable.local",
            login_params={"api_key": "E" * 20, "api_token": "TickTock"},
            verify_ssl=True,
            timeout=60,
            logger=None,
            proxies=None
        )

        self.mock.ReplayAll()
        c = papi_client.PapiClientFactory.client_from_config(self.conf, "papi")
        self.assertIs(c, mock)
        self.mock.VerifyAll()

    def test_account_auth(self):
        self.conf.set("papi", "auth_method", "account")
        self.conf.set("papi", "username", "j@ll.com")
        self.conf.set("papi", "password", "pa55wordz")
        mock = papi_client.PapiClient(
            url="https://xyz.not.reachable.local",
            login_params={"username": "j@ll.com", "password": "pa55wordz"},
            verify_ssl=True,
            timeout=60,
            logger=None,
            proxies=None
        )

        self.mock.ReplayAll()
        c = papi_client.PapiClientFactory.client_from_config(self.conf, "papi")
        self.assertIs(c, mock)
        self.mock.VerifyAll()

    def test_proxy_forwarded(self):
        self.conf.set("papi", "auth_method", "license")
        self.conf.set("papi", "api_key", "E" * 20)
        self.conf.set("papi", "api_token", "TickTock")
        mock = papi_client.PapiClient(
            url="https://xyz.not.reachable.local",
            login_params={"api_key": "E" * 20, "api_token": "TickTock"},
            verify_ssl=True,
            timeout=60,
            logger=None,
            proxies={"https": "127.0.0.9:9189"}
        )

        self.mock.ReplayAll()
        c = papi_client.PapiClientFactory.client_from_config(
            self.conf, "papi", proxies={"https": "127.0.0.9:9189"}
        )
        self.assertIs(c, mock)
        self.mock.VerifyAll()

@ddt.ddt
class TestPapiClient(unittest.TestCase):
    """
    Basic tests for intel view

    Here we're just testing a single get and a single post-based API
    to see that the whole framework works correctly.
    """
    def setUp(self):
        self.mock = mox.Mox()

        self.logger = logging.getLogger()
        sh = logging.StreamHandler()
        self.logger.setLevel(logging.FATAL)
        sh.setLevel(logging.FATAL)
        self.logger.addHandler(sh)

        self.session = self.mock.CreateMock(requests.Session)
        self.cookies = self.mock.CreateMock(requests.cookies.RequestsCookieJar)
        self.session.cookies = self.cookies

        self.mock.StubOutWithMock(requests, "request")
        self.mock.StubOutWithMock(requests, "session")

    def tearDown(self):
        self.mock.UnsetStubs()
        self.mock.ResetAll()

    def make_test_client(self, proxies=None):
        return papi_client.PapiClient(
            url="https://non-reachable-test-url",
            login_params={
                "username": "test",
                "password": "test1234",
            },
            proxies=proxies
        )

    def make_response(self):
        return self.mock.CreateMockAnything()

    def mock_login(self, proxies=None):
        call = self.session.request(
            method="POST",
            url="https://non-reachable-test-url/login",
            data=mox.IgnoreArg(),
            verify=True,
            timeout=60,
            proxies=proxies
        )

        response = self.make_response()
        response.raise_for_status()
        response.json().AndReturn({"success": 1, "data": []})
        call.AndReturn(response)  # pylint: disable=E1101

    @ddt.data(
        (
            {"url": "", "login_params": {"username": "john", "password": "xyz"}},
            "url missing"
        ),
        (
            {"url": "https://url", "login_params": {}},
            "no login_params"
        ),
        (
            {"url": "https://url", "login_params": {"username": "john"}},
            "username without password"
        ),
        (
            {"url": "https://url", "login_params": {"api_key": "1234"}},
            "api_key without api_token"
        ),
        (
            {
                "url": "ftp://random.host",
                "login_params": {"username": "john", "password": "xyz"}
            },
            "^Invalid URL 'ftp://random.host': Invalid scheme 'ftp'$"
        ),
        (
            {
                "url": "url=random.host",
                "login_params": {"username": "john", "password": "xyz"}
            },
            "^Invalid URL 'url=random.host': Invalid scheme ''$"
        ),
        (
            {
                "url": "http://unreachable.host.local:6666",
                "login_params": {"username": "john", "password": "xyz"},
                "proxies": {"ftp": "127.1.1.9:3128"},
            },
            "^No valid 'https' proxy in proxies"
        ),
        (
            {
                "url": "http://unreachable.host.local:6666",
                "login_params": {"username": "john", "password": "xyz"},
                "proxies": {"https": ""},
            },
            "^No valid 'https' proxy in proxies"
        ),
    )
    def test_init_fail(self, args):
        kwargs, regex = args

        with self.assertRaisesRegexp(papi_client.InvalidArgument, regex):
            papi_client.PapiClient(**kwargs)


    @ddt.data(
        "http://unreachable.host.com/test.php",
        "https://unreachable.host.com/test.php",
        "https://unreachable.host.com/test/",
    )
    def test_ok_url(self, url):
        papi_client.PapiClient(
            url=url,
            login_params={
                "api_key": "test_key_long",
                "api_token": "test_api_token_1234",
            }
        )

    def test_init_account(self):
        self.make_test_client()

    def test_init_api_key(self):
        papi_client.PapiClient(
            url="https://non-reachable",
            login_params={
                "api_key": "test_key_long",
                "api_token": "test_api_token_1234",
            }
        )

    def test_login(self):
        c = self.make_test_client()

        call = requests.session()
        call.AndReturn(self.session)  # pylint: disable=E1101
        self.mock_login()

        self.mock.ReplayAll()
        c.login()
        self.mock.VerifyAll()

    def test_login_with_proxy(self):
        test_proxies = {"https": "127.0.0.9:9281"}
        c = self.make_test_client(proxies=test_proxies)

        call = requests.session()
        call.AndReturn(self.session)  # pylint: disable=E1101
        self.mock_login(proxies=test_proxies)

        self.mock.ReplayAll()
        c.login()
        self.mock.VerifyAll()

    def test_login_failure(self):
        call = requests.session()
        call.AndReturn(self.session)  # pylint: disable=E1101
        call = self.session.request(
            method="POST",
            url="https://non-reachable-test-url/login",
            data=mox.IgnoreArg(),
            verify=True,
            timeout=60,
            proxies=None
        )
        call.AndRaise(requests.RequestException("Early error"))

        self.mock.ReplayAll()
        c = self.make_test_client()

        with self.assertRaises(papi_client.CommunicationError):
            c.do_request("GET", module="foobar", function="ping")
        self.mock.VerifyAll()

    def test_do_request(self):
        c = self.make_test_client()

        call = requests.session()
        call.AndReturn(self.session)  # pylint: disable=E1101

        self.mock_login()

        call = self.session.request(
            method="GET",
            url="https://non-reachable-test-url/foobar/ping.json",
            data=mox.IgnoreArg(),
            params=None,
            files=None,
            verify=True,
            timeout=60,
            proxies=None
        )

        response = self.make_response()
        response.raise_for_status()
        response.json().AndReturn({"success": 1, "data": "pong"})
        call.AndReturn(response)  # pylint: disable=E1101

        self.mock.ReplayAll()
        ret = c.do_request(
            method="GET",
            module="foobar",
            function="ping",
        )
        self.assertEqual(ret, "pong")
        self.mock.VerifyAll()

    def test_do_request_with_proxy(self):
        test_proxies = {"https": "127.0.0.9:9281"}
        c = self.make_test_client(proxies=test_proxies)

        call = requests.session()
        call.AndReturn(self.session)  # pylint: disable=E1101

        self.mock_login(proxies=test_proxies)

        call = self.session.request(
            method="GET",
            url="https://non-reachable-test-url/foobar/ping.json",
            data=mox.IgnoreArg(),
            params=None,
            files=None,
            verify=True,
            timeout=60,
            proxies=test_proxies
        )

        response = self.make_response()
        response.raise_for_status()
        response.json().AndReturn({"success": 1, "data": "pong"})
        call.AndReturn(response)  # pylint: disable=E1101

        self.mock.ReplayAll()
        ret = c.do_request(
            method="GET",
            module="foobar",
            function="ping",
        )
        self.assertEqual(ret, "pong")
        self.mock.VerifyAll()

    def test_do_request_retry_error(self):
        c = self.make_test_client()

        call = requests.session()
        call.AndReturn(self.session)  # pylint: disable=E1101

        self.mock_login()

        call = self.session.request(
            method="GET",
            url="https://non-reachable-test-url/foobar/ping.json",
            data=mox.IgnoreArg(),
            params=None,
            files=None,
            verify=True,
            timeout=60,
            proxies=None
        )
        response = self.make_response()
        response.raise_for_status()
        response.json().AndReturn({"success": 0, "error_code": 3001})
        call.AndReturn(response)  # pylint: disable=E1101

        # On Permission denied, remove all cookies.
        self.session.cookies.clear()
        self.mock_login()

        # Success this time
        call = self.session.request(
            method="GET",
            url="https://non-reachable-test-url/foobar/ping.json",
            data=mox.IgnoreArg(),
            params=None,
            files=None,
            verify=True,
            timeout=60,
            proxies=None
        )
        response = self.make_response()
        response.raise_for_status()
        response.json().AndReturn({"success": 1, "data": "pong"})
        call.AndReturn(response)  # pylint: disable=E1101

        self.mock.ReplayAll()
        ret = c.do_request(
            method="GET",
            module="foobar",
            function="ping",
        )
        self.assertEqual(ret, "pong")
        self.mock.VerifyAll()

    @ddt.data(
        {"success": 0, "error_code": 4711},
        {"success": 0, "error_code": 4711, "error": "Eau de Cologne"},
        {"success": 0, "error": "Eau de Cologne"},
    )
    def test_api_error(self, arg):
        c = self.make_test_client()

        call = requests.session()
        call.AndReturn(self.session)  # pylint: disable=E1101

        self.mock_login()

        call = self.session.request(
            method="GET",
            url="https://non-reachable-test-url/foobar/ping.json",
            data=mox.IgnoreArg(),
            params=None,
            files=None,
            verify=True,
            timeout=60,
            proxies=None
        )

        response = self.make_response()
        response.raise_for_status()
        response.json().AndReturn(arg)
        call.AndReturn(response)  # pylint: disable=E1101

        self.mock.ReplayAll()
        with self.assertRaises(papi_client.ApiError):
            c.do_request("GET", module="foobar", function="ping")
        self.mock.VerifyAll()

    @ddt.data(
        {"data": "no success field"},
        {"success": 1, "something": "no data field"},
    )
    def test_missing_field(self, arg):
        c = self.make_test_client()

        call = requests.session()
        call.AndReturn(self.session)  # pylint: disable=E1101

        self.mock_login()

        call = self.session.request(
            method="GET",
            url="https://non-reachable-test-url/foobar/ping.json",
            data=mox.IgnoreArg(),
            params=None,
            files=None,
            verify=True,
            timeout=60,
            proxies=None
        )

        response = self.make_response()
        response.raise_for_status()
        response.json().AndReturn(arg)
        call.AndReturn(response)  # pylint: disable=E1101

        self.mock.ReplayAll()
        with self.assertRaises(papi_client.Error):
            c.do_request("GET", module="foobar", function="ping")
        self.mock.VerifyAll()


if __name__ == "__main__":
    exit(unittest.main())
