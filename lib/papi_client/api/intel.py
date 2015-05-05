#!/usr/bin/python
"""
PAPI client view for talking to the intel API

:Copyright:
     Copyright 2014 Lastline, Inc.  All Rights Reserved.
"""
# Use simpleson if we have it, else json
try:
    import simplejson as json
except ImportError:
    import json


from papi_client import loader


def purge_none(d):
    """
    Purge None entries from a dictionary
    """
    for k in d.keys():
        if d[k] is None:
            del d[k]
    return d



class PapiClientIntel(loader.PapiViewClient):
    """
    Client for the Lastline intelligence API
    
    This is the API for managing custom intelligence for a Lastline installation.
    See the API documentation here: 
    https://user.lastline.com/papi-doc/api/html/intel/overview.html
    
    Scope
    -------
    
    The intelligence API allows to configure intelligence at differnt
    scopes. This can be 
    
     - sensor scope: limited to a specific sensor
     - license scope: limited to all appliances under a license
     - global scope: global, for all appliances of a customer

    See the API documentation for more information on scopes. 
    Methods in this API client take a key parameter that is used to 
    determine the scope at which we are operating. This can be one of the 
    following:
    
     - None: to operate at global scope
     - a license string: to operate at license scope
     - a license:subkey: to operate at sensor scope
     - a papi_client.KeyIds object: to operate at license or sensor scope
         based on a key_id and optionally subkey_id
    
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
        description = "Custom intelligence API"
        loader.PapiViewClient.__init__(self, "intel", base_client, logger,
                                       description=description)
    
    def ping(self, raw=False):
        """
        Ping this API to verify it is supported by the API server
        we are talking with.
        
        :param raw: if True, return raw JSON instead of parsed response data
        """
        return self._get("ip/ping", raw=raw)
    
    def list_ip(self, key=None, source=None, raw=False):
        """
        List IP addresses in custom blacklist at a specific scope
        
        :param key: Determines the scope at which we are listing the IPs.
            Will only return IPs that are blacklisted exactly at this scope.
        :param source: only list entries from this source
        :param raw: if True, return raw JSON instead of parsed response data
        """
        params = {}
        if source:
            params["source"] = source
        if key:
            params.update(self._get_key_params(key))
        return self._get("ip/list", params=params, raw=raw)
    
    def get_ip(self, ip, key=None, inherit_scope=False, raw=False):
        """
        Get an entry in custom blacklist at a specific scope
        
        :param ip: get blacklist entry for this ip
        :param key: Determines the scope at which we are getting the domain.
            Will only return domains that are blacklisted exactly at this scope.
        :param inherit_scope: if set, also consider parents scope 
            when looking for rule
        :param raw: if True, return raw JSON instead of parsed response data
        """
        params = {
            "ip":ip,
            "inherit_scope":inherit_scope
        }
        if key:
            params.update(self._get_key_params(key))
        return self._get("ip/get", params=params, raw=raw)
    
    def feed_ip(self, key=None, current_version=None, raw=False):
        """
        Get the IP blacklist feed at a specified scope.
        
        :param key: Determines the scope at which we are fetching the feed.
            Will include IPs that are blacklisted at this scope
            and all applicable scopes.
        :param current_version: version of the feed you already have,
            as returned by this method. Using this parameter may lead to an empty
            response (if there are no changes) or an incremental response
            describing ips to add and remove from the previous feed version.
        :param raw: if True, return raw JSON instead of parsed response data
        """
        params = {}
        if current_version:
            params["current_version"] = current_version
        if key:
            params.update(self._get_key_params(key))
        return self._get("ip/feed", params=params, raw=raw)
    
    def add_ip(self, entries, key=None, raw=False):
        """
        Add to the IP blacklist at a specified scope
        
        :param entries: sequence of entry dictionaries
        :param key: Determines the scope at which we are adding the IPs
        :param raw: if True, return raw JSON instead of parsed response data
        
        Each dictionary in entries has the following fields:
        
        **ip**:
            The IP address. An IPv4 address in dotted-decimal notation. (required)
        **source**:
            Use this field to store the source of this information, such as the
            name of the watchlist or blacklist that this entry comes from 
            (up to 45 ASCII characters).
        **comment**:
            Free text comment field for 
            (up to 255 characters)
        **impact**:
            Impact level of events generated by this entry. 
            This can be 10-100 in increments of 10.
        """
        entries_str = json.dumps(entries)
        params = {"entries":entries_str}
        if key:
            params.update(self._get_key_params(key))

        return self._post("ip/add", data=params, raw=raw)
    
    def delete_ip(self, ips, key=None, raw=False):
        """
        Remove an IP from the custom blacklist at a specified scope
        
        :param ips: sequence of IPv4 addresses in dotted-decimal notation (required)
        :param key: Determines the scope at which we are adding the IPs
        :param raw: if True, return raw JSON instead of parsed response data
        """
        ips_str = ",".join(ips)
        
        params = {"ips":ips_str}
        if key:
            params.update(self._get_key_params(key))

        return self._post("ip/del", data=params, raw=raw)
    
    def list_domain(self, key=None, source=None, raw=False):
        """
        List domain names in custom blacklist at a specific scope
        
        :param key: Determines the scope at which we are listing the domains.
            Will only return domains that are blacklisted exactly at this scope.
        :param source: only list entries from this source
        :param raw: if True, return raw JSON instead of parsed response data
        """
        params = {}
        if source:
            params["source"] = source
        if key:
            params.update(self._get_key_params(key))
        return self._get("domain/list", params=params, raw=raw)
    
    def get_domain(self, domain, key=None, inherit_scope=False, raw=False):
        """
        Get an entry in custom blacklist at a specific scope
        
        :param domain: get blacklist entry for this domain
        :param key: Determines the scope at which we are getting the domain.
            Will only return domains that are blacklisted exactly at this scope.
        :param inherit_scope: if set, also consider parents scope 
            when looking for rule
        :param raw: if True, return raw JSON instead of parsed response data
        """
        params = {
            "domain":domain,
            "inherit_scope":inherit_scope
        }
        if key:
            params.update(self._get_key_params(key))
        return self._get("domain/get", params=params, raw=raw)
    
    def feed_domain(self, key=None, current_version=None, raw=False):
        """
        Get the IP blacklist feed at a specified scope.
        
        :param key: Determines the scope at which we are fetching the feed.
            Will include IPs that are blacklisted at this scope
            and all applicable scopes.
        :param current_version: version of the feed you already have,
            as returned by this method. Using this parameter may lead to an empty
            response (if there are no changes) or an incremental response
            describing ips to add and remove from the previous feed version.
        :param raw: if True, return raw JSON instead of parsed response data
        """
        params = {}
        if current_version:
            params["current_version"] = current_version
        if key:
            params.update(self._get_key_params(key))
        return self._get("domain/feed", params=params, raw=raw)
    
    def add_domain(self, entries, key=None, raw=False):
        """
        Add to the IP blacklist at a specified scope
        
        :param entries: sequence of entry dictionaries
        :param key: Determines the scope at which we are adding the IPs
        :param raw: if True, return raw JSON instead of parsed response data
        
        Each dictionary in entries has the following fields:
        
        **domain**:
            The domain. This is a fully-qualified domain name in ASCII (required)
        **source**:
            Use this field to store the source of this information, such as the
            name of the watchlist or blacklist that this entry comes from 
            (up to 45 ASCII characters).
        **comment**:
            Free text comment field for 
            (up to 255 characters)
        **impact**:
            Impact level of events generated by this entry. 
            This can be 10-100 in increments of 10.
        """
        entries_str = json.dumps(entries)
        print "THE ENTRIES" 
        print entries_str
        params = {"entries":entries_str}
        if key:
            params.update(self._get_key_params(key))

        return self._post("domain/add", data=params, raw=raw)
    
    def delete_domain(self, domains, key=None, raw=False):
        """
        Remove an IP from the custom blacklist at a specified scope
        
        :param domains: sequence of fully-qualified domain name in ASCII (required)
        :param key: Determines the scope at which we are adding the IPs
        :param raw: if True, return raw JSON instead of parsed response data
        """
        domains_str = ",".join(domains)
        
        params = {"domains":domains_str}
        if key:
            params.update(self._get_key_params(key))

        return self._post("domain/del", data=params, raw=raw)
    
    def list_ids_rule(self, key=None, source=None, raw=False):
        """
        List custom ids rules at a specific scope
        
        :param key: Determines the scope at which we are listing the rules.
            Will only return rules that are defined exactly at this scope.
        :param source: only list entries from this source
        :param raw: if True, return raw JSON instead of parsed response data
        """
        params = {}
        if source:
            params["source"] = source
        if key:
            params.update(self._get_key_params(key))
        return self._get("ids_rule/list", params=params, raw=raw)
    
    
    def get_ids_rule(self, rule_id=None, group_id=None, key=None, signature_id=None, inherit_scope=False, raw=False):
        """
        Get a custom IDS rule at a specific scope
        
        :param rule_id: rule identifier to get (sid)
        :param group_id: group identifier to get (gid)
        :param key: Determines the scope at which we are getting the entry.
             Will only return entries exactly at this scope.
        :param signature_id: lastline identifier of signature: provide
            in alternative to customer sid/gid
        :param inherit_scope: if set, also consider parents scope 
            when looking for rule
        :param raw: if True, return raw JSON instead of parsed response data
        """
        params = {
            "rule_id":rule_id,
            "group_id":group_id,
            "signature_id":signature_id,
            "inherit_scope":inherit_scope,
        }
        params = purge_none(params)
        if key:
            params.update(self._get_key_params(key))
        return self._get("ids_rule/get", params=params, raw=raw)
    
    def feed_ids_rule(self, key=None, current_version=None, raw=False):
        """
        Get the custom ids rules feed at a specified scope.
        
        :param key: Determines the scope at which we are fetching the feed.
            Will include rules defined at this scope
            and all applicable scopes.
        :param current_version: version of the feed you already have,
            as returned by this method. Using this parameter may lead to an empty
            response (if there are no changes) or an incremental response
            describing ips to add and remove from the previous feed version.
        :param raw: if True, return raw JSON instead of parsed response data
        """
        params = {}
        if current_version:
            params["current_version"] = current_version
        if key:
            params.update(self._get_key_params(key))
        return self._get("ids_rule/feed", params=params, raw=raw)
    
    def add_ids_rule(self, entries, key=None, raw=False):
        """
        Add a custom ids rule at a specified scope
        
        :param entries: sequence of entry dictionaries
        :param key: Determines the scope at which we are adding the rules
        :param raw: if True, return raw JSON instead of parsed response data
        
        Each dictionary in entries has the following fields:
        
        **rule**:
            The IDS rule to add (required)
        **source**:
            Use this field to store the source of this information, such as the
            name of the watchlist or blacklist that this entry comes from 
            (up to 45 ASCII characters).
        **impact**:
            Impact level of events generated by this entry. 
            This can be 10-100 in increments of 10. (required)
        """
        entries_str = json.dumps(entries)
        params = {"entries":entries_str}
        if key:
            params.update(self._get_key_params(key))

        return self._post("ids_rule/add", data=params, raw=raw)
    
    def delete_ids_rule(self, rules, key=None, raw=False):
        """
        Remove an ids rule from the custom blacklist at a specified scope
        
        :param rules: list of dictionaries holding 
            a required rule_id and optional group_id (defaults to 0)
            of the rules to delete (required)
        :param key: Determines the scope at which we are adding the rules
        :param raw: if True, return raw JSON instead of parsed response data
        """
        rules_str = json.dumps(rules)
        
        params = {"rules":rules_str}
        if key:
            params.update(self._get_key_params(key))

        return self._post("ids_rule/del", data=params, raw=raw)
    
    def list_ids_rule_variable(self, key=None, raw=False):
        """
        List variables for custom ids rules at a specific scope
        
        :param key: Determines the scope at which we are listing the variables.
            Will only return variables that are defined at this scope.
        :param source: only list entries from this source
        :param raw: if True, return raw JSON instead of parsed response data
        """
        params = {}
        if key:
            params.update(self._get_key_params(key))
        return self._get("ids_rule_variable/list", params=params, raw=raw)
    
    def get_ids_rule_variable(self, rule_id, group_id=None, key=None, inherit_scope=False, raw=False):
        """
        Get a custom IDS rule variable at a specific scope
        
        :param rule_id: rule identifier to get (sid)
        :param group_id: group identifier to get (gid)
        :param key: Determines the scope at which we are getting the entry.
             Will only return entries exactly at this scope.
        :param inherit_scope: if set, also consider parents scope 
            when looking for rule
        :param raw: if True, return raw JSON instead of parsed response data
        """
        params = {
            "rule_id":rule_id,
            "inherit_scope":inherit_scope
        }
        if group_id:
            params["group_id"] = group_id
        if key:
            params.update(self._get_key_params(key))
        return self._get("ids_rule_variable/get", params=params, raw=raw)
    
    def feed_ids_rule_variable(self, key=None, current_version=None, raw=False):
        """
        Get the custom ids rule variables feed at a specified scope.
        
        :param key: Determines the scope at which we are fetching the feed.
            Will include variables defined at this scope
            and all applicable scopes.
        :param current_version: version of the feed you already have,
            as returned by this method. Using this parameter may lead to an empty
            response (if there are no changes) or an incremental response
            describing ips to add and remove from the previous feed version.
        :param raw: if True, return raw JSON instead of parsed response data
        """
        params = {}
        if current_version:
            params["current_version"] = current_version
        if key:
            params.update(self._get_key_params(key))
        return self._get("ids_rule_variable/feed", params=params, raw=raw)
    
    def add_ids_rule_variable(self, entries, key=None, raw=False):
        """
        Add a custom ids rule variable at a specified scope
        
        :param entries: sequence of entry dictionaries
        :param key: Determines the scope at which we are adding the rules
        :param raw: if True, return raw JSON instead of parsed response data
        
        Each dictionary in entries has the following fields:
        
        **variable_name**: 
            The variable name. Up to 32 ASCII characters (required)
        **variable_type**: 
            'ADDRESSGROUP' or 'PORTGROUP' (required)
        **value**:
            The value of the variable: Up to 4096 ASCII characters (required)
        """
        entries_str = json.dumps(entries)
        params = {"entries":entries_str}
        if key:
            params.update(self._get_key_params(key))

        return self._post("ids_rule_variable/add", data=params, raw=raw)
    
    def delete_ids_rule_variable(self, variable_names, key=None, raw=False):
        """
        Remove an ids rule variable from the custom blacklist at a specified scope
        
        :param variable_names: The variables to delete.
            Sequence of variable names(required)
        :param key: Determines the scope at which we are adding the rules
        :param raw: if True, return raw JSON instead of parsed response data
        """
        names_str = ",".join(variable_names)
        
        params = {"variable_names":names_str}
        if key:
            params.update(self._get_key_params(key))

        return self._post("ids_rule_variable/del", data=params, raw=raw)

