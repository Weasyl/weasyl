# {py:mod}`libweasyl.models.api`

```{py:module} libweasyl.models.api
```

```{autodoc2-docstring} libweasyl.models.api
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`APIToken <libweasyl.models.api.APIToken>`
  - ```{autodoc2-docstring} libweasyl.models.api.APIToken
    :summary:
    ```
* - {py:obj}`OAuthConsumer <libweasyl.models.api.OAuthConsumer>`
  - ```{autodoc2-docstring} libweasyl.models.api.OAuthConsumer
    :summary:
    ```
* - {py:obj}`OAuthBearerToken <libweasyl.models.api.OAuthBearerToken>`
  - ```{autodoc2-docstring} libweasyl.models.api.OAuthBearerToken
    :summary:
    ```
````

### API

`````{py:class} APIToken
:canonical: libweasyl.models.api.APIToken

Bases: {py:obj}`libweasyl.models.meta.Base`

```{autodoc2-docstring} libweasyl.models.api.APIToken
```

````{py:attribute} __table__
:canonical: libweasyl.models.api.APIToken.__table__
:value: >
   None

```{autodoc2-docstring} libweasyl.models.api.APIToken.__table__
```

````

````{py:attribute} user
:canonical: libweasyl.models.api.APIToken.user
:value: >
   'relationship(...)'

```{autodoc2-docstring} libweasyl.models.api.APIToken.user
```

````

`````

`````{py:class} OAuthConsumer
:canonical: libweasyl.models.api.OAuthConsumer

Bases: {py:obj}`libweasyl.models.meta.Base`

```{autodoc2-docstring} libweasyl.models.api.OAuthConsumer
```

````{py:attribute} __table__
:canonical: libweasyl.models.api.OAuthConsumer.__table__
:value: >
   None

```{autodoc2-docstring} libweasyl.models.api.OAuthConsumer.__table__
```

````

````{py:attribute} owner
:canonical: libweasyl.models.api.OAuthConsumer.owner
:value: >
   'relationship(...)'

```{autodoc2-docstring} libweasyl.models.api.OAuthConsumer.owner
```

````

````{py:property} client_id
:canonical: libweasyl.models.api.OAuthConsumer.client_id

```{autodoc2-docstring} libweasyl.models.api.OAuthConsumer.client_id
```

````

`````

`````{py:class} OAuthBearerToken
:canonical: libweasyl.models.api.OAuthBearerToken

Bases: {py:obj}`libweasyl.models.meta.Base`

```{autodoc2-docstring} libweasyl.models.api.OAuthBearerToken
```

````{py:attribute} __table__
:canonical: libweasyl.models.api.OAuthBearerToken.__table__
:value: >
   None

```{autodoc2-docstring} libweasyl.models.api.OAuthBearerToken.__table__
```

````

````{py:attribute} user
:canonical: libweasyl.models.api.OAuthBearerToken.user
:value: >
   'relationship(...)'

```{autodoc2-docstring} libweasyl.models.api.OAuthBearerToken.user
```

````

`````
