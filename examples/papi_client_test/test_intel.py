#!/usr/bin/python
"""
Unit tests for the intel view

:Copyright: 
     Copyright 2014 Lastline, Inc.  All Rights Reserved.
"""
import ConfigParser
import unittest
import logging
import mox
import stubout


from papi_client import loader
from papi_client import papi_client

KEY1 = "A" *20

class TestIntel(unittest.TestCase):
    """
    Basic tests for intel view
    
    Here we're just testing a single get and a single post-based API
    to see that the whole framework works correctly.
    """
    def setUp(self):
        self.mock = mox.Mox()
        self.stubs = stubout.StubOutForTesting()
        
        self.logger = logging.getLogger()
        sh = logging.StreamHandler()
        self.logger.setLevel(logging.FATAL)
        sh.setLevel(logging.FATAL)
        self.logger.addHandler(sh)
        
        self.conf = ConfigParser.ConfigParser()
        self.base_client = self.mock.CreateMock(papi_client.PapiClient)
        self.client = loader.PapiClientCollection(base_client=self.base_client,
                                                  conf=self.conf,
                                                  logger=self.logger)
        self.client.load_view("intel")
        self.intel_client = self.client.intel  # pylint: disable=E1101
    
    def tearDown(self):
        self.mock.UnsetStubs()
        self.stubs.UnsetAll()
        self.stubs.SmartUnsetAll()
    
    def test_nop(self):
        # just test setup/teardown
        pass

    def test_list_ip(self):
        ########################################
        # record interaction with mock objects
        self.base_client.do_request(
            fmt='JSON',
            function='ip/list',
            method='GET',
            module='intel',
            params={"source":"bad list"},
            raw=False
        ).AndReturn([])
        
        ########################################
        # actually run the task
        self.mock.ReplayAll()
        self.intel_client.list_ip(source="bad list")
        self.mock.VerifyAll()
    
    def test_list_ip_key(self):
        ########################################
        # record interaction with mock objects
        self.base_client.do_request(
            fmt='JSON',
            function='ip/list',
            method='GET',
            module='intel',
            params={
                "key":KEY1,
                "source":"bad list"
            },
            raw=False
        ).AndReturn([])
        
        ########################################
        # actually run the task
        self.mock.ReplayAll()
        self.intel_client.list_ip(key=KEY1, source="bad list")
        self.mock.VerifyAll()
    
    def test_list_ip_key_ids(self):
        key_ids = papi_client.KeyIds(key_id=33, subkey_id=77)
        
        ########################################
        # record interaction with mock objects
        self.base_client.do_request(
            fmt='JSON',
            function='ip/list',
            method='GET',
            module='intel',
            params={
                "key_id":33,
                "subkey_id":77,
                "source":"bad list"
            },
            raw=False
        ).AndReturn([])
        
        ########################################
        # actually run the task
        self.mock.ReplayAll()
        self.intel_client.list_ip(key=key_ids, source="bad list")
        self.mock.VerifyAll()
    
    def test_add_ip(self):
        entries = [
            {"ip":"1.2.3.4"}
        ]
        
        ########################################
        # record interaction with mock objects
        self.base_client.do_request(
            data={'key': 'AAAAAAAAAAAAAAAAAAAA',
                  'entries': '[{"ip": "1.2.3.4"}]'},
            files=None,
            fmt='JSON',
            function='ip/add',
            method='POST',
            module='intel',
            params=None,
            raw=False
        ).AndReturn([])
        
        ########################################
        # actually run the task
        self.mock.ReplayAll()
        self.intel_client.add_ip(entries=entries, key=KEY1)
        self.mock.VerifyAll()
        


if __name__ == '__main__':
    exit(unittest.main())
