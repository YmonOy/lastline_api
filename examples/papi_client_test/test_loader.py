#!/usr/bin/python
"""
Unit tests for the loader

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
from papi_client.api import intel
from papi_client.api import postprocessing


# You need to update this if you add a new Client/View, unfortunately.
ALL_IMPLEMENTED_VIEWS = [
    "appliance_mgmt",
    "intel",
    "postprocessing",
]

class TestLoader(unittest.TestCase):
    """
    Unit test for this module.
    """
    def setUp(self):
        self.mock = mox.Mox()
        self.stubs = stubout.StubOutForTesting()
        
        self.logger = logging.getLogger()
        sh = logging.StreamHandler()
        self.logger.setLevel(logging.FATAL)
        sh.setLevel(logging.FATAL)
        self.logger.addHandler(sh)
        
        self.base_client = self.mock.CreateMock(papi_client.PapiClient)
    
    def tearDown(self):
        self.mock.UnsetStubs()
        self.stubs.UnsetAll()
        self.stubs.SmartUnsetAll()
    
    def test_load_all(self):
        config_parser = ConfigParser.ConfigParser()
        base_client = "stub of a PapiClient"
        
        client = loader.PapiClientCollection(base_client=base_client,
                                             conf=config_parser,
                                             logger=self.logger)
        client.load_all_views()
        
        views = client.list_views()
        self.assertEqual(views, ALL_IMPLEMENTED_VIEWS)
        self.assertEquals(client.intel.description(), "Custom intelligence API")  # pylint: disable=E1101
        return client
    
    def test_load_module(self):
        config_parser = ConfigParser.ConfigParser()
        base_client = "stub of a PapiClient"
        client = loader.PapiClientCollection(base_client=base_client,
                                             conf=config_parser,
                                             logger=self.logger)
        intel_view = loader.PapiViewLoader.get_view_from_module(
            module=intel,
            base_client=base_client,
            conf=config_parser,
            logger=self.logger)
        client.add_view("intel", intel_view)
        
        views = client.list_views()
        self.assertEqual(views, ["intel"])
    
    def test_get_view(self):
        client = self.test_load_all()
        
        self.assertEquals(client.view("intel").name(), "intel")
        with self.assertRaises(loader.NoSuchView):
            client.view("nosuchview")


class TestFactory(unittest.TestCase):
    """
    Unit test for this module's factory methods.
    """
    def setUp(self):
        self.mock = mox.Mox()

        self.logger = logging.getLogger()
        sh = logging.StreamHandler()
        self.logger.setLevel(logging.FATAL)
        sh.setLevel(logging.FATAL)
        self.logger.addHandler(sh)

    def tearDown(self):
        self.mock.UnsetStubs()

    def test_view_factory(self):
        """
        Test factory of different views
        """
        conf = ConfigParser.ConfigParser()
        mock_client = self.mock.CreateMock(papi_client.PapiClient)

        view = postprocessing.PapiClientPostprocessing.\
            client_from_config(mock_client, conf, self.logger)
        self.assertEqual(view.name(), 'postprocessing')
        self.assertEqual(view._client, mock_client)

        view = intel.PapiClientIntel.\
            client_from_config(mock_client, conf, self.logger)
        self.assertEqual(view.name(), 'intel')
        self.assertEqual(view._client, mock_client)

        # for convenience, we declare the factory on the base-class. Make
        # sure this does not mean one can instantiate the abstract view
        with self.assertRaises(Exception) as err:
            loader.PapiViewClient.\
                client_from_config(mock_client, conf, self.logger)
        self.assertEqual(err.exception.message,
                         'Factory must be called on a specific '
                         'PapiViewClient subclass')

    def test_view_with_client_from_config(self):
        """
        Test generating a view+client via the factory method
        """
        conf = ConfigParser.ConfigParser()
        conf.add_section('test_client')
        conf.set('test_client', 'url', 'http://test')
        conf.set('test_client', 'auth_method', 'account')
        conf.set('test_client', 'username', 'test_user')
        conf.set('test_client', 'password', 'test_password')
        conf.set('test_client', 'verify_ssl', 'false')
        conf.set('test_client', 'timeout', '123')

        self.mock.StubOutClassWithMocks(papi_client, 'PapiClient')
        mock_client = papi_client.PapiClient(
            url='http://test',
            login_params={
                'username': 'test_user',
                'password': 'test_password',
            },
            verify_ssl=False,
            timeout=123,
            logger=self.logger,
            proxies=None
        )

        self.mock.ReplayAll()
        result_view = postprocessing.PapiClientPostprocessing.\
            view_with_client_from_config(conf, 'test_client', self.logger)
        self.mock.VerifyAll()

        self.assertEqual(result_view._client, mock_client)


if __name__ == '__main__':
    exit(unittest.main())
