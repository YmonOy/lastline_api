#!/usr/bin/python
"""
Sample program to add SSO options to a Manager/Pinbox.

:Copyright:
         Copyright 2014 Lastline, Inc.  All Rights Reserved.
         Created on: Dec 8, 2014 by Lukyan Hritsko
"""

import requests
import argparse
import ConfigParser
import os.path
import logging
import re
from lxml import etree
from json import dumps
from urlparse import urlparse

from papi_client import papi_client
from papi_client import loader


class MissingValue(Exception):
    pass


class InvalidXML(Exception):
    pass


class InvalidFile(Exception):
    pass


class InvalidURL(Exception):
    pass


class MetadataExtractor(object):
    XPATHS = {
        'entity_descriptor': '/md:EntityDescriptor',
        'idp_sso_descriptor': '/md:EntityDescriptor/md:IDPSSODescriptor'
    }

    NAMESPACES = {
        'md': 'urn:oasis:names:tc:SAML:2.0:metadata',
        'ds': 'http://www.w3.org/2000/09/xmldsig#'
    }

    def __init__(self, xml):
        self.entity_id = None
        self.x509_cert = None
        self.sso_service_url = None
        self.idp_binding = None
        self.name_id_format = None
        self.parse_values(xml)

    def get_values_as_dict(self):
        return {
            'entity_id': self.entity_id,
            'x509_cert': self.x509_cert,
            'sso_service_url': self.sso_service_url,
            'idp_binding': self.idp_binding,
            'name_id_format': self.name_id_format,
        }

    def parse_entity_id(self, xml_root):
        try:
            entity_descriptor = xml_root.xpath(MetadataExtractor.XPATHS['entity_descriptor'],
                                               namespaces=MetadataExtractor.NAMESPACES)[0]
            self.entity_id = entity_descriptor.attrib['entityID']
        except (KeyError, IndexError):
            raise MissingValue("Unable to parse entityID")

    def parse_x509_cert(self, key_desc_node):
        xpath_from_node = 'ds:KeyInfo/ds:X509Data/ds:X509Certificate'
        try:
            x509_node = key_desc_node.xpath(xpath_from_node,
                                            namespaces=MetadataExtractor.NAMESPACES)[0]
            self.x509_cert = x509_node.text
            if not self.x509_cert:
                raise MissingValue
        except (IndexError, MissingValue):
            raise MissingValue("Unable to parse x509 certificate")

    def parse_idp_binding_and_location(self, sso_node):
        try:
            attributes = sso_node.attrib
            self.sso_service_url = attributes['Location']
            self.idp_binding = attributes['Binding']
        except (KeyError) as e:
            raise MissingValue("Unable to parse %s", e.message)

    def parse_name_id_format(self, name_id_node):
        self.name_id_format = name_id_node.text
        if not self.name_id_format:
            raise MissingValue("Unable to parse name id format")

    def extract_tag(self, raw_tag):
        return raw_tag[raw_tag.find('}') + 1:]

    def get_parser_dispatcher(self):
        return {
            'KeyDescriptor': self.parse_x509_cert,
            'NameIDFormat': self.parse_name_id_format,
            'SingleSignOnService': self.parse_idp_binding_and_location
        }

    def parse_values(self, xml):
        try:
            root = etree.fromstring(xml)
        except (Exception) as e:
            raise InvalidXML("Unable to load XML: %s" % e.message)

        parser_dispatcher = self.get_parser_dispatcher()
        self.parse_entity_id(root)

        try:
            idp_sso_desc = root.xpath(MetadataExtractor.XPATHS['idp_sso_descriptor'],
                                      namespaces=MetadataExtractor.NAMESPACES)[0]
        except (IndexError) as e:
            raise InvalidXML("Unable to parse IdP SSO Descriptor Node")

        for node in idp_sso_desc.getchildren():
            tag = self.extract_tag(node.tag)
            parser = parser_dispatcher[tag]
            parser(node)


def xml_read_from_file(file_name):
    xml_fn = os.path.expanduser(file_name)
    if not os.path.isfile(xml_fn):
        raise InvalidFile("Specified file: '%s' not found" % xml_fn)

    with open(xml_fn, 'r') as fp:
        return fp.read()


def xml_read_from_url(url, skip_validation=False):
    try:
        req = requests.get(url, verify=(not skip_validation))
        req.raise_for_status()

        if not req.content:
            raise Exception
    except Exception:
        raise InvalidURL("Unable to extract metadata from URL")

    return req.content


def get_config_parser(file_name):
    config_fn = os.path.expanduser(file_name)
    if not os.path.isfile(config_fn):
        raise InvalidFile("Specified config file: '%s' not found" % config_fn)

    config_parser = ConfigParser.ConfigParser()
    config_parser.read(config_fn)

    return config_parser


def get_logger():
    # Python logger...
    logger = logging.getLogger()
    sh = logging.StreamHandler()
    logger.setLevel(logging.DEBUG)
    sh.setLevel(logging.DEBUG)
    logger.addHandler(sh)
    return logger


def get_papi_client(config_parser, logger):
    base_client = papi_client.PapiClientFactory.client_from_config(
        config_parser,
        'papi',
        logger)
    client = loader.PapiClientCollection(base_client=base_client,
                                         conf=config_parser,
                                         logger=logger)
    client.load_view("appliance_mgmt")
    return client


class SAMLApplianceConfiguration(object):

    def __init__(
            self, appliance_uuid, config_index, metadata=None, display_name=None):
        self._appliance_uuid = appliance_uuid
        self._config_index = config_index
        self._metadata = metadata
        self._display_name = display_name

    def _get_config_settings(self, is_add=True):
        sso_config_key = "sso_saml2_config%d" % self._config_index
        sso_enabled_key = "sso_saml2_enabled%d" % self._config_index
        if is_add:
            sso_config_settings = self._metadata.get_values_as_dict()
            sso_config_settings['display_name'] = self._display_name
        else:
            sso_config_settings = {}

        return {
            sso_enabled_key: is_add,
            sso_config_key: dumps(sso_config_settings)
        }

    def add_sso(self, client):
        settings = self._get_config_settings()
        client.appliance_mgmt.configure(
            self._appliance_uuid,
            settings=settings)

    def delete_sso(self, client):
        settings = self._get_config_settings(is_add=False)
        client.appliance_mgmt.configure(
            self._appliance_uuid,
            settings=settings)


def url_or_file(string):
    if re.match(r'https?://', string, re.IGNORECASE):
        return {'url': string}
    else:
        return {'file': string}


def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="mode",
                                       help="Add or delete a config")
    # Parser for add mode
    add_parser = subparsers.add_parser('add')
    add_parser.add_argument("appliance_uuid",
                            type=str,
                            help="Specify the appliance UUID to configure.")
    add_parser.add_argument("url_or_file",
                            type=url_or_file,
                            help="Specify file location of metadata or specify "
                                 "a url to automatically parse information.")
    add_parser.add_argument("display_name",
                            nargs="?",
                            default=None,
                            help="Specify a namne that will be displayed in "
                            "the UI.")
    add_parser.add_argument("-n",
                            "--index",
                            type=int,
                            dest="config_index",
                            default=0,
                            choices=xrange(0, 4),
                            help="Specify configuration index for single "
                                 "sign on.  This is used when configuring "
                                 "multiple SSO options, i.e., first config "
                                 "is 0, second is 1, and so on...")
    add_parser.add_argument("--skip-verify-ssl",
                            default=False,
                            action="store_true",
                            help="Skips validation of SSL when retrieving "
                            "metadata from a URL")
    add_parser.add_argument("-c",
                            "--config",
                            type=str,
                            dest="config",
                            default="papi_client.ini")
    # Parser for delete mode
    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("appliance_uuid",
                               type=str,
                               help="Specify the appliance UUID to configure.")
    delete_parser.add_argument("config_index",
                               type=int,
                               choices=xrange(0, 4),
                               help="Specify which configuration to remove.")
    delete_parser.add_argument("-c",
                               "--config",
                               type=str,
                               dest="config",
                               default="papi_client.ini")
    args = parser.parse_args()
    logger = get_logger()

    try:
        config_parser = get_config_parser(args.config)
        client = get_papi_client(config_parser, logger)

        if args.mode == "delete":
            saml_configuration = SAMLApplianceConfiguration(
                args.appliance_uuid, args.config_index)
            saml_configuration.delete_sso(client)
            return 0

        if args.url_or_file.get('url', None):
            xml_content = xml_read_from_url(args.url_or_file['url'],
                                            args.skip_verify_ssl)
        else:
            xml_content = xml_read_from_file(args.url_or_file['file'])

        metadata = MetadataExtractor(xml_content)

        # If no display name exists, let's use the FQDN of the IdP
        display_name = args.display_name
        if not display_name:
            display_name = urlparse(metadata.entity_id).netloc  # pylint: disable=E1101

        logger.info("Adding SSO configuration (index %d) for appliance %s" %
                    (args.config_index, args.appliance_uuid))

        saml_configuration = SAMLApplianceConfiguration(args.appliance_uuid,
                                                        args.config_index,
                                                        metadata=metadata,
                                                        display_name=display_name)
        saml_configuration.add_sso(client)

    except (MissingValue, InvalidXML, InvalidFile, InvalidURL) as e:
        logger.error(e.message)
        return 1

    return 0

if __name__ == "__main__":
    main()
