from configparser import ConfigParser, NoOptionError, NoSectionError
from typing import overload

from weasyl import macro


_in_test = False


config_obj = ConfigParser()

with open(macro.MACRO_CFG_SITE_CONFIG, 'r') as f:
    config_obj.read_file(f, source=macro.MACRO_CFG_SITE_CONFIG)
del f


@overload
def config_read_setting(setting: str, value: None = None, *, section: str = 'general') -> str | None:
    ...


@overload
def config_read_setting(setting: str, value: str, *, section: str = 'general') -> str:
    ...


def config_read_setting(setting, value=None, *, section='general'):
    """
    Retrieves a value from the weasyl config.
    Defaults to 'general' section. If the key or section is missing, returns
    `value`, default None.
    """
    try:
        return config_obj.get(section, setting)
    except (NoOptionError, NoSectionError):
        return value


def config_read_bool(setting: str, section: str = 'general') -> bool:
    """
    Retrieves a boolean value from the weasyl config.
    Defaults to 'general' section. If the key or section is missing, or
    the value isn't a valid boolean, returns False.
    """
    try:
        return config_obj.getboolean(section, setting)
    except (NoOptionError, NoSectionError, ValueError):
        return False
