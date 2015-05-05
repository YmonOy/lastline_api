#!/usr/bin/python
"""
Loader for papi clients for all supported papi API views

:Copyright:
     Copyright 2014 Lastline, Inc.  All Rights Reserved.
"""
# so that we don't import papi_client.papi_client instead of papi_client
from __future__ import absolute_import

import sys
import inspect
import pkgutil

import papi_client.api
import papi_client.errors
import papi_client.papi_client

class Error(papi_client.errors.Error):
    """
    Base class for all exceptions in this module
    """


class NoSuchView(Error):
    """
    The requested PAPI view client cannot be found
    """
    def __init__(self, view):
        Error.__init__(self, "No such view '%s'" % str(view))


class DuplicateView(Error):
    """
    Already have a view with this name!
    """
    def __init__(self, view):
        Error.__init__(self, "Duplicate view '%s'" % str(view))


class UnexpectedView(Error):
    """
    This view is not what I expected it to be
    """


def import_module(name):
    """
    Import a module by name. 
    
    Name can use the . notation.
    Unlike the builtin function __import__, 
    return value is the last part to the right:
    
    example:
        import_module("package.module.submodule")
        
        returns the submodule, while
        
        __import__("package.module.submodule")
        
        returns the package
    
    Copied out of llutils.llfs to make this code
    self-contained
    """
    __import__(name)
    return sys.modules[name]


class PapiViewClient(object):
    """
    Abstract base class for a client that can send API requests
    to a view (a module) of the PAPI.
    """
    @classmethod
    def client_from_config(cls, base_client, conf, logger=None):
        """
        Factory method for constructing a view; Needed by PapiClientCollection
        to load instances of this class
        """
        _unused = conf
        if cls == PapiViewClient:
            # we're implementing this factory in the base-class, so we don't
            # have to copy-paste it into every single view. This means that
            # someone could invoke it in the abstract base, which does not make
            # any sense, so we have to catch it
            raise Exception("Factory must be called on a specific "
                            "PapiViewClient subclass")
        return cls(base_client, logger)

    @classmethod
    def view_with_client_from_config(cls, conf, config_section, logger=None):
        """
        Factory method for constructing a new base-client plus the corresponding
        view; Typically used in combination with pools

        :param conf: ConfigParser object holding client configuration
        :param config_section: Name of the section holding client configuration
        :param logger: Logger object to pass to view (optional)
        """
        if cls == PapiViewClient:
            # we're implementing this factory in the base-class, so we don't
            # have to copy-paste it into every single view. This means that
            # someone could invoke it in the abstract base, which does not make
            # any sense, so we have to catch it
            raise Exception("Factory must be called on a specific "
                            "PapiViewClient subclass")

        base_client = papi_client.papi_client.PapiClientFactory.\
            client_from_config(conf, config_section, logger)
        return cls.client_from_config(base_client, conf, logger)

    def __init__(self, view_name, base_client, logger=None, description=None):
        self._name = view_name
        self._client = base_client
        self._logger = logger
        self._description = description

    def name(self):
        return self._name
    
    def module_name(self):
        """
        This is the path to this view on the API server.
        
        By default, it is the same as name().
        """
        return self.name()
    
    def description(self):
        if self._description:
            return self._description
        return self.name() + " API"
    
    def _get(self, function, params=None, fmt="JSON", raw=False):
        return self._client.do_request(
            method="GET",
            module=self.module_name(),
            function=function,
            params=params,
            fmt=fmt,
            raw=raw)
    
    def _post(self, function, params=None, data=None, files=None, fmt="JSON", raw=False):
        return self._client.do_request(
            method="POST",
            module=self.module_name(),
            function=function,
            params=params,
            data=data,
            files=files,
            fmt=fmt,
            raw=raw)
    
    @staticmethod
    def _get_key_params(key):
        return papi_client.papi_client.PapiClient._get_key_params(key)


class PapiViewLoader(object):

    @staticmethod
    def get_view_class_from_name(name):
        module_name = "papi_client.api.%s" % name
        try:
            module = import_module(module_name)
        except ImportError:
            raise NoSuchView(name)
        return PapiViewLoader.get_view_class_from_module(module)

    @staticmethod
    def get_view_class_from_module(module):
        for name in dir(module):
            obj = getattr(module, name)
            if inspect.isclass(obj):
                if issubclass(obj, PapiViewClient):
                    return obj
    
        raise NoSuchView(module.__name__)
    
    @staticmethod
    def get_view_from_module(module, base_client, conf, logger=None):
        view_class = PapiViewLoader.get_view_class_from_module(module)
        return view_class.client_from_config(base_client=base_client,
                                             conf=conf,
                                             logger=logger)
    
    @staticmethod
    def get_view_from_name(name, base_client, conf, logger=None):
        view_class = PapiViewLoader.get_view_class_from_name(name)
        return view_class.client_from_config(base_client=base_client,
                                             conf=conf,
                                             logger=logger)


class PapiClientCollection(object):
    """
    Collection of PapiViewClient objects
    """
    def __init__(self, base_client, conf, logger=None):
        self._client = base_client
        self._conf = conf
        self._logger = logger
        self._views = {}
    
    def base_client(self):
        """
        Get a base client for sending generic
        API requests to the PAPI.
        """
        return self._client
    
    def view(self, name):
        """
        Get a client for a specific API view.
        
        Invoke list_views() to get a list of
        available views.
        """
        try:
            return self._views[name]
        except KeyError:
            raise NoSuchView(name)

    def list_views(self):
        return sorted(self._views.keys())

    def load_view(self, name):
        if name in self._views:
            raise DuplicateView(name)

        view = PapiViewLoader.get_view_from_name(
            name=name,
            base_client=self._client,
            conf=self._conf,
            logger=self._logger)
        
        self.add_view(name, view)
    
    def add_view(self, name, view):
        if name != view.name():
            msg = "%s: view.name() returns '%s'" % (name, view.name())
            raise UnexpectedView(msg)
        
        self._views[name] = view
        
        #try to also add it as an attribute to 
        #this object with the view's name.
        if hasattr(self, name):
            self._logger.warning("PapiClientCollection already has %s attribute: view will be accessible through views() method")
        else:
            setattr(self, name, view)

    def load_all_views(self):
        info = [i for i in pkgutil.iter_modules(papi_client.api.__path__)]
        # i[2] is is_pkg, i[1] is the name
        names = [i[1] for i in info if not i[2]]
        for name in names:
            try:
                self.load_view(name)
                self._logger.info("Loaded view '%s'", name)
            except NoSuchView as e:
                self._logger.warning("%s", e)
