# {py:mod}`weasyl.turnstile`

```{py:module} weasyl.turnstile
```

```{autodoc2-docstring} weasyl.turnstile
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`Result <weasyl.turnstile.Result>`
  -
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_check <weasyl.turnstile._check>`
  - ```{autodoc2-docstring} weasyl.turnstile._check
    :summary:
    ```
* - {py:obj}`require <weasyl.turnstile.require>`
  - ```{autodoc2-docstring} weasyl.turnstile.require
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <weasyl.turnstile.logger>`
  - ```{autodoc2-docstring} weasyl.turnstile.logger
    :summary:
    ```
* - {py:obj}`SITE_KEY <weasyl.turnstile.SITE_KEY>`
  - ```{autodoc2-docstring} weasyl.turnstile.SITE_KEY
    :summary:
    ```
* - {py:obj}`_SECRET_KEY <weasyl.turnstile._SECRET_KEY>`
  - ```{autodoc2-docstring} weasyl.turnstile._SECRET_KEY
    :summary:
    ```
* - {py:obj}`ENFORCE <weasyl.turnstile.ENFORCE>`
  - ```{autodoc2-docstring} weasyl.turnstile.ENFORCE
    :summary:
    ```
````

### API

````{py:data} logger
:canonical: weasyl.turnstile.logger
:value: >
   'getLogger(...)'

```{autodoc2-docstring} weasyl.turnstile.logger
```

````

````{py:data} SITE_KEY
:canonical: weasyl.turnstile.SITE_KEY
:value: >
   'get(...)'

```{autodoc2-docstring} weasyl.turnstile.SITE_KEY
```

````

````{py:data} _SECRET_KEY
:canonical: weasyl.turnstile._SECRET_KEY
:value: >
   None

```{autodoc2-docstring} weasyl.turnstile._SECRET_KEY
```

````

````{py:data} ENFORCE
:canonical: weasyl.turnstile.ENFORCE
:value: >
   None

```{autodoc2-docstring} weasyl.turnstile.ENFORCE
```

````

`````{py:class} Result(*args, **kwds)
:canonical: weasyl.turnstile.Result

Bases: {py:obj}`enum.Enum`

````{py:attribute} NOT_LOADED
:canonical: weasyl.turnstile.Result.NOT_LOADED
:value: >
   'auto(...)'

```{autodoc2-docstring} weasyl.turnstile.Result.NOT_LOADED
```

````

````{py:attribute} NOT_COMPLETED
:canonical: weasyl.turnstile.Result.NOT_COMPLETED
:value: >
   'auto(...)'

```{autodoc2-docstring} weasyl.turnstile.Result.NOT_COMPLETED
```

````

````{py:attribute} INVALID
:canonical: weasyl.turnstile.Result.INVALID
:value: >
   'auto(...)'

```{autodoc2-docstring} weasyl.turnstile.Result.INVALID
```

````

````{py:attribute} SUCCESS
:canonical: weasyl.turnstile.Result.SUCCESS
:value: >
   'auto(...)'

```{autodoc2-docstring} weasyl.turnstile.Result.SUCCESS
```

````

`````

````{py:function} _check(request) -> weasyl.turnstile.Result
:canonical: weasyl.turnstile._check

```{autodoc2-docstring} weasyl.turnstile._check
```
````

````{py:function} require(request) -> None
:canonical: weasyl.turnstile.require

```{autodoc2-docstring} weasyl.turnstile.require
```
````
