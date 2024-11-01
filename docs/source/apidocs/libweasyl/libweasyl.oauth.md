# {py:mod}`libweasyl.oauth`

```{py:module} libweasyl.oauth
```

```{autodoc2-docstring} libweasyl.oauth
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`WeasylValidator <libweasyl.oauth.WeasylValidator>`
  - ```{autodoc2-docstring} libweasyl.oauth.WeasylValidator
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`get_consumers_for_user <libweasyl.oauth.get_consumers_for_user>`
  - ```{autodoc2-docstring} libweasyl.oauth.get_consumers_for_user
    :summary:
    ```
* - {py:obj}`revoke_consumers_for_user <libweasyl.oauth.revoke_consumers_for_user>`
  - ```{autodoc2-docstring} libweasyl.oauth.revoke_consumers_for_user
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`validator <libweasyl.oauth.validator>`
  - ```{autodoc2-docstring} libweasyl.oauth.validator
    :summary:
    ```
* - {py:obj}`server <libweasyl.oauth.server>`
  - ```{autodoc2-docstring} libweasyl.oauth.server
    :summary:
    ```
````

### API

`````{py:class} WeasylValidator
:canonical: libweasyl.oauth.WeasylValidator

Bases: {py:obj}`oauthlib.oauth2.RequestValidator`

```{autodoc2-docstring} libweasyl.oauth.WeasylValidator
```

````{py:method} _get_client(client_id)
:canonical: libweasyl.oauth.WeasylValidator._get_client

```{autodoc2-docstring} libweasyl.oauth.WeasylValidator._get_client
```

````

````{py:method} validate_client_id(client_id, request, *a, **kw)
:canonical: libweasyl.oauth.WeasylValidator.validate_client_id

```{autodoc2-docstring} libweasyl.oauth.WeasylValidator.validate_client_id
```

````

````{py:method} validate_redirect_uri(client_id, redirect_uri, request, *args, **kwargs)
:canonical: libweasyl.oauth.WeasylValidator.validate_redirect_uri

```{autodoc2-docstring} libweasyl.oauth.WeasylValidator.validate_redirect_uri
```

````

````{py:method} get_default_redirect_uri(client_id, request, *args, **kwargs)
:canonical: libweasyl.oauth.WeasylValidator.get_default_redirect_uri

```{autodoc2-docstring} libweasyl.oauth.WeasylValidator.get_default_redirect_uri
```

````

````{py:method} validate_scopes(client_id, scopes, client, request, *args, **kwargs)
:canonical: libweasyl.oauth.WeasylValidator.validate_scopes

```{autodoc2-docstring} libweasyl.oauth.WeasylValidator.validate_scopes
```

````

````{py:method} get_default_scopes(client_id, request, *args, **kwargs)
:canonical: libweasyl.oauth.WeasylValidator.get_default_scopes

```{autodoc2-docstring} libweasyl.oauth.WeasylValidator.get_default_scopes
```

````

````{py:method} validate_response_type(client_id, response_type, client, request, *args, **kwargs)
:canonical: libweasyl.oauth.WeasylValidator.validate_response_type

```{autodoc2-docstring} libweasyl.oauth.WeasylValidator.validate_response_type
```

````

````{py:method} cache_key(code)
:canonical: libweasyl.oauth.WeasylValidator.cache_key
:classmethod:

```{autodoc2-docstring} libweasyl.oauth.WeasylValidator.cache_key
```

````

````{py:method} save_authorization_code(client_id, code, request, *args, **kwargs)
:canonical: libweasyl.oauth.WeasylValidator.save_authorization_code

```{autodoc2-docstring} libweasyl.oauth.WeasylValidator.save_authorization_code
```

````

````{py:method} authenticate_client(request, *args, **kwargs)
:canonical: libweasyl.oauth.WeasylValidator.authenticate_client

```{autodoc2-docstring} libweasyl.oauth.WeasylValidator.authenticate_client
```

````

````{py:method} authenticate_client_id(client_id, request, *args, **kwargs)
:canonical: libweasyl.oauth.WeasylValidator.authenticate_client_id

```{autodoc2-docstring} libweasyl.oauth.WeasylValidator.authenticate_client_id
```

````

````{py:method} validate_code(client_id, code, client, request, *args, **kwargs)
:canonical: libweasyl.oauth.WeasylValidator.validate_code

```{autodoc2-docstring} libweasyl.oauth.WeasylValidator.validate_code
```

````

````{py:method} confirm_redirect_uri(client_id, code, redirect_uri, client, *args, **kwargs)
:canonical: libweasyl.oauth.WeasylValidator.confirm_redirect_uri

```{autodoc2-docstring} libweasyl.oauth.WeasylValidator.confirm_redirect_uri
```

````

````{py:method} validate_grant_type(client_id, grant_type, client, request, *args, **kwargs)
:canonical: libweasyl.oauth.WeasylValidator.validate_grant_type

```{autodoc2-docstring} libweasyl.oauth.WeasylValidator.validate_grant_type
```

````

````{py:method} save_bearer_token(token, request, *args, **kwargs)
:canonical: libweasyl.oauth.WeasylValidator.save_bearer_token

```{autodoc2-docstring} libweasyl.oauth.WeasylValidator.save_bearer_token
```

````

````{py:method} invalidate_authorization_code(client_id, code, request, *args, **kwargs)
:canonical: libweasyl.oauth.WeasylValidator.invalidate_authorization_code

```{autodoc2-docstring} libweasyl.oauth.WeasylValidator.invalidate_authorization_code
```

````

````{py:method} _get_bearer(**kw)
:canonical: libweasyl.oauth.WeasylValidator._get_bearer

```{autodoc2-docstring} libweasyl.oauth.WeasylValidator._get_bearer
```

````

````{py:method} validate_bearer_token(token, scopes, request)
:canonical: libweasyl.oauth.WeasylValidator.validate_bearer_token

```{autodoc2-docstring} libweasyl.oauth.WeasylValidator.validate_bearer_token
```

````

````{py:method} validate_refresh_token(refresh_token, client, request, *args, **kwargs)
:canonical: libweasyl.oauth.WeasylValidator.validate_refresh_token

```{autodoc2-docstring} libweasyl.oauth.WeasylValidator.validate_refresh_token
```

````

````{py:method} get_original_scopes(refresh_token, request, *args, **kwargs)
:canonical: libweasyl.oauth.WeasylValidator.get_original_scopes

```{autodoc2-docstring} libweasyl.oauth.WeasylValidator.get_original_scopes
```

````

`````

````{py:data} validator
:canonical: libweasyl.oauth.validator
:value: >
   'WeasylValidator(...)'

```{autodoc2-docstring} libweasyl.oauth.validator
```

````

````{py:data} server
:canonical: libweasyl.oauth.server
:value: >
   'WebApplicationServer(...)'

```{autodoc2-docstring} libweasyl.oauth.server
```

````

````{py:function} get_consumers_for_user(userid)
:canonical: libweasyl.oauth.get_consumers_for_user

```{autodoc2-docstring} libweasyl.oauth.get_consumers_for_user
```
````

````{py:function} revoke_consumers_for_user(userid, clientids)
:canonical: libweasyl.oauth.revoke_consumers_for_user

```{autodoc2-docstring} libweasyl.oauth.revoke_consumers_for_user
```
````
