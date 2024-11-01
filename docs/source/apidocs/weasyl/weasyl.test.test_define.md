# {py:mod}`weasyl.test.test_define`

```{py:module} weasyl.test.test_define
```

```{autodoc2-docstring} weasyl.test.test_define
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`l2dl <weasyl.test.test_define.l2dl>`
  - ```{autodoc2-docstring} weasyl.test.test_define.l2dl
    :summary:
    ```
* - {py:obj}`test_paginate <weasyl.test.test_define.test_paginate>`
  - ```{autodoc2-docstring} weasyl.test.test_define.test_paginate
    :summary:
    ```
* - {py:obj}`test_iso8601 <weasyl.test.test_define.test_iso8601>`
  - ```{autodoc2-docstring} weasyl.test.test_define.test_iso8601
    :summary:
    ```
* - {py:obj}`test_parse_iso8601 <weasyl.test.test_define.test_parse_iso8601>`
  - ```{autodoc2-docstring} weasyl.test.test_define.test_parse_iso8601
    :summary:
    ```
* - {py:obj}`test_parse_iso8601_invalid_format <weasyl.test.test_define.test_parse_iso8601_invalid_format>`
  - ```{autodoc2-docstring} weasyl.test.test_define.test_parse_iso8601_invalid_format
    :summary:
    ```
* - {py:obj}`create_with_user <weasyl.test.test_define.create_with_user>`
  - ```{autodoc2-docstring} weasyl.test.test_define.create_with_user
    :summary:
    ```
* - {py:obj}`test_content_view <weasyl.test.test_define.test_content_view>`
  - ```{autodoc2-docstring} weasyl.test.test_define.test_content_view
    :summary:
    ```
* - {py:obj}`test_content_view_twice <weasyl.test.test_define.test_content_view_twice>`
  - ```{autodoc2-docstring} weasyl.test.test_define.test_content_view_twice
    :summary:
    ```
* - {py:obj}`test_content_view_same_user_twice <weasyl.test.test_define.test_content_view_same_user_twice>`
  - ```{autodoc2-docstring} weasyl.test.test_define.test_content_view_same_user_twice
    :summary:
    ```
* - {py:obj}`test_content_view_same_user_twice_clearing_views <weasyl.test.test_define.test_content_view_same_user_twice_clearing_views>`
  - ```{autodoc2-docstring} weasyl.test.test_define.test_content_view_same_user_twice_clearing_views
    :summary:
    ```
* - {py:obj}`test_anonymous_content_view <weasyl.test.test_define.test_anonymous_content_view>`
  - ```{autodoc2-docstring} weasyl.test.test_define.test_anonymous_content_view
    :summary:
    ```
* - {py:obj}`test_two_anonymous_content_views <weasyl.test.test_define.test_two_anonymous_content_views>`
  - ```{autodoc2-docstring} weasyl.test.test_define.test_two_anonymous_content_views
    :summary:
    ```
* - {py:obj}`test_viewing_own_profile <weasyl.test.test_define.test_viewing_own_profile>`
  - ```{autodoc2-docstring} weasyl.test.test_define.test_viewing_own_profile
    :summary:
    ```
* - {py:obj}`test_sysname <weasyl.test.test_define.test_sysname>`
  - ```{autodoc2-docstring} weasyl.test.test_define.test_sysname
    :summary:
    ```
* - {py:obj}`test_nul <weasyl.test.test_define.test_nul>`
  - ```{autodoc2-docstring} weasyl.test.test_define.test_nul
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`pagination_tests <weasyl.test.test_define.pagination_tests>`
  - ```{autodoc2-docstring} weasyl.test.test_define.pagination_tests
    :summary:
    ```
* - {py:obj}`iso8601_tests <weasyl.test.test_define.iso8601_tests>`
  - ```{autodoc2-docstring} weasyl.test.test_define.iso8601_tests
    :summary:
    ```
* - {py:obj}`view_things <weasyl.test.test_define.view_things>`
  - ```{autodoc2-docstring} weasyl.test.test_define.view_things
    :summary:
    ```
````

### API

````{py:function} l2dl(l, k='k')
:canonical: weasyl.test.test_define.l2dl

```{autodoc2-docstring} weasyl.test.test_define.l2dl
```
````

````{py:data} pagination_tests
:canonical: weasyl.test.test_define.pagination_tests
:value: >
   [((), (None, 1)), ((), (None, 2)), ((), (None, None)), ((), (2, 3)), ((), (1, 2)), ((), (None, 4)), ...

```{autodoc2-docstring} weasyl.test.test_define.pagination_tests
```

````

````{py:function} test_paginate(parameters, expected_pair, expected_rows)
:canonical: weasyl.test.test_define.test_paginate

```{autodoc2-docstring} weasyl.test.test_define.test_paginate
```
````

````{py:data} iso8601_tests
:canonical: weasyl.test.test_define.iso8601_tests
:value: >
   [(1392206700, '2014-02-12T17:05:00Z'), (1392206701, '2014-02-12T17:05:01Z'), (1392206760, '2014-02-1...

```{autodoc2-docstring} weasyl.test.test_define.iso8601_tests
```

````

````{py:function} test_iso8601(parameter, expected)
:canonical: weasyl.test.test_define.test_iso8601

```{autodoc2-docstring} weasyl.test.test_define.test_iso8601
```
````

````{py:function} test_parse_iso8601(parameter, expected)
:canonical: weasyl.test.test_define.test_parse_iso8601

```{autodoc2-docstring} weasyl.test.test_define.test_parse_iso8601
```
````

````{py:function} test_parse_iso8601_invalid_format()
:canonical: weasyl.test.test_define.test_parse_iso8601_invalid_format

```{autodoc2-docstring} weasyl.test.test_define.test_parse_iso8601_invalid_format
```
````

````{py:function} create_with_user(func)
:canonical: weasyl.test.test_define.create_with_user

```{autodoc2-docstring} weasyl.test.test_define.create_with_user
```
````

````{py:data} view_things
:canonical: weasyl.test.test_define.view_things
:value: >
   [(), (), (), ()]

```{autodoc2-docstring} weasyl.test.test_define.view_things
```

````

````{py:function} test_content_view(db, create_func, model, feature)
:canonical: weasyl.test.test_define.test_content_view

```{autodoc2-docstring} weasyl.test.test_define.test_content_view
```
````

````{py:function} test_content_view_twice(db, create_func, model, feature)
:canonical: weasyl.test.test_define.test_content_view_twice

```{autodoc2-docstring} weasyl.test.test_define.test_content_view_twice
```
````

````{py:function} test_content_view_same_user_twice(db, create_func, model, feature)
:canonical: weasyl.test.test_define.test_content_view_same_user_twice

```{autodoc2-docstring} weasyl.test.test_define.test_content_view_same_user_twice
```
````

````{py:function} test_content_view_same_user_twice_clearing_views(db, create_func, model, feature)
:canonical: weasyl.test.test_define.test_content_view_same_user_twice_clearing_views

```{autodoc2-docstring} weasyl.test.test_define.test_content_view_same_user_twice_clearing_views
```
````

````{py:function} test_anonymous_content_view(db, create_func, model, feature)
:canonical: weasyl.test.test_define.test_anonymous_content_view

```{autodoc2-docstring} weasyl.test.test_define.test_anonymous_content_view
```
````

````{py:function} test_two_anonymous_content_views(db, create_func, model, feature)
:canonical: weasyl.test.test_define.test_two_anonymous_content_views

```{autodoc2-docstring} weasyl.test.test_define.test_two_anonymous_content_views
```
````

````{py:function} test_viewing_own_profile(db)
:canonical: weasyl.test.test_define.test_viewing_own_profile

```{autodoc2-docstring} weasyl.test.test_define.test_viewing_own_profile
```
````

````{py:function} test_sysname()
:canonical: weasyl.test.test_define.test_sysname

```{autodoc2-docstring} weasyl.test.test_define.test_sysname
```
````

````{py:function} test_nul()
:canonical: weasyl.test.test_define.test_nul

```{autodoc2-docstring} weasyl.test.test_define.test_nul
```
````
