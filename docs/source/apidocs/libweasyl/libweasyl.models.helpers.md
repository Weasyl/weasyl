# {py:mod}`libweasyl.models.helpers`

```{py:module} libweasyl.models.helpers
```

```{autodoc2-docstring} libweasyl.models.helpers
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`CharSettings <libweasyl.models.helpers.CharSettings>`
  -
* - {py:obj}`CharSettingsColumn <libweasyl.models.helpers.CharSettingsColumn>`
  -
* - {py:obj}`WeasylTimestampColumn <libweasyl.models.helpers.WeasylTimestampColumn>`
  -
* - {py:obj}`ArrowColumn <libweasyl.models.helpers.ArrowColumn>`
  -
* - {py:obj}`JSONValuesColumn <libweasyl.models.helpers.JSONValuesColumn>`
  -
* - {py:obj}`IntegerEnumColumn <libweasyl.models.helpers.IntegerEnumColumn>`
  -
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`reverse_dict <libweasyl.models.helpers.reverse_dict>`
  - ```{autodoc2-docstring} libweasyl.models.helpers.reverse_dict
    :summary:
    ```
* - {py:obj}`clauses_for <libweasyl.models.helpers.clauses_for>`
  - ```{autodoc2-docstring} libweasyl.models.helpers.clauses_for
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`RatingColumn <libweasyl.models.helpers.RatingColumn>`
  - ```{autodoc2-docstring} libweasyl.models.helpers.RatingColumn
    :summary:
    ```
````

### API

````{py:function} reverse_dict(d)
:canonical: libweasyl.models.helpers.reverse_dict

```{autodoc2-docstring} libweasyl.models.helpers.reverse_dict
```
````

`````{py:class} CharSettings(settings, file_types, enum_values)
:canonical: libweasyl.models.helpers.CharSettings

Bases: {py:obj}`sqlalchemy.ext.mutable.Mutable`

````{py:method} __repr__()
:canonical: libweasyl.models.helpers.CharSettings.__repr__

````

````{py:method} coerce(key, value)
:canonical: libweasyl.models.helpers.CharSettings.coerce
:classmethod:

````

````{py:property} mutable_settings
:canonical: libweasyl.models.helpers.CharSettings.mutable_settings

```{autodoc2-docstring} libweasyl.models.helpers.CharSettings.mutable_settings
```

````

````{py:property} settings
:canonical: libweasyl.models.helpers.CharSettings.settings

```{autodoc2-docstring} libweasyl.models.helpers.CharSettings.settings
```

````

````{py:property} mutable_file_types
:canonical: libweasyl.models.helpers.CharSettings.mutable_file_types

```{autodoc2-docstring} libweasyl.models.helpers.CharSettings.mutable_file_types
```

````

````{py:property} file_types
:canonical: libweasyl.models.helpers.CharSettings.file_types

```{autodoc2-docstring} libweasyl.models.helpers.CharSettings.file_types
```

````

````{py:method} __contains__(k)
:canonical: libweasyl.models.helpers.CharSettings.__contains__

```{autodoc2-docstring} libweasyl.models.helpers.CharSettings.__contains__
```

````

````{py:method} __getitem__(k)
:canonical: libweasyl.models.helpers.CharSettings.__getitem__

```{autodoc2-docstring} libweasyl.models.helpers.CharSettings.__getitem__
```

````

````{py:method} __setitem__(k, v)
:canonical: libweasyl.models.helpers.CharSettings.__setitem__

```{autodoc2-docstring} libweasyl.models.helpers.CharSettings.__setitem__
```

````

`````

`````{py:class} CharSettingsColumn(settings_map, enums=(), **kwargs)
:canonical: libweasyl.models.helpers.CharSettingsColumn

Bases: {py:obj}`sqlalchemy.types.TypeDecorator`

````{py:attribute} impl
:canonical: libweasyl.models.helpers.CharSettingsColumn.impl
:value: >
   None

```{autodoc2-docstring} libweasyl.models.helpers.CharSettingsColumn.impl
```

````

````{py:attribute} cache_ok
:canonical: libweasyl.models.helpers.CharSettingsColumn.cache_ok
:value: >
   True

```{autodoc2-docstring} libweasyl.models.helpers.CharSettingsColumn.cache_ok
```

````

````{py:attribute} file_type_things
:canonical: libweasyl.models.helpers.CharSettingsColumn.file_type_things
:value: >
   None

```{autodoc2-docstring} libweasyl.models.helpers.CharSettingsColumn.file_type_things
```

````

````{py:attribute} reverse_file_type_things
:canonical: libweasyl.models.helpers.CharSettingsColumn.reverse_file_type_things
:value: >
   'reverse_dict(...)'

```{autodoc2-docstring} libweasyl.models.helpers.CharSettingsColumn.reverse_file_type_things
```

````

````{py:attribute} file_type_kinds
:canonical: libweasyl.models.helpers.CharSettingsColumn.file_type_kinds
:value: >
   None

```{autodoc2-docstring} libweasyl.models.helpers.CharSettingsColumn.file_type_kinds
```

````

````{py:attribute} reverse_file_type_kinds
:canonical: libweasyl.models.helpers.CharSettingsColumn.reverse_file_type_kinds
:value: >
   'reverse_dict(...)'

```{autodoc2-docstring} libweasyl.models.helpers.CharSettingsColumn.reverse_file_type_kinds
```

````

````{py:method} process_bind_param(value, dialect)
:canonical: libweasyl.models.helpers.CharSettingsColumn.process_bind_param

````

````{py:method} process_result_value(original_value, dialect)
:canonical: libweasyl.models.helpers.CharSettingsColumn.process_result_value

````

````{py:method} clauses_for(column)
:canonical: libweasyl.models.helpers.CharSettingsColumn.clauses_for

```{autodoc2-docstring} libweasyl.models.helpers.CharSettingsColumn.clauses_for
```

````

`````

`````{py:class} WeasylTimestampColumn(*args, **kwargs)
:canonical: libweasyl.models.helpers.WeasylTimestampColumn

Bases: {py:obj}`sqlalchemy.types.TypeDecorator`

````{py:attribute} impl
:canonical: libweasyl.models.helpers.WeasylTimestampColumn.impl
:value: >
   None

```{autodoc2-docstring} libweasyl.models.helpers.WeasylTimestampColumn.impl
```

````

````{py:attribute} cache_ok
:canonical: libweasyl.models.helpers.WeasylTimestampColumn.cache_ok
:value: >
   True

```{autodoc2-docstring} libweasyl.models.helpers.WeasylTimestampColumn.cache_ok
```

````

````{py:method} process_result_value(value, dialect)
:canonical: libweasyl.models.helpers.WeasylTimestampColumn.process_result_value

````

````{py:method} process_bind_param(value, dialect)
:canonical: libweasyl.models.helpers.WeasylTimestampColumn.process_bind_param

````

`````

`````{py:class} ArrowColumn(*args, **kwargs)
:canonical: libweasyl.models.helpers.ArrowColumn

Bases: {py:obj}`sqlalchemy.types.TypeDecorator`

````{py:attribute} impl
:canonical: libweasyl.models.helpers.ArrowColumn.impl
:value: >
   None

```{autodoc2-docstring} libweasyl.models.helpers.ArrowColumn.impl
```

````

````{py:attribute} cache_ok
:canonical: libweasyl.models.helpers.ArrowColumn.cache_ok
:value: >
   True

```{autodoc2-docstring} libweasyl.models.helpers.ArrowColumn.cache_ok
```

````

````{py:method} process_result_value(value, dialect)
:canonical: libweasyl.models.helpers.ArrowColumn.process_result_value

````

````{py:method} process_bind_param(value, dialect)
:canonical: libweasyl.models.helpers.ArrowColumn.process_bind_param

````

`````

`````{py:class} JSONValuesColumn(*args, **kwargs)
:canonical: libweasyl.models.helpers.JSONValuesColumn

Bases: {py:obj}`sqlalchemy.types.TypeDecorator`

````{py:attribute} impl
:canonical: libweasyl.models.helpers.JSONValuesColumn.impl
:value: >
   None

```{autodoc2-docstring} libweasyl.models.helpers.JSONValuesColumn.impl
```

````

````{py:method} process_bind_param(value, dialect)
:canonical: libweasyl.models.helpers.JSONValuesColumn.process_bind_param

````

````{py:method} process_result_value(value, dialect)
:canonical: libweasyl.models.helpers.JSONValuesColumn.process_result_value

````

`````

`````{py:class} IntegerEnumColumn(enum_values)
:canonical: libweasyl.models.helpers.IntegerEnumColumn

Bases: {py:obj}`sqlalchemy.types.TypeDecorator`

````{py:attribute} impl
:canonical: libweasyl.models.helpers.IntegerEnumColumn.impl
:value: >
   None

```{autodoc2-docstring} libweasyl.models.helpers.IntegerEnumColumn.impl
```

````

````{py:attribute} cache_ok
:canonical: libweasyl.models.helpers.IntegerEnumColumn.cache_ok
:value: >
   True

```{autodoc2-docstring} libweasyl.models.helpers.IntegerEnumColumn.cache_ok
```

````

````{py:method} process_bind_param(value, dialect)
:canonical: libweasyl.models.helpers.IntegerEnumColumn.process_bind_param

````

````{py:method} process_result_value(value, dialect)
:canonical: libweasyl.models.helpers.IntegerEnumColumn.process_result_value

````

`````

````{py:data} RatingColumn
:canonical: libweasyl.models.helpers.RatingColumn
:value: >
   'IntegerEnumColumn(...)'

```{autodoc2-docstring} libweasyl.models.helpers.RatingColumn
```

````

````{py:function} clauses_for(table, column='settings')
:canonical: libweasyl.models.helpers.clauses_for

```{autodoc2-docstring} libweasyl.models.helpers.clauses_for
```
````
