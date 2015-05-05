#!/usr/bin/python
"""
PAPI client view for talking to the postprocessing API

:Copyright:
     Copyright 2014 Lastline, Inc.  All Rights Reserved.
"""
# Use simpleson if we have it, else json

from papi_client import loader





class PapiClientPostprocessing(loader.PapiViewClient):
    """
    Client for the Lastline postprocessing API
    
    This is the API for managing custom intelligence for a Lastline installation.
    See the API documentation here: 
    https://user.lastline.com/papi-doc/api/html/intel/overview.html

    raw
    -------
    
    API methods on this client take a "raw" parameter.
    
     - If it is set to True, the client will return the raw server response 
       (that is, the HTTP body) so long as the HTTP request is successful.
       If the HTTP request fails a `papi_client.papi_client.CommunicationError` 
       is raised
     - If it is set to True, the client will try to parse the json response
       and return the data field. If the API response is an error, a
       `papi_client.papi_client.ApiError` is raised
    
    :param base_client: This is the client that actually sends requests
        to the API server.
    :type base_client: `papi_client.papi_client.PapiClient`
    :param logger: python logger to which we will log
    """
    def __init__(self, base_client, logger=None):
        loader.PapiViewClient.__init__(self, "postprocessing", base_client, logger)

    def ping(self, raw=False):
        """
        Ping this API to verify it is supported by the API server
        we are talking with.
        
        :param raw: if True, return raw JSON instead of parsed response data
        """
        return self._get("ping", raw=raw)
    
    def analysis_completed(self, uuid, score, licenses, raw=False):
        """
        An analysis task has completed
        
        This API call announces to the enterprise backend that an analysis task
        has completed or rescored, so that this information can be propagated and
        reflected in network information, notifications, etc for networks
        where this file was seen.
        
        :param uuid: uuid of the completed analysis task (required)
        :param score: score of the task: 0-100 (required)
        :param licenses: sequence of access keys (required)
        :param raw: if True, return raw JSON instead of parsed response data
        """
        #conversts sequence to list,
        #and increases determinism
        licenses=sorted(licenses)
        params = {
            "uuid":uuid,
            "score":score,
            "licenses":licenses
        }

        return self._post("analysis/completed", data=params, raw=raw)

