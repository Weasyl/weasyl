# {py:mod}`weasyl.oauth2`

```{py:module} weasyl.oauth2
```

```{autodoc2-docstring} weasyl.oauth2
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`OAuthResponse <weasyl.oauth2.OAuthResponse>`
  - ```{autodoc2-docstring} weasyl.oauth2.OAuthResponse
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`extract_params <weasyl.oauth2.extract_params>`
  - ```{autodoc2-docstring} weasyl.oauth2.extract_params
    :summary:
    ```
* - {py:obj}`render_form <weasyl.oauth2.render_form>`
  - ```{autodoc2-docstring} weasyl.oauth2.render_form
    :summary:
    ```
* - {py:obj}`authorize_get_ <weasyl.oauth2.authorize_get_>`
  - ```{autodoc2-docstring} weasyl.oauth2.authorize_get_
    :summary:
    ```
* - {py:obj}`authorize_post_ <weasyl.oauth2.authorize_post_>`
  - ```{autodoc2-docstring} weasyl.oauth2.authorize_post_
    :summary:
    ```
* - {py:obj}`token_ <weasyl.oauth2.token_>`
  - ```{autodoc2-docstring} weasyl.oauth2.token_
    :summary:
    ```
* - {py:obj}`get_userid_from_authorization <weasyl.oauth2.get_userid_from_authorization>`
  - ```{autodoc2-docstring} weasyl.oauth2.get_userid_from_authorization
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <weasyl.oauth2.__all__>`
  - ```{autodoc2-docstring} weasyl.oauth2.__all__
    :summary:
    ```
````

### API

````{py:class} OAuthResponse(headers, body, status)
:canonical: weasyl.oauth2.OAuthResponse

Bases: {py:obj}`pyramid.response.Response`

```{autodoc2-docstring} weasyl.oauth2.OAuthResponse
```

```{rubric} Initialization
```

```{autodoc2-docstring} weasyl.oauth2.OAuthResponse.__init__
```

````

````{py:function} extract_params(request)
:canonical: weasyl.oauth2.extract_params

```{autodoc2-docstring} weasyl.oauth2.extract_params
```
````

````{py:function} render_form(request, scopes, credentials, mobile, error=None, username='', password='', remember_me=False, not_me=False)
:canonical: weasyl.oauth2.render_form

```{autodoc2-docstring} weasyl.oauth2.render_form
```
````

````{py:function} authorize_get_(request)
:canonical: weasyl.oauth2.authorize_get_

```{autodoc2-docstring} weasyl.oauth2.authorize_get_
```
````

````{py:function} authorize_post_(request)
:canonical: weasyl.oauth2.authorize_post_

```{autodoc2-docstring} weasyl.oauth2.authorize_post_
```
````

````{py:function} token_(request)
:canonical: weasyl.oauth2.token_

```{autodoc2-docstring} weasyl.oauth2.token_
```
````

````{py:function} get_userid_from_authorization(request, scopes=['wholesite'])
:canonical: weasyl.oauth2.get_userid_from_authorization

```{autodoc2-docstring} weasyl.oauth2.get_userid_from_authorization
```
````

````{py:data} __all__
:canonical: weasyl.oauth2.__all__
:value: >
   ['get_consumers_for_user', 'revoke_consumers_for_user', 'get_userid_from_authorization']

```{autodoc2-docstring} weasyl.oauth2.__all__
```

````
