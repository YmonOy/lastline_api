#!/usr/bin/python
"""
Sample program to add custom intelligence from a CSV file.

:Copyright:
     Copyright 2014 Lastline, Inc.  All Rights Reserved.
     Created on: Apr 1, 2014 by Paolo Milani
"""

import argparse
import ConfigParser
import os.path
import logging
import csv
import collections
import socket

from papi_client import papi_client
from papi_client import loader
from papi_client.api import intel 


__INTEL_ENTRY_COLS = [
    "ip",
    "domain",
    "impact",
    "source",
    "comment"
]
IntelEntry = collections.namedtuple("IntelEntry", __INTEL_ENTRY_COLS)


class CSVFormat(object):
    PLACEHOLDERS = [
        "IP",
        "DOMAIN",
        "IMPACT",
        "SOURCE",
        "COMMENT",
        "IGNORE"
    ]

    def __init__(self, ip_pos, domain_pos, impact_pos, source_pos, comment_pos):
        if ip_pos is None and domain_pos is None:
            assert False, "Invalid FORMAT specifier: must include IP or DOMAIN"
        if ip_pos is not None and domain_pos is not None:
            assert False, "Invalid FORMAT specifier: cannot include both IP and DOMAIN"
            
        self._ip_pos = ip_pos
        self._domain_pos = domain_pos
        self._impact_pos = impact_pos
        self._source_pos = source_pos
        self._comment_pos = comment_pos
        self._max_pos = max([self._ip_pos,
                             self._domain_pos,
                             self._impact_pos,
                             self._source_pos,
                             self._comment_pos])
    
    def intel_type(self):
        if self._ip_pos is not None:
            return "IP"
        if self._domain_pos is not None:
            return "DOMAIN"
        assert False
            

    @staticmethod
    def from_format_string(format_string):
        parts = format_string.split(",")
        for part in parts:
            assert part in CSVFormat.PLACEHOLDERS, "Invalid FORMAT specifier: '%s'" % part
        
        ip_pos=None
        domain_pos=None
        impact_pos=None
        source_pos=None
        comment_pos=None
        
        try:
            ip_pos = parts.index("IP")
        except ValueError:
            pass
        
        try:
            domain_pos = parts.index("DOMAIN")
        except ValueError:
            pass
        
        try:
            impact_pos = parts.index("IMPACT")
        except ValueError:
            pass
        
        try:
            source_pos = parts.index("SOURCE")
        except ValueError:
            pass
        
        try:
            comment_pos = parts.index("COMMENT")
        except ValueError:
            pass
        
        return CSVFormat(
            ip_pos=ip_pos,
            domain_pos=domain_pos,
            impact_pos=impact_pos,
            source_pos=source_pos,
            comment_pos=comment_pos
        )
    
    @staticmethod
    def parse_impact(impact):
        try:
            impact = int(impact)
        except ValueError:
            return None
        
        if impact < 1 or impact > 100:
            return None
        
        return impact
    
    @staticmethod
    def parse_ip(ip):
        try:
            socket.inet_pton(socket.AF_INET, ip)
        except socket.error:
            return None
        return ip
    
    def parse_line(self, csv_line, line_num, logger=None):
        values = {
            "ip": None,
            "domain": None,
            "impact": None,
            "source": None,
            "comment": None
        }
        
        if self._ip_pos is not None:
            values["ip"] = self.parse_ip(csv_line[self._ip_pos])
            if not values["ip"]:
                if logger:
                    logger.error("Invalid line %s: invalid IP '%s'",
                                 line_num,
                                 csv_line[self._ip_pos])
                return None
        
        if self._domain_pos is not None:
            values["domain"] = csv_line[self._domain_pos]
        
        if self._impact_pos is not None:
            values["impact"] = self.parse_impact(csv_line[self._impact_pos])
            if not values["impact"]:
                if logger:
                    logger.error("Invalid line %s: invalid impact '%s'",
                                 line_num,
                                 csv_line[self._impact_pos])
        
        if self._source_pos is not None:
            values["source"] = csv_line[self._source_pos]
        
        if self._comment_pos is not None:
            values["comment"] = csv_line[self._comment_pos]
        
        return IntelEntry(**values)

    def parse_csv(self, csv_file, skip=0, logger=None):
        reader = csv.reader(csv_file)
        line_num = 0
        for line in reader:
            # line number is 1-indexed, as is more common in editors
            line_num += 1
            if line_num <= skip:
                continue
            if not line:
                logger.warning("Skipping empty line %s", line_num)
                continue
            
            if self._max_pos >= len(line):
                if logger:
                    logger.error("Invalid line %s: not enough csv parts", line_num)
                continue
            entry = self.parse_line(line, line_num, logger)
            yield entry


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str, dest="config",
                        default="papi_client.ini")
    parser.add_argument("input_file", help="Input CSV file", metavar="INPUT.CSV")
    parser.add_argument("format_string", metavar="FORMAT",
                        help="Format of CSV file. This is a comma-separated list"
                        " that can contain the following strings: "
                        "IP, DOMAIN, IMPACT, SOURCE, COMMENT, IGNORE. "
                        "This determines what to do with the first "
                        "comma-separated parameters of each line. "
                        "Exactly one IP or DOMAIN string must be specified, "
                        "and this determines whether we are blacklisting IPs "
                        "or domains. The IGNORE field is used to skip "
                        "CSV fields that are not needed by the Lastline "
                        "intel API. An example string could be: " 
                        "'IP,IMPACT,SOURCE,COMMENT'")
    parser.add_argument("key", nargs="?", default=None,
                        help="Add entries at the scope of this license "
                        "key[:subkey]. If not provided, add at global scope")
    parser.add_argument("--impact", type=int,
                        help="set this impact for all added entries. "
                        "This is in alternative to including an IMPACT " 
                        "field in the FORMAT")
    parser.add_argument("--source",
                        help="set this source for all added entries. "
                        "This is in alternative to including a SOURCE " 
                        "field in the FORMAT")
    parser.add_argument("--comment",
                        help="set this comment for all added entries. "
                        "This is in alternative to including a COMMENT " 
                        "field in the FORMAT")
    parser.add_argument("--skip-header", type=int, default=0,
                        help="Skip this many lines at start of file")
    parser.add_argument("--limit", type=int,
                        help="Add at most this many entries (mostly for testing)")
    parser.add_argument("--test", default=False, action="store_true",
                        help="Don't actually run the add, just print out "
                        "the entries that would be added")

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
    
    csv_format = CSVFormat.from_format_string(args.format_string)
    
    if args.impact:
        if not CSVFormat.parse_impact(args.impact):
            logger.error("Invalid impact %s", args.impact)
            exit(1)
    
    entries = [e for e in csv_format.parse_csv(open(args.input_file),
                                               skip=args.skip_header,
                                               logger=logger)]
    
    if args.impact:
        entries = map(lambda e:e._replace(impact=args.impact), entries)
    
    if args.source:
        entries = map(lambda e:e._replace(source=args.source), entries)
    
    if args.comment:
        entries = map(lambda e:e._replace(comment=args.comment), entries)
    
    logger.info("Parsed %s feed entries", len(entries))
    
    if args.limit:
        entries = entries[:args.limit]
    
    

    # if we pass the namedtuples through,
    # simplejson serializes them correctly (like dictionaries)
    # but plain json does not
    entries = [dict(e._asdict()) for e in entries]
    # remove anything we're not setting
    for e in entries:
        intel.purge_none(e)

    print entries[:10]

    base_client = papi_client.PapiClientFactory.client_from_config(config_parser, "papi", logger)
    client = loader.PapiClientCollection(base_client=base_client,
                                          conf=config_parser,
                                          logger=logger)
    client.load_view("intel")
    intel_type = csv_format.intel_type()
    
    
    
    logger.info("Adding %s %s entries through intelligence API for key '%s'",
                len(entries),
                intel_type,
                args.key)
    
    if args.test:
        logger.info("STOP: we are in test mode")
    else:
        if intel_type == "IP":
            result = client.intel.add_ip(entries, args.key)  # pylint: disable=E1101
        elif intel_type == "DOMAIN":
            result = client.intel.add_domain(entries, args.key)  # pylint: disable=E1101
        
        print result
    
    
    
if __name__ == "__main__":
    main()
