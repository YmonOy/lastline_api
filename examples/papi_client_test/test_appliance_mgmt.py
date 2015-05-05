#!/usr/bin/python
"""
Unit tests for the appliance_mgmt client.

:Copyright:
     Copyright 2014 Lastline, Inc.  All Rights Reserved.
"""
import mox

from papi_client import loader
import papi_client
import papi_client.papi_client
import papi_client.api.appliance_mgmt


class TestApplianceMgmt(mox.MoxTestBase):
    """
    Basic tests for intel view

    """
    def setUp(self):
        mox.MoxTestBase.setUp(self)
        self.conf = self.mox.CreateMockAnything()
        self.client_mock = self.mox.CreateMock(
            papi_client.papi_client.PapiClient
        )
        self.amgmt = papi_client.api.appliance_mgmt.PapiClientApplianceMgmt(
            base_client=self.client_mock
        )
        self.mox.StubOutWithMock(self.amgmt, "_get")
        self.mox.StubOutWithMock(self.amgmt, "_post")

    def test_ping(self):
        self.amgmt._get("ping", raw=False).AndReturn("pong")

        self.mox.ReplayAll()
        result = self.amgmt.ping()
        self.assertEqual(result, "pong")

    def test_get_overview(self):
        r = self.amgmt._get("overview", params={}, raw=False)
        r.AndReturn({})
        r = self.amgmt._get("overview", params={"user_id": 3}, raw=False)
        r.AndReturn({"3"})

        self.mox.ReplayAll()
        result = self.amgmt.get_overview()
        self.assertEqual(result, {})
        result = self.amgmt.get_overview(user_id=3)
        self.assertEqual(result, {"3"})

    def test_get_configuration(self):
        params = {"appliance_uuid": "A" * 32}
        params2 = {k: v for k, v in params.iteritems()}
        params2["user_id"] = 3

        r = self.amgmt._get("configuration", params=params, raw=False)
        r.AndReturn("CONF")
        r = self.amgmt._get("configuration", params=params2, raw=False)
        r.AndReturn("CONF2")

        self.mox.ReplayAll()
        result = self.amgmt.get_configuration("A" * 32)
        self.assertEqual(result, "CONF")
        result = self.amgmt.get_configuration("A" * 32, user_id=3)
        self.assertEqual(result, "CONF2")

    def test_configure_no_params(self):

        data = {
            "appliance_uuid": "A" * 32,
            "action_parameters": "{}",
            "action_type": "CONFIGURE"
        }
        r = self.amgmt._post("action/request", data=data, raw=False)
        r.AndReturn("UUID")

        data2 = {k: v for k, v in data.iteritems()}
        data2["user_id"] = 3
        r = self.amgmt._post("action/request", data=data2, raw=False)
        r.AndReturn("UUID2")

        self.mox.ReplayAll()
        result = self.amgmt.configure("A" * 32)
        self.assertEqual(result, "UUID")
        result = self.amgmt.configure("A" * 32, user_id=3)
        self.assertEqual(result, "UUID2")

    def test_configure_full_params(self):

        # This might/will break depending on the JSON encoder :-(
        action_params = ('{"auto_update": false, "software_version": "V", '
                          '"settings": {"some_setting": "true"}}')
        data = {
            "appliance_uuid": "A" * 32,
            "action_parameters": action_params,
            "action_type": "CONFIGURE"
        }
        r = self.amgmt._post("action/request", data=data, raw=False)
        r.AndReturn("UUID")

        data2 = {k: v for k, v in data.iteritems()}
        data2["user_id"] = 3
        r = self.amgmt._post("action/request", data=data2, raw=False)
        r.AndReturn("UUID2")

        self.mox.ReplayAll()
        result = self.amgmt.configure(
            appliance_uuid="A" * 32,
            software_version="V",
            auto_update=False,
            settings={"some_setting": "true"}
        )
        self.assertEqual(result, "UUID")
        result = self.amgmt.configure(
            appliance_uuid="A" * 32,
            software_version="V",
            auto_update=False,
            settings={"some_setting": "true"},
            user_id=3
        )
        self.assertEqual(result, "UUID2")

    def test_get_action_status(self):
        params = {"action_uuid": "B" * 32}
        params2 = {k: v for k, v in params.iteritems()}
        params2["user_id"] = 3

        r = self.amgmt._get("action/status", params=params, raw=False)
        r.AndReturn("STAT")
        r = self.amgmt._get("action/status", params=params2, raw=False)
        r.AndReturn("STAT2")

        self.mox.ReplayAll()
        result = self.amgmt.get_action_status("B" * 32)
        self.assertEqual(result, "STAT")
        result = self.amgmt.get_action_status("B" * 32, user_id=3)
        self.assertEqual(result, "STAT2")

    def test_loading(self):

        self.mox.ReplayAll()
        collection = loader.PapiClientCollection(
            base_client=self.client_mock,
            conf=self.conf
        )
        collection.load_view("appliance_mgmt")


if __name__ == "__main__":
    mox.unittest.main()
