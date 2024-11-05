# {py:mod}`libweasyl.conftest`

```{py:module} libweasyl.conftest
```

```{autodoc2-docstring} libweasyl.conftest
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`setup <libweasyl.conftest.setup>`
  - ```{autodoc2-docstring} libweasyl.conftest.setup
    :summary:
    ```
* - {py:obj}`staticdir <libweasyl.conftest.staticdir>`
  - ```{autodoc2-docstring} libweasyl.conftest.staticdir
    :summary:
    ```
* - {py:obj}`db <libweasyl.conftest.db>`
  - ```{autodoc2-docstring} libweasyl.conftest.db
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`engine <libweasyl.conftest.engine>`
  - ```{autodoc2-docstring} libweasyl.conftest.engine
    :summary:
    ```
* - {py:obj}`sessionmaker <libweasyl.conftest.sessionmaker>`
  - ```{autodoc2-docstring} libweasyl.conftest.sessionmaker
    :summary:
    ```
````

### API

````{py:data} engine
:canonical: libweasyl.conftest.engine
:value: >
   'create_engine(...)'

```{autodoc2-docstring} libweasyl.conftest.engine
```

````

````{py:data} sessionmaker
:canonical: libweasyl.conftest.sessionmaker
:value: >
   'scoped_session(...)'

```{autodoc2-docstring} libweasyl.conftest.sessionmaker
```

````

````{py:function} setup(request)
:canonical: libweasyl.conftest.setup

```{autodoc2-docstring} libweasyl.conftest.setup
```
````

````{py:function} staticdir(tmpdir)
:canonical: libweasyl.conftest.staticdir

```{autodoc2-docstring} libweasyl.conftest.staticdir
```
````

````{py:function} db(request)
:canonical: libweasyl.conftest.db

```{autodoc2-docstring} libweasyl.conftest.db
```
````
