# {py:mod}`weasyl.controllers.api`

```{py:module} weasyl.controllers.api
```

```{autodoc2-docstring} weasyl.controllers.api
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`api_method <weasyl.controllers.api.api_method>`
  - ```{autodoc2-docstring} weasyl.controllers.api.api_method
    :summary:
    ```
* - {py:obj}`api_login_required <weasyl.controllers.api.api_login_required>`
  - ```{autodoc2-docstring} weasyl.controllers.api.api_login_required
    :summary:
    ```
* - {py:obj}`api_useravatar_ <weasyl.controllers.api.api_useravatar_>`
  - ```{autodoc2-docstring} weasyl.controllers.api.api_useravatar_
    :summary:
    ```
* - {py:obj}`api_whoami_ <weasyl.controllers.api.api_whoami_>`
  - ```{autodoc2-docstring} weasyl.controllers.api.api_whoami_
    :summary:
    ```
* - {py:obj}`api_version_ <weasyl.controllers.api.api_version_>`
  - ```{autodoc2-docstring} weasyl.controllers.api.api_version_
    :summary:
    ```
* - {py:obj}`tidy_submission <weasyl.controllers.api.tidy_submission>`
  - ```{autodoc2-docstring} weasyl.controllers.api.tidy_submission
    :summary:
    ```
* - {py:obj}`api_frontpage_ <weasyl.controllers.api.api_frontpage_>`
  - ```{autodoc2-docstring} weasyl.controllers.api.api_frontpage_
    :summary:
    ```
* - {py:obj}`api_submission_view_ <weasyl.controllers.api.api_submission_view_>`
  - ```{autodoc2-docstring} weasyl.controllers.api.api_submission_view_
    :summary:
    ```
* - {py:obj}`api_journal_view_ <weasyl.controllers.api.api_journal_view_>`
  - ```{autodoc2-docstring} weasyl.controllers.api.api_journal_view_
    :summary:
    ```
* - {py:obj}`api_character_view_ <weasyl.controllers.api.api_character_view_>`
  - ```{autodoc2-docstring} weasyl.controllers.api.api_character_view_
    :summary:
    ```
* - {py:obj}`api_user_view_ <weasyl.controllers.api.api_user_view_>`
  - ```{autodoc2-docstring} weasyl.controllers.api.api_user_view_
    :summary:
    ```
* - {py:obj}`api_user_gallery_ <weasyl.controllers.api.api_user_gallery_>`
  - ```{autodoc2-docstring} weasyl.controllers.api.api_user_gallery_
    :summary:
    ```
* - {py:obj}`api_messages_submissions_ <weasyl.controllers.api.api_messages_submissions_>`
  - ```{autodoc2-docstring} weasyl.controllers.api.api_messages_submissions_
    :summary:
    ```
* - {py:obj}`api_messages_summary_ <weasyl.controllers.api.api_messages_summary_>`
  - ```{autodoc2-docstring} weasyl.controllers.api.api_messages_summary_
    :summary:
    ```
* - {py:obj}`api_favorite_ <weasyl.controllers.api.api_favorite_>`
  - ```{autodoc2-docstring} weasyl.controllers.api.api_favorite_
    :summary:
    ```
* - {py:obj}`api_unfavorite_ <weasyl.controllers.api.api_unfavorite_>`
  - ```{autodoc2-docstring} weasyl.controllers.api.api_unfavorite_
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_ERROR_UNEXPECTED <weasyl.controllers.api._ERROR_UNEXPECTED>`
  - ```{autodoc2-docstring} weasyl.controllers.api._ERROR_UNEXPECTED
    :summary:
    ```
* - {py:obj}`_ERROR_UNSIGNED <weasyl.controllers.api._ERROR_UNSIGNED>`
  - ```{autodoc2-docstring} weasyl.controllers.api._ERROR_UNSIGNED
    :summary:
    ```
* - {py:obj}`_ERROR_SITE_STATUS <weasyl.controllers.api._ERROR_SITE_STATUS>`
  - ```{autodoc2-docstring} weasyl.controllers.api._ERROR_SITE_STATUS
    :summary:
    ```
* - {py:obj}`_ERROR_PERMISSION <weasyl.controllers.api._ERROR_PERMISSION>`
  - ```{autodoc2-docstring} weasyl.controllers.api._ERROR_PERMISSION
    :summary:
    ```
* - {py:obj}`_CONTENT_IDS <weasyl.controllers.api._CONTENT_IDS>`
  - ```{autodoc2-docstring} weasyl.controllers.api._CONTENT_IDS
    :summary:
    ```
* - {py:obj}`_STANDARD_WWW_AUTHENTICATE <weasyl.controllers.api._STANDARD_WWW_AUTHENTICATE>`
  - ```{autodoc2-docstring} weasyl.controllers.api._STANDARD_WWW_AUTHENTICATE
    :summary:
    ```
````

### API

````{py:data} _ERROR_UNEXPECTED
:canonical: weasyl.controllers.api._ERROR_UNEXPECTED
:value: >
   None

```{autodoc2-docstring} weasyl.controllers.api._ERROR_UNEXPECTED
```

````

````{py:data} _ERROR_UNSIGNED
:canonical: weasyl.controllers.api._ERROR_UNSIGNED
:value: >
   None

```{autodoc2-docstring} weasyl.controllers.api._ERROR_UNSIGNED
```

````

````{py:data} _ERROR_SITE_STATUS
:canonical: weasyl.controllers.api._ERROR_SITE_STATUS
:value: >
   None

```{autodoc2-docstring} weasyl.controllers.api._ERROR_SITE_STATUS
```

````

````{py:data} _ERROR_PERMISSION
:canonical: weasyl.controllers.api._ERROR_PERMISSION
:value: >
   None

```{autodoc2-docstring} weasyl.controllers.api._ERROR_PERMISSION
```

````

````{py:data} _CONTENT_IDS
:canonical: weasyl.controllers.api._CONTENT_IDS
:value: >
   None

```{autodoc2-docstring} weasyl.controllers.api._CONTENT_IDS
```

````

````{py:function} api_method(view_callable)
:canonical: weasyl.controllers.api.api_method

```{autodoc2-docstring} weasyl.controllers.api.api_method
```
````

````{py:data} _STANDARD_WWW_AUTHENTICATE
:canonical: weasyl.controllers.api._STANDARD_WWW_AUTHENTICATE
:value: >
   'Bearer realm="Weasyl", Weasyl-API-Key realm="Weasyl"'

```{autodoc2-docstring} weasyl.controllers.api._STANDARD_WWW_AUTHENTICATE
```

````

````{py:function} api_login_required(view_callable)
:canonical: weasyl.controllers.api.api_login_required

```{autodoc2-docstring} weasyl.controllers.api.api_login_required
```
````

````{py:function} api_useravatar_(request)
:canonical: weasyl.controllers.api.api_useravatar_

```{autodoc2-docstring} weasyl.controllers.api.api_useravatar_
```
````

````{py:function} api_whoami_(request)
:canonical: weasyl.controllers.api.api_whoami_

```{autodoc2-docstring} weasyl.controllers.api.api_whoami_
```
````

````{py:function} api_version_(request)
:canonical: weasyl.controllers.api.api_version_

```{autodoc2-docstring} weasyl.controllers.api.api_version_
```
````

````{py:function} tidy_submission(submission)
:canonical: weasyl.controllers.api.tidy_submission

```{autodoc2-docstring} weasyl.controllers.api.tidy_submission
```
````

````{py:function} api_frontpage_(request)
:canonical: weasyl.controllers.api.api_frontpage_

```{autodoc2-docstring} weasyl.controllers.api.api_frontpage_
```
````

````{py:function} api_submission_view_(request)
:canonical: weasyl.controllers.api.api_submission_view_

```{autodoc2-docstring} weasyl.controllers.api.api_submission_view_
```
````

````{py:function} api_journal_view_(request)
:canonical: weasyl.controllers.api.api_journal_view_

```{autodoc2-docstring} weasyl.controllers.api.api_journal_view_
```
````

````{py:function} api_character_view_(request)
:canonical: weasyl.controllers.api.api_character_view_

```{autodoc2-docstring} weasyl.controllers.api.api_character_view_
```
````

````{py:function} api_user_view_(request)
:canonical: weasyl.controllers.api.api_user_view_

```{autodoc2-docstring} weasyl.controllers.api.api_user_view_
```
````

````{py:function} api_user_gallery_(request)
:canonical: weasyl.controllers.api.api_user_gallery_

```{autodoc2-docstring} weasyl.controllers.api.api_user_gallery_
```
````

````{py:function} api_messages_submissions_(request)
:canonical: weasyl.controllers.api.api_messages_submissions_

```{autodoc2-docstring} weasyl.controllers.api.api_messages_submissions_
```
````

````{py:function} api_messages_summary_(request)
:canonical: weasyl.controllers.api.api_messages_summary_

```{autodoc2-docstring} weasyl.controllers.api.api_messages_summary_
```
````

````{py:function} api_favorite_(request)
:canonical: weasyl.controllers.api.api_favorite_

```{autodoc2-docstring} weasyl.controllers.api.api_favorite_
```
````

````{py:function} api_unfavorite_(request)
:canonical: weasyl.controllers.api.api_unfavorite_

```{autodoc2-docstring} weasyl.controllers.api.api_unfavorite_
```
````
