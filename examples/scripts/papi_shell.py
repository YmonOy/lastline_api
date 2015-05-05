#!/usr/bin/python
"""
Interactive shell for the papi client.

:Copyright:
     Copyright 2014 Lastline, Inc.  All Rights Reserved.
     Created on: Apr 1, 2014 by Paolo Milani
"""

import argparse
import ConfigParser
import os.path
import logging
import IPython

from papi_client import papi_client
from papi_client import loader

BANNER_PART1 = """
---------------------------------------------------------
Lastline PAPI shell
---------------------------------------------------------

The 'client' object is a PapiClientCollection,
which provides access to the functionality
of the individual API views.

Views currently available are:

"""

BANNER_PART2 = """

This is an IPython shell, so you can take
advantage of tab auto-completion and other
convenient features of IPython. 

E.g.:

Typing the command 'client.intel?' followed by a RETURN,
will print documentation for the intel API client,
while typing 'client.intel' followed by TAB will present
auto-completion options 
(the list of methods of the intel client).

---------------------------------------------------------
"""


def main():
    parser = argparse.ArgumentParser(usage="""
    
Interactive shell for the Lastline PAPI
-----------------------------------------

    %(prog)s -c CONFIG
    
For a sample configuration INI file, see papi_client.ini.template

""")
    parser.add_argument("-c", "--config", type=str, dest="config",
                        default="papi_client.ini",
                        help="Configuration file name")
    parser.add_argument("--section", type=str, default="papi",
                        help="Section of configuration file to read from")

    args = parser.parse_args()

    # Python logger...
    logger = logging.getLogger()
    sh = logging.StreamHandler()
    logger.setLevel(logging.DEBUG)
    sh.setLevel(logging.DEBUG)
    logger.addHandler(sh)

    config_fn = os.path.expanduser(args.config)
    if not os.path.isfile(config_fn):
        logger.error("config %s not found", args.config)
        return 1

    config_parser = ConfigParser.ConfigParser()
    config_parser.read(config_fn)

    base_client = papi_client.PapiClientFactory.client_from_config(config_parser, args.section, logger)
    client = loader.PapiClientCollection(base_client=base_client,
                                          conf=config_parser,
                                          logger=logger)
    client.load_all_views()
    views = client.list_views()
    logger.info("Loaded %s views:", len(views))
    for v in views:
        logger.info("-->%s", v)

    view_desc = [" - 'client.%s': %s" % (v, client.view(v).description()) for v in views]
    banner = BANNER_PART1 + "\n".join(view_desc) + BANNER_PART2

    # ipython interactive shell
    IPython.embed(banner1=banner)

if __name__ == "__main__":
    main()
