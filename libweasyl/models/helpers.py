import contextlib

import json
import arrow
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import Mutable, MutableDict
from sqlalchemy import types

from ..legacy import UNIXTIME_OFFSET
from .. import ratings


def reverse_dict(d):
    return {v: k for k, v in d.items()}


class CharSettings(Mutable):
    def __init__(self, settings, file_types, enum_values):
        self._settings = settings
        self._file_types = file_types
        self._enum_values = enum_values

    def __repr__(self):
        return '<CharSettings %#x; %r; file types %r; enums %r>' % (
            id(self), self._settings, self._file_types, self._enum_values)

    @classmethod
    def coerce(cls, key, value):
        if value is None:
            return cls(set(), {}, {})
        elif isinstance(value, cls):
            return value
        else:
            return super().coerce(key, value)

    @property
    def mutable_settings(self):
        self.changed()
        return self._settings

    @property
    def settings(self):
        return frozenset(self._settings)

    @settings.setter
    def settings(self, value):
        self._settings = set(value)
        self.changed()

    @property
    def mutable_file_types(self):
        self.changed()
        return self._file_types

    @property
    def file_types(self):
        return self._file_types

    @file_types.setter
    def file_types(self, value):
        self._file_types = dict(value)
        self.changed()

    def __contains__(self, k):
        return k in self._settings

    def __getitem__(self, k):
        return self._enum_values.get(k)

    def __setitem__(self, k, v):
        if v is None:
            self._enum_values.pop(k, None)
        else:
            self._enum_values[k] = v
        self.changed()


class CharSettingsColumn(types.TypeDecorator):
    impl = types.String
    cache_ok = True

    file_type_things = {
        '~': 'cover',
        '-': 'thumb',
        '=': 'submit',
        '>': 'avatar',
        '<': 'banner',
        '#': 'propic',
        '$': 'ad',
    }

    reverse_file_type_things = reverse_dict(file_type_things)

    file_type_kinds = {
        'J': 'jpg',
        'P': 'png',
        'G': 'gif',
        'T': 'txt',
        'H': 'htm',
        'M': 'mp3',
        'F': 'swf',
        'A': 'pdf',
    }

    reverse_file_type_kinds = reverse_dict(file_type_kinds)

    def __init__(self, settings_map, enums=(), **kwargs):
        super().__init__(**kwargs)

        enums = dict(enums)

        # SQLAlchemy cache keys
        self.settings_map = tuple(settings_map.items())
        self.enums = tuple((k, tuple(v.items())) for k, v in enums.items())

        self._settings_map = {k: (None, v) for k, v in settings_map.items()}
        for name, enum_settings in enums.items():
            for char, setting in enum_settings.items():
                self._settings_map[char] = name, setting
        self._reverse_settings_map = reverse_dict(self._settings_map)

    def process_bind_param(self, value, dialect):
        if not isinstance(value, CharSettings):
            return value
        ret = []
        for thing, kind in value._file_types.items():
            ret.append(self.reverse_file_type_things[thing] + self.reverse_file_type_kinds[kind])
        ret.extend(self._reverse_settings_map[None, s] for s in value._settings)
        ret.extend(self._reverse_settings_map[ev] for ev in value._enum_values.items())
        ret.sort()
        return ''.join(ret)

    def process_result_value(self, original_value, dialect):
        if not isinstance(original_value, str):
            return original_value
        chars = iter(original_value)
        settings = set()
        file_types = {}
        enum_values = {}
        for char in chars:
            if char in self.file_type_things:
                filetype = next(chars)
                try:
                    file_types[self.file_type_things[char]] = self.file_type_kinds[filetype]
                except KeyError:
                    raise ValueError(filetype, 'not found among', self.file_type_kinds)
            else:
                try:
                    enum, value = self._settings_map[char]
                except KeyError:
                    raise ValueError(char, 'not found among', self._settings_map)
                if enum is None:
                    settings.add(value)
                else:
                    enum_values[enum] = value
        return CharSettings(settings, file_types, enum_values)

    @contextlib.contextmanager
    def clauses_for(self, column):
        def clause_for(a, b=None):
            if b is None:
                enum, value = None, a

                @hybrid_property
                def clause(inst):
                    return value in getattr(inst, column)

                @clause.setter
                def clause(inst, new_value):
                    settings = getattr(inst, column)
                    if new_value:
                        settings.mutable_settings.add(value)
                    else:
                        settings.mutable_settings.discard(value)
            else:
                enum, value = a, b

                @hybrid_property
                def clause(inst):
                    return getattr(inst, column)[enum] == value

                @clause.setter
                def clause(inst, new_value):
                    if new_value:
                        getattr(inst, column)[enum] = value
                    else:
                        raise ValueError("can't set this attribute to a false-y value")

            @clause.expression
            def clause(cls):
                return getattr(cls, column).op('~')(self._reverse_settings_map[enum, value])

            return clause

        yield clause_for


CharSettings.associate_with(CharSettingsColumn)


class WeasylTimestampColumn(types.TypeDecorator):
    impl = types.INTEGER
    cache_ok = True

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return arrow.get(value - UNIXTIME_OFFSET)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return value.int_timestamp + UNIXTIME_OFFSET


class ArrowColumn(types.TypeDecorator):
    impl = types.TIMESTAMP
    cache_ok = True

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return arrow.get(value)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return value.to('UTC').naive


class JSONValuesColumn(types.TypeDecorator):
    impl = HSTORE

    def process_bind_param(self, value, dialect):
        if not isinstance(value, dict):
            return value
        ret = {k: json.dumps(v) for k, v in value.items()}
        return ret

    def process_result_value(self, value, dialect):
        if not value:
            return MutableDict()
        ret = MutableDict({k: json.loads(v) for k, v in value.items()})
        return ret


MutableDict.associate_with(JSONValuesColumn)


class IntegerEnumColumn(types.TypeDecorator):
    impl = types.INTEGER
    cache_ok = True

    def __init__(self, enum_values):
        super().__init__()
        self.enum_values = tuple(enum_values.items())
        self._enum_values = enum_values
        self._reverse_enum_values = reverse_dict(enum_values)

    def process_bind_param(self, value, dialect):
        return self._reverse_enum_values.get(value, value)

    def process_result_value(self, value, dialect):
        return self._enum_values.get(value, value)


RatingColumn = IntegerEnumColumn({rating.code: rating for rating in ratings.ALL_RATINGS})


def clauses_for(table, column='settings'):
    return table.c[column].type.clauses_for(column)
