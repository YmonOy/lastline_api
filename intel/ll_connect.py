from django.conf import settings

import sys
import os.path
import ConfigParser

from papi_client import papi_client
from papi_client import loader

# Session re-use
import dill as pickle
import requests, requests.utils
from intel.models import APISession

from ll_logger import LogExceptions
from ll_debug import __debugvar__


# TODO: Handle Permission Denied errors if our provided account has no rights.

class APIConn:
  def __init__(self, logger):
    self.logger = logger

  @LogExceptions()
  def load_config(self):
    __config_fn = settings.PAPI_CLIENTCONF 
    if not os.path.isfile(__config_fn):
      errors = 'Config file({0}) not found'.format(settings.PAPI_CLIENTCONF)
      self.logger.error(self.logger.to_internal(self, errors))
      sys.exit(errors)

    self.__config_parser = ConfigParser.ConfigParser()
    self.__config_parser.read(__config_fn)
    return self.__config_parser
 
  @LogExceptions()
  def connect_api(self, __config_parser):
    # Create base client object from config
    __base_client = papi_client.PapiClientFactory.client_from_config(
      __config_parser,
      'papi',
      logger=self.logger.instance
    )
    self.client = loader.PapiClientCollection(
      base_client=__base_client,
      conf=__config_parser,
      logger=self.logger.instance
    )

    # Load old session (Auth cookies) - Looked up by login URI from db
    # Alternatively: session = self.client._client._PapiClient__url
    self.login_uri = __config_parser.get('papi', 'url')
    try:
      __session = APISession.objects.get(login_uri=self.login_uri)
    except APISession.DoesNotExist:
      self.client._client._PapiClient__session = None
      self.cookie = None
    except: raise
    else:
      self.client._client._PapiClient__session = pickle.loads(__session.serialized) 
      self.cookie = self.client._client._PapiClient__session.cookies['PHPSESSID']

    return self.client

  # Check if authorization cookie has changed between queries
  def check_auth(self):
    # Cookie received from Lastline
    __current_cookie = self.client._client._PapiClient__session.cookies['PHPSESSID']
    if(self.cookie != __current_cookie):
      # Store changed cookie in DB
      __sessionDB = APISession(
          login_uri=self.login_uri,
          serialized=pickle.dumps(self.client._client._PapiClient__session)
      )
      __sessionDB.save()
      self.cookie = __current_cookie
      return False
    return True

  # Wrapped API calls 
  @LogExceptions()
  def ll_list_ip(self):
    response = self.client.intel.list_ip()
    self.check_auth() # Update stored auth if changed
    return response

  @LogExceptions()
  def ll_add_ip(self, entries):
    response = self.client.intel.add_ip(entries)
    self.check_auth()
    return response

  @LogExceptions()
  def ll_delete_ip(self, entries):
    response = self.client.intel.delete_ip(entries)
    self.check_auth()
    return response

  @LogExceptions()
  def ll_list_domain(self):
    response = self.client.intel.list_domain()
    self.check_auth()
    return response

  @LogExceptions()
  def ll_add_domain(self, entries):
    response = self.client.intel.add_domain(entries)
    self.check_auth()
    return response

  @LogExceptions()
  def ll_delete_domain(self, entries):
    response = self.client.intel.delete_domain(entries)
    self.check_auth()
    return response
