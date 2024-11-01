# {py:mod}`weasyl.test.conftest`

```{py:module} weasyl.test.conftest
```

```{autodoc2-docstring} weasyl.test.conftest
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`TestApp <weasyl.test.conftest.TestApp>`
  - ```{autodoc2-docstring} weasyl.test.conftest.TestApp
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`setupdb <weasyl.test.conftest.setupdb>`
  - ```{autodoc2-docstring} weasyl.test.conftest.setupdb
    :summary:
    ```
* - {py:obj}`empty_storage <weasyl.test.conftest.empty_storage>`
  - ```{autodoc2-docstring} weasyl.test.conftest.empty_storage
    :summary:
    ```
* - {py:obj}`configurator <weasyl.test.conftest.configurator>`
  - ```{autodoc2-docstring} weasyl.test.conftest.configurator
    :summary:
    ```
* - {py:obj}`setup_request_environment <weasyl.test.conftest.setup_request_environment>`
  - ```{autodoc2-docstring} weasyl.test.conftest.setup_request_environment
    :summary:
    ```
* - {py:obj}`lower_bcrypt_rounds <weasyl.test.conftest.lower_bcrypt_rounds>`
  - ```{autodoc2-docstring} weasyl.test.conftest.lower_bcrypt_rounds
    :summary:
    ```
* - {py:obj}`drop_email <weasyl.test.conftest.drop_email>`
  - ```{autodoc2-docstring} weasyl.test.conftest.drop_email
    :summary:
    ```
* - {py:obj}`db <weasyl.test.conftest.db>`
  - ```{autodoc2-docstring} weasyl.test.conftest.db
    :summary:
    ```
* - {py:obj}`cache_ <weasyl.test.conftest.cache_>`
  - ```{autodoc2-docstring} weasyl.test.conftest.cache_
    :summary:
    ```
* - {py:obj}`template_cache <weasyl.test.conftest.template_cache>`
  - ```{autodoc2-docstring} weasyl.test.conftest.template_cache
    :summary:
    ```
* - {py:obj}`no_csrf <weasyl.test.conftest.no_csrf>`
  - ```{autodoc2-docstring} weasyl.test.conftest.no_csrf
    :summary:
    ```
* - {py:obj}`deterministic_marketplace_tests <weasyl.test.conftest.deterministic_marketplace_tests>`
  - ```{autodoc2-docstring} weasyl.test.conftest.deterministic_marketplace_tests
    :summary:
    ```
* - {py:obj}`disable_turnstile <weasyl.test.conftest.disable_turnstile>`
  - ```{autodoc2-docstring} weasyl.test.conftest.disable_turnstile
    :summary:
    ```
* - {py:obj}`wsgi_app <weasyl.test.conftest.wsgi_app>`
  - ```{autodoc2-docstring} weasyl.test.conftest.wsgi_app
    :summary:
    ```
* - {py:obj}`app <weasyl.test.conftest.app>`
  - ```{autodoc2-docstring} weasyl.test.conftest.app
    :summary:
    ```
````

### API

````{py:function} setupdb(request)
:canonical: weasyl.test.conftest.setupdb

```{autodoc2-docstring} weasyl.test.conftest.setupdb
```
````

````{py:function} empty_storage()
:canonical: weasyl.test.conftest.empty_storage

```{autodoc2-docstring} weasyl.test.conftest.empty_storage
```
````

````{py:function} configurator()
:canonical: weasyl.test.conftest.configurator

```{autodoc2-docstring} weasyl.test.conftest.configurator
```
````

````{py:function} setup_request_environment(request, configurator)
:canonical: weasyl.test.conftest.setup_request_environment

```{autodoc2-docstring} weasyl.test.conftest.setup_request_environment
```
````

````{py:function} lower_bcrypt_rounds(monkeypatch)
:canonical: weasyl.test.conftest.lower_bcrypt_rounds

```{autodoc2-docstring} weasyl.test.conftest.lower_bcrypt_rounds
```
````

````{py:function} drop_email(monkeypatch)
:canonical: weasyl.test.conftest.drop_email

```{autodoc2-docstring} weasyl.test.conftest.drop_email
```
````

````{py:function} db(request)
:canonical: weasyl.test.conftest.db

```{autodoc2-docstring} weasyl.test.conftest.db
```
````

````{py:function} cache_(request)
:canonical: weasyl.test.conftest.cache_

```{autodoc2-docstring} weasyl.test.conftest.cache_
```
````

````{py:function} template_cache()
:canonical: weasyl.test.conftest.template_cache

```{autodoc2-docstring} weasyl.test.conftest.template_cache
```
````

````{py:function} no_csrf(monkeypatch)
:canonical: weasyl.test.conftest.no_csrf

```{autodoc2-docstring} weasyl.test.conftest.no_csrf
```
````

````{py:function} deterministic_marketplace_tests(monkeypatch)
:canonical: weasyl.test.conftest.deterministic_marketplace_tests

```{autodoc2-docstring} weasyl.test.conftest.deterministic_marketplace_tests
```
````

````{py:function} disable_turnstile(monkeypatch)
:canonical: weasyl.test.conftest.disable_turnstile

```{autodoc2-docstring} weasyl.test.conftest.disable_turnstile
```
````

````{py:function} wsgi_app()
:canonical: weasyl.test.conftest.wsgi_app

```{autodoc2-docstring} weasyl.test.conftest.wsgi_app
```
````

`````{py:class} TestApp
:canonical: weasyl.test.conftest.TestApp

Bases: {py:obj}`webtest.TestApp`

```{autodoc2-docstring} weasyl.test.conftest.TestApp
```

````{py:method} do_request(req, status=None, expect_errors=None)
:canonical: weasyl.test.conftest.TestApp.do_request

```{autodoc2-docstring} weasyl.test.conftest.TestApp.do_request
```

````

`````

````{py:function} app(wsgi_app)
:canonical: weasyl.test.conftest.app

```{autodoc2-docstring} weasyl.test.conftest.app
```
````
