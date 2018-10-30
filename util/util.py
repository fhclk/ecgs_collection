#!/usr/bin/env python
#-*-coding:utf-8-*-


from ConfigParser import ConfigParser, RawConfigParser
import sys

import pdb

from finalLogger import FinalLogger
log = FinalLogger.getLogger()

def readconf(conffile, section_name=None, log_name=None, defaults=None, raw=False):
    """
    Read config file and return config items as a dict

    :param conffile: path to config file, or a file-like object (hasattr
                readline)
    :param section_name: config section to read (will return all sections if
                not defined)
    :param log_name: name to be used with logging (will use section_name if
                not defined)
    :param defaults: dict of default values to pre-populate the config with
    :returns: dict of config items
    """
    if defaults is None:
        defaults = {}
    if raw:
        c = RawConfigParser(defaults)
    else:
        c = ConfigParser(defaults)
    if hasattr(conffile, 'readline'):
        c.readfp(conffile)
    else:
        if not c.read(conffile):
            print ("Unable to read config file %s") % conffile
            sys.exit(1)
    if section_name:
        if c.has_section(section_name):
            conf = dict(c.items(section_name))
        else:
            print ("Unable to find %s config section in %s") % \
                (section_name, conffile)
            sys.exit(1)
        if "log_name" not in conf:
            if log_name is not None:
                conf['log_name'] = log_name
            else:
                conf['log_name'] = section_name
    else:
        conf = {}
        for s in c.sections():
            conf.update({s: dict(c.items(s))})
        if 'log_name' not in conf:
            conf['log_name'] = log_name
    conf['__file__'] = conffile
    return conf


def hexToInt(a,b):
    return a * 256 + b

def hexListToInt(datalist):
    return reduce(hexToInt, datalist)

def intToHexList(value):
    result = []
    while value > 0:
        n = value & 0xff
        result.insert(0,n)
        value = value >> 8
    return result

def intToHexListWithLen(value, length):
    result = []
    while value > 0:
        n = value & 0xff
        result.insert(0,n)
        value = value >> 8
    if length < len(result):
        return result[(len(result) - length):]
    else:
        num = length - len(result)
        while num > 0:
            result.insert(0,0x00)
            num -= 1
        return result

def hexListToHexStr(value):
    str = ''
    for i in value:
        str += ('%02x' % i)
    return str

def hexListToHexStrBlank(value):
    str = ''
    for i in value:
        str += ('%02x ' % i)
    return str
