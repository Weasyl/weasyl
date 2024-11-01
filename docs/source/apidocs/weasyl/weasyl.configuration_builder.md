# {py:mod}`weasyl.configuration_builder`

```{py:module} weasyl.configuration_builder
```

```{autodoc2-docstring} weasyl.configuration_builder
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`ConfigOption <weasyl.configuration_builder.ConfigOption>`
  - ```{autodoc2-docstring} weasyl.configuration_builder.ConfigOption
    :summary:
    ```
* - {py:obj}`ConfigAttribute <weasyl.configuration_builder.ConfigAttribute>`
  - ```{autodoc2-docstring} weasyl.configuration_builder.ConfigAttribute
    :summary:
    ```
* - {py:obj}`BaseConfig <weasyl.configuration_builder.BaseConfig>`
  - ```{autodoc2-docstring} weasyl.configuration_builder.BaseConfig
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`BoolOption <weasyl.configuration_builder.BoolOption>`
  - ```{autodoc2-docstring} weasyl.configuration_builder.BoolOption
    :summary:
    ```
* - {py:obj}`find_duplicate <weasyl.configuration_builder.find_duplicate>`
  - ```{autodoc2-docstring} weasyl.configuration_builder.find_duplicate
    :summary:
    ```
* - {py:obj}`create_configuration <weasyl.configuration_builder.create_configuration>`
  - ```{autodoc2-docstring} weasyl.configuration_builder.create_configuration
    :summary:
    ```
````

### API

`````{py:class} ConfigOption(name, value_map)
:canonical: weasyl.configuration_builder.ConfigOption

```{autodoc2-docstring} weasyl.configuration_builder.ConfigOption
```

```{rubric} Initialization
```

```{autodoc2-docstring} weasyl.configuration_builder.ConfigOption.__init__
```

````{py:method} get_code(value)
:canonical: weasyl.configuration_builder.ConfigOption.get_code

```{autodoc2-docstring} weasyl.configuration_builder.ConfigOption.get_code
```

````

````{py:method} get_value(code)
:canonical: weasyl.configuration_builder.ConfigOption.get_value

```{autodoc2-docstring} weasyl.configuration_builder.ConfigOption.get_value
```

````

`````

````{py:function} BoolOption(name, code)
:canonical: weasyl.configuration_builder.BoolOption

```{autodoc2-docstring} weasyl.configuration_builder.BoolOption
```
````

```{py:exception} DuplicateCode()
:canonical: weasyl.configuration_builder.DuplicateCode

Bases: {py:obj}`Exception`

```

```{py:exception} InvalidValue()
:canonical: weasyl.configuration_builder.InvalidValue

Bases: {py:obj}`ValueError`

```

`````{py:class} ConfigAttribute(option)
:canonical: weasyl.configuration_builder.ConfigAttribute

```{autodoc2-docstring} weasyl.configuration_builder.ConfigAttribute
```

```{rubric} Initialization
```

```{autodoc2-docstring} weasyl.configuration_builder.ConfigAttribute.__init__
```

````{py:method} __get__(instance, owner)
:canonical: weasyl.configuration_builder.ConfigAttribute.__get__

```{autodoc2-docstring} weasyl.configuration_builder.ConfigAttribute.__get__
```

````

````{py:method} __set__(instance, value)
:canonical: weasyl.configuration_builder.ConfigAttribute.__set__

```{autodoc2-docstring} weasyl.configuration_builder.ConfigAttribute.__set__
```

````

`````

`````{py:class} BaseConfig()
:canonical: weasyl.configuration_builder.BaseConfig

```{autodoc2-docstring} weasyl.configuration_builder.BaseConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} weasyl.configuration_builder.BaseConfig.__init__
```

````{py:attribute} _options
:canonical: weasyl.configuration_builder.BaseConfig._options
:value: >
   None

```{autodoc2-docstring} weasyl.configuration_builder.BaseConfig._options
```

````

````{py:attribute} _options_by_code
:canonical: weasyl.configuration_builder.BaseConfig._options_by_code
:value: >
   None

```{autodoc2-docstring} weasyl.configuration_builder.BaseConfig._options_by_code
```

````

````{py:attribute} all_option_codes
:canonical: weasyl.configuration_builder.BaseConfig.all_option_codes
:value: <Multiline-String>

```{autodoc2-docstring} weasyl.configuration_builder.BaseConfig.all_option_codes
```

````

````{py:method} __repr__()
:canonical: weasyl.configuration_builder.BaseConfig.__repr__

````

````{py:method} to_code()
:canonical: weasyl.configuration_builder.BaseConfig.to_code

```{autodoc2-docstring} weasyl.configuration_builder.BaseConfig.to_code
```

````

````{py:method} from_code(code)
:canonical: weasyl.configuration_builder.BaseConfig.from_code
:classmethod:

```{autodoc2-docstring} weasyl.configuration_builder.BaseConfig.from_code
```

````

`````

````{py:function} find_duplicate(values)
:canonical: weasyl.configuration_builder.find_duplicate

```{autodoc2-docstring} weasyl.configuration_builder.find_duplicate
```
````

````{py:function} create_configuration(options, base=BaseConfig)
:canonical: weasyl.configuration_builder.create_configuration

```{autodoc2-docstring} weasyl.configuration_builder.create_configuration
```
````
