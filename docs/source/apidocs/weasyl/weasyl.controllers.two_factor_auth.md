# {py:mod}`weasyl.controllers.two_factor_auth`

```{py:module} weasyl.controllers.two_factor_auth
```

```{autodoc2-docstring} weasyl.controllers.two_factor_auth
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_set_totp_code_on_session <weasyl.controllers.two_factor_auth._set_totp_code_on_session>`
  - ```{autodoc2-docstring} weasyl.controllers.two_factor_auth._set_totp_code_on_session
    :summary:
    ```
* - {py:obj}`_get_totp_code_from_session <weasyl.controllers.two_factor_auth._get_totp_code_from_session>`
  - ```{autodoc2-docstring} weasyl.controllers.two_factor_auth._get_totp_code_from_session
    :summary:
    ```
* - {py:obj}`_set_recovery_codes_on_session <weasyl.controllers.two_factor_auth._set_recovery_codes_on_session>`
  - ```{autodoc2-docstring} weasyl.controllers.two_factor_auth._set_recovery_codes_on_session
    :summary:
    ```
* - {py:obj}`_get_recovery_codes_from_session <weasyl.controllers.two_factor_auth._get_recovery_codes_from_session>`
  - ```{autodoc2-docstring} weasyl.controllers.two_factor_auth._get_recovery_codes_from_session
    :summary:
    ```
* - {py:obj}`_cleanup_session <weasyl.controllers.two_factor_auth._cleanup_session>`
  - ```{autodoc2-docstring} weasyl.controllers.two_factor_auth._cleanup_session
    :summary:
    ```
* - {py:obj}`tfa_status_get_ <weasyl.controllers.two_factor_auth.tfa_status_get_>`
  - ```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_status_get_
    :summary:
    ```
* - {py:obj}`tfa_init_get_ <weasyl.controllers.two_factor_auth.tfa_init_get_>`
  - ```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_init_get_
    :summary:
    ```
* - {py:obj}`tfa_init_post_ <weasyl.controllers.two_factor_auth.tfa_init_post_>`
  - ```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_init_post_
    :summary:
    ```
* - {py:obj}`tfa_init_qrcode_get_ <weasyl.controllers.two_factor_auth.tfa_init_qrcode_get_>`
  - ```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_init_qrcode_get_
    :summary:
    ```
* - {py:obj}`tfa_init_qrcode_post_ <weasyl.controllers.two_factor_auth.tfa_init_qrcode_post_>`
  - ```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_init_qrcode_post_
    :summary:
    ```
* - {py:obj}`tfa_init_verify_get_ <weasyl.controllers.two_factor_auth.tfa_init_verify_get_>`
  - ```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_init_verify_get_
    :summary:
    ```
* - {py:obj}`tfa_init_verify_post_ <weasyl.controllers.two_factor_auth.tfa_init_verify_post_>`
  - ```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_init_verify_post_
    :summary:
    ```
* - {py:obj}`tfa_disable_get_ <weasyl.controllers.two_factor_auth.tfa_disable_get_>`
  - ```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_disable_get_
    :summary:
    ```
* - {py:obj}`tfa_disable_post_ <weasyl.controllers.two_factor_auth.tfa_disable_post_>`
  - ```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_disable_post_
    :summary:
    ```
* - {py:obj}`tfa_generate_recovery_codes_verify_password_get_ <weasyl.controllers.two_factor_auth.tfa_generate_recovery_codes_verify_password_get_>`
  - ```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_generate_recovery_codes_verify_password_get_
    :summary:
    ```
* - {py:obj}`tfa_generate_recovery_codes_verify_password_post_ <weasyl.controllers.two_factor_auth.tfa_generate_recovery_codes_verify_password_post_>`
  - ```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_generate_recovery_codes_verify_password_post_
    :summary:
    ```
* - {py:obj}`tfa_generate_recovery_codes_get_ <weasyl.controllers.two_factor_auth.tfa_generate_recovery_codes_get_>`
  - ```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_generate_recovery_codes_get_
    :summary:
    ```
* - {py:obj}`tfa_generate_recovery_codes_post_ <weasyl.controllers.two_factor_auth.tfa_generate_recovery_codes_post_>`
  - ```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_generate_recovery_codes_post_
    :summary:
    ```
````

### API

````{py:function} _set_totp_code_on_session(request, totp_code)
:canonical: weasyl.controllers.two_factor_auth._set_totp_code_on_session

```{autodoc2-docstring} weasyl.controllers.two_factor_auth._set_totp_code_on_session
```
````

````{py:function} _get_totp_code_from_session(request)
:canonical: weasyl.controllers.two_factor_auth._get_totp_code_from_session

```{autodoc2-docstring} weasyl.controllers.two_factor_auth._get_totp_code_from_session
```
````

````{py:function} _set_recovery_codes_on_session(request, recovery_codes)
:canonical: weasyl.controllers.two_factor_auth._set_recovery_codes_on_session

```{autodoc2-docstring} weasyl.controllers.two_factor_auth._set_recovery_codes_on_session
```
````

````{py:function} _get_recovery_codes_from_session(request)
:canonical: weasyl.controllers.two_factor_auth._get_recovery_codes_from_session

```{autodoc2-docstring} weasyl.controllers.two_factor_auth._get_recovery_codes_from_session
```
````

````{py:function} _cleanup_session(request)
:canonical: weasyl.controllers.two_factor_auth._cleanup_session

```{autodoc2-docstring} weasyl.controllers.two_factor_auth._cleanup_session
```
````

````{py:function} tfa_status_get_(request)
:canonical: weasyl.controllers.two_factor_auth.tfa_status_get_

```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_status_get_
```
````

````{py:function} tfa_init_get_(request)
:canonical: weasyl.controllers.two_factor_auth.tfa_init_get_

```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_init_get_
```
````

````{py:function} tfa_init_post_(request)
:canonical: weasyl.controllers.two_factor_auth.tfa_init_post_

```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_init_post_
```
````

````{py:function} tfa_init_qrcode_get_(request)
:canonical: weasyl.controllers.two_factor_auth.tfa_init_qrcode_get_

```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_init_qrcode_get_
```
````

````{py:function} tfa_init_qrcode_post_(request)
:canonical: weasyl.controllers.two_factor_auth.tfa_init_qrcode_post_

```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_init_qrcode_post_
```
````

````{py:function} tfa_init_verify_get_(request)
:canonical: weasyl.controllers.two_factor_auth.tfa_init_verify_get_

```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_init_verify_get_
```
````

````{py:function} tfa_init_verify_post_(request)
:canonical: weasyl.controllers.two_factor_auth.tfa_init_verify_post_

```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_init_verify_post_
```
````

````{py:function} tfa_disable_get_(request)
:canonical: weasyl.controllers.two_factor_auth.tfa_disable_get_

```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_disable_get_
```
````

````{py:function} tfa_disable_post_(request)
:canonical: weasyl.controllers.two_factor_auth.tfa_disable_post_

```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_disable_post_
```
````

````{py:function} tfa_generate_recovery_codes_verify_password_get_(request)
:canonical: weasyl.controllers.two_factor_auth.tfa_generate_recovery_codes_verify_password_get_

```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_generate_recovery_codes_verify_password_get_
```
````

````{py:function} tfa_generate_recovery_codes_verify_password_post_(request)
:canonical: weasyl.controllers.two_factor_auth.tfa_generate_recovery_codes_verify_password_post_

```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_generate_recovery_codes_verify_password_post_
```
````

````{py:function} tfa_generate_recovery_codes_get_(request)
:canonical: weasyl.controllers.two_factor_auth.tfa_generate_recovery_codes_get_

```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_generate_recovery_codes_get_
```
````

````{py:function} tfa_generate_recovery_codes_post_(request)
:canonical: weasyl.controllers.two_factor_auth.tfa_generate_recovery_codes_post_

```{autodoc2-docstring} weasyl.controllers.two_factor_auth.tfa_generate_recovery_codes_post_
```
````
