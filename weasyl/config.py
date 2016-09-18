from __future__ import absolute_import

import ConfigParser

from weasyl import macro


_in_test = False


config_obj = ConfigParser.ConfigParser()
config_obj.read([macro.MACRO_CFG_SITE_CONFIG])


def config_read():
    return dict(config_obj.items('general'))


def config_read_setting(setting, value=None, section='general'):
    """
    Retrieves a value from the weasyl config.
    Defaults to 'general' section. If the key or section is missing, returns
    `value`, default None.
    """
    try:
        return config_obj.get(section, setting)
    except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
        return value


def config_read_bool(setting, value=False, section='general'):
    """
    Retrieves a boolean value from the weasyl config.
    Defaults to 'general' section. If the key or section is missing, or
    the value isn't a valid boolean, returns `value`, default False.
    """
    try:
        return config_obj.getboolean(section, setting)
    except (ConfigParser.NoOptionError, ConfigParser.NoSectionError, ValueError):
        return value
