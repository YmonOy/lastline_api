"""
PAPI client view for talking to the Appliance Management API

:Copyright:
     Copyright 2014 Lastline, Inc.  All Rights Reserved.
"""
from papi_client import loader
from papi_client import papi_client


class PapiClientApplianceMgmt(loader.PapiViewClient):
    """
    Client to acccess the Lastline Appliance Management API

    Detailed documentation can be found at the following URL::

        https://user.lastline.com/papi-doc/api/html/appliance_mgmt/overview.html

    API methods on this client take a "raw" parameter.

     - If raw is set to True, the client will return the raw server response
       (that is, the HTTP body) so long as the HTTP request is successful.
       If the HTTP request fails a `papi_client.papi_client.CommunicationError`
       is raised
     - If raw is set to False, the client will try to parse the json response
       and return the data field of the response. If the API response is an
       error, a `papi_client.papi_client.ApiError` is raised.

    :param base_client: This is the client that actually sends requests
        to the API server.
    :type base_client: `papi_client.papi_client.PapiClient`
    :param logger: python logger to which we will log
    """
    def __init__(self, base_client, logger=None):
        loader.PapiViewClient.__init__(self, "appliance_mgmt", base_client,
                                       logger=logger,
                                       description="Appliance Management API")

    def ping(self, raw=False):
        """
        Ping this API to verify it is supported by the server.
        """
        return self._get("ping", raw=raw)

    def get_overview(self, user_id=None, raw=False):
        """
        """
        params = {}
        if user_id is not None:
            params["user_id"] = int(user_id)

        return self._get("overview", params=params, raw=raw)

    def get_configuration(self, appliance_uuid, user_id=None, raw=False):
        """
        Get the current configuration of an appliance.

        :param appliance_uuid: Unique identifier of the appliance as received by
            `get_overview()`.
        """
        params = {"appliance_uuid": appliance_uuid}
        if user_id is not None:
            params["user_id"] = int(user_id)

        return self._get("configuration", params=params, raw=raw)

    def _do_action(self, appliance_uuid, action_type, action_parameters=None,
                   user_id=None, raw=False):
        """
        Execute an action on an appliance.

        :param appliance_uuid: Unique identifier of the appliance as received by
            `get_overview()`.
        :param action_type: The action to execute, e.g., CONFIGURE
        :param action_parameters: A dict representing parameters depending on
            the selected action.
        """
        data = {
            "appliance_uuid": appliance_uuid,
            "action_type": action_type,
        }

        if user_id is not None:
            data["user_id"] = int(user_id)

        if action_parameters is not None:
            data["action_parameters"] = papi_client.json.dumps(action_parameters)

        return self._post("action/request", data=data, raw=raw)

    def configure(self, appliance_uuid, software_version=None, auto_update=None,
                  settings=None, user_id=None, raw=False):
        """
        Configure or re-trigger a configuration on an appliance.

        See the URL above for a more extensive description of the parameters.

        :param appliance_uuid: Unique identifier of the appliance as received by
            `get_overview()`.
        :param software_version: Set the appliance to this version.
        :param auto_update: Enable or disable auto_update on this appliance.
        :param settings: Type and version specific settings to configure on
            the appliance. The current and default settings of a given
            appliance can be received using `get_configuration()`.
        """
        action_parameters = {}

        if settings:
            action_parameters["settings"] = settings

        if auto_update is not None:
            action_parameters["auto_update"] = auto_update

        if software_version:
            action_parameters["software_version"] = software_version

        return self._do_action(
            appliance_uuid=appliance_uuid,
            action_type="CONFIGURE",
            action_parameters=action_parameters,
            user_id=user_id,
            raw=raw
        )

    def get_action_status(self, action_uuid, user_id=None, raw=False):
        """
        Get the status of an action identified by its action_uuid.

        :param action_uuid: Unique identifier of the Action
        """
        params = {"action_uuid": action_uuid}
        if user_id is not None:
            params["user_id"] = int(user_id)

        return self._get("action/status", params=params, raw=raw)
