# TODO(kailys): Doc and create examples

class ConfigOption(object):
    "A class representing options for ``Config``."

    def __init__(self, name, value_map):
        self.name = name
        self.value_to_code_map = value_map
        self.code_to_value_map = {v: k for k, v in value_map.items()}
        self.values = value_map.keys()
        self.codes = value_map.values()

    def get_code(self, value):
        """
        Returns the code corresponding to the given value or the empty string if it
        does not exist.
        """
        return self.value_to_code_map.get(value, '')

    def get_value(self, code):
        """
        Returns the value corresponding to the given code or None if it does not
        exist.
        """
        return self.code_to_value_map.get(code)


def BoolOption(name, code):
    """
    A specialized boolean option which uses the provided character code when the
    option is on and an empty string when it is off.
    """
    return ConfigOption(name, {True: code, False: ''})


class DuplicateCode(Exception):
    pass


class InvalidValue(ValueError):
    pass


class ConfigAttribute(object):
    def __init__(self, option):
        self.option = option

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance._values.get(self.option.name)

    def __set__(self, instance, value):
        if value not in self.option.values:
            raise InvalidValue(value, self.option.name)
        instance._values[self.option.name] = value


class BaseConfig(object):
    _options = {}
    _options_by_code = {}
    all_option_codes = ''

    def __init__(self):
        self._values = {}

    def __repr__(self):
        return '%s(%r)' % (type(self).__name__, self._values)

    def to_code(self):
        """
        Render into character codes.
        """
        result = []
        for key, value in self._values.items():
            result.append(self._options[key].get_code(value))
        result.sort()
        return "".join(result)

    @classmethod
    def from_code(cls, code):
        """
        Render from character codes.
        """
        config = cls()
        for char in code:
            option = cls._options_by_code.get(char)
            if not option:
                # do not complain; we sometimes want to make subsets of config codes
                continue
            config._values[option.name] = option.get_value(char)
        return config


def find_duplicate(values):
    seen = set()
    for value in values:
        if value in seen:
            return value
        seen.add(value)
    return None


# argument: a list of ConfigOptions. This will return a class that can configure
# the specified options.
def create_configuration(options, base=BaseConfig):
    duplicated_code = find_duplicate(
        code for option in options for code in option.codes if code)
    if duplicated_code:
        raise DuplicateCode(duplicated_code)

    options_dict = {option.name: option for option in options}
    options_by_code = {
        code: option for option in options for code in option.codes if code}

    class Config(base):
        _options = options_dict
        _options_by_code = options_by_code
        all_option_codes = ''.join(options_by_code)

    for option in options:
        setattr(Config, option.name, ConfigAttribute(option))

    return Config
