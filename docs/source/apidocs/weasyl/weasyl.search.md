# {py:mod}`weasyl.search`

```{py:module} weasyl.search
```

```{autodoc2-docstring} weasyl.search
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`Query <weasyl.search.Query>`
  - ```{autodoc2-docstring} weasyl.search.Query
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`select_users <weasyl.search.select_users>`
  - ```{autodoc2-docstring} weasyl.search.select_users
    :summary:
    ```
* - {py:obj}`_find_without_media <weasyl.search._find_without_media>`
  - ```{autodoc2-docstring} weasyl.search._find_without_media
    :summary:
    ```
* - {py:obj}`select <weasyl.search.select>`
  - ```{autodoc2-docstring} weasyl.search.select
    :summary:
    ```
* - {py:obj}`browse <weasyl.search.browse>`
  - ```{autodoc2-docstring} weasyl.search.browse
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_QUERY_FIND_MODIFIERS <weasyl.search._QUERY_FIND_MODIFIERS>`
  - ```{autodoc2-docstring} weasyl.search._QUERY_FIND_MODIFIERS
    :summary:
    ```
* - {py:obj}`_QUERY_RATING_MODIFIERS <weasyl.search._QUERY_RATING_MODIFIERS>`
  - ```{autodoc2-docstring} weasyl.search._QUERY_RATING_MODIFIERS
    :summary:
    ```
* - {py:obj}`_QUERY_DELIMITER <weasyl.search._QUERY_DELIMITER>`
  - ```{autodoc2-docstring} weasyl.search._QUERY_DELIMITER
    :summary:
    ```
* - {py:obj}`_TABLE_INFORMATION <weasyl.search._TABLE_INFORMATION>`
  - ```{autodoc2-docstring} weasyl.search._TABLE_INFORMATION
    :summary:
    ```
* - {py:obj}`COUNT_LIMIT <weasyl.search.COUNT_LIMIT>`
  - ```{autodoc2-docstring} weasyl.search.COUNT_LIMIT
    :summary:
    ```
````

### API

````{py:data} _QUERY_FIND_MODIFIERS
:canonical: weasyl.search._QUERY_FIND_MODIFIERS
:value: >
   None

```{autodoc2-docstring} weasyl.search._QUERY_FIND_MODIFIERS
```

````

````{py:data} _QUERY_RATING_MODIFIERS
:canonical: weasyl.search._QUERY_RATING_MODIFIERS
:value: >
   None

```{autodoc2-docstring} weasyl.search._QUERY_RATING_MODIFIERS
```

````

````{py:data} _QUERY_DELIMITER
:canonical: weasyl.search._QUERY_DELIMITER
:value: >
   'compile(...)'

```{autodoc2-docstring} weasyl.search._QUERY_DELIMITER
```

````

````{py:data} _TABLE_INFORMATION
:canonical: weasyl.search._TABLE_INFORMATION
:value: >
   None

```{autodoc2-docstring} weasyl.search._TABLE_INFORMATION
```

````

````{py:data} COUNT_LIMIT
:canonical: weasyl.search.COUNT_LIMIT
:value: >
   10000

```{autodoc2-docstring} weasyl.search.COUNT_LIMIT
```

````

`````{py:class} Query()
:canonical: weasyl.search.Query

```{autodoc2-docstring} weasyl.search.Query
```

```{rubric} Initialization
```

```{autodoc2-docstring} weasyl.search.Query.__init__
```

````{py:method} add_criterion(criterion)
:canonical: weasyl.search.Query.add_criterion

```{autodoc2-docstring} weasyl.search.Query.add_criterion
```

````

````{py:method} __bool__()
:canonical: weasyl.search.Query.__bool__

```{autodoc2-docstring} weasyl.search.Query.__bool__
```

````

````{py:method} parse(query_string, find_default)
:canonical: weasyl.search.Query.parse
:classmethod:

```{autodoc2-docstring} weasyl.search.Query.parse
```

````

`````

````{py:function} select_users(q)
:canonical: weasyl.search.select_users

```{autodoc2-docstring} weasyl.search.select_users
```
````

````{py:function} _find_without_media(userid, rating, limit, search, within, cat, subcat, backid, nextid)
:canonical: weasyl.search._find_without_media

```{autodoc2-docstring} weasyl.search._find_without_media
```
````

````{py:function} select(**kwargs)
:canonical: weasyl.search.select

```{autodoc2-docstring} weasyl.search.select
```
````

````{py:function} browse(userid, rating, limit, find, cat, backid, nextid)
:canonical: weasyl.search.browse

```{autodoc2-docstring} weasyl.search.browse
```
````
