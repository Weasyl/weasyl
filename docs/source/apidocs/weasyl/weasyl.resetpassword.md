# {py:mod}`weasyl.resetpassword`

```{py:module} weasyl.resetpassword
```

```{autodoc2-docstring} weasyl.resetpassword
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_hash_token <weasyl.resetpassword._hash_token>`
  - ```{autodoc2-docstring} weasyl.resetpassword._hash_token
    :summary:
    ```
* - {py:obj}`request <weasyl.resetpassword.request>`
  - ```{autodoc2-docstring} weasyl.resetpassword.request
    :summary:
    ```
* - {py:obj}`_find_reset_target <weasyl.resetpassword._find_reset_target>`
  - ```{autodoc2-docstring} weasyl.resetpassword._find_reset_target
    :summary:
    ```
* - {py:obj}`prepare <weasyl.resetpassword.prepare>`
  - ```{autodoc2-docstring} weasyl.resetpassword.prepare
    :summary:
    ```
* - {py:obj}`reset <weasyl.resetpassword.reset>`
  - ```{autodoc2-docstring} weasyl.resetpassword.reset
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`Unregistered <weasyl.resetpassword.Unregistered>`
  - ```{autodoc2-docstring} weasyl.resetpassword.Unregistered
    :summary:
    ```
````

### API

````{py:data} Unregistered
:canonical: weasyl.resetpassword.Unregistered
:value: >
   'namedtuple(...)'

```{autodoc2-docstring} weasyl.resetpassword.Unregistered
```

````

````{py:function} _hash_token(token)
:canonical: weasyl.resetpassword._hash_token

```{autodoc2-docstring} weasyl.resetpassword._hash_token
```
````

````{py:function} request(email)
:canonical: weasyl.resetpassword.request

```{autodoc2-docstring} weasyl.resetpassword.request
```
````

````{py:function} _find_reset_target(db, email)
:canonical: weasyl.resetpassword._find_reset_target

```{autodoc2-docstring} weasyl.resetpassword._find_reset_target
```
````

````{py:function} prepare(token)
:canonical: weasyl.resetpassword.prepare

```{autodoc2-docstring} weasyl.resetpassword.prepare
```
````

````{py:function} reset(*, token, password, expect_userid, address)
:canonical: weasyl.resetpassword.reset

```{autodoc2-docstring} weasyl.resetpassword.reset
```
````
