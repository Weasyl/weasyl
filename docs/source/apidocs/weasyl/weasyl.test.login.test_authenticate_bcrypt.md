# {py:mod}`weasyl.test.login.test_authenticate_bcrypt`

```{py:module} weasyl.test.login.test_authenticate_bcrypt
```

```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`test_login_fails_if_no_username_provided <weasyl.test.login.test_authenticate_bcrypt.test_login_fails_if_no_username_provided>`
  - ```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.test_login_fails_if_no_username_provided
    :summary:
    ```
* - {py:obj}`test_login_fails_if_no_password_provided <weasyl.test.login.test_authenticate_bcrypt.test_login_fails_if_no_password_provided>`
  - ```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.test_login_fails_if_no_password_provided
    :summary:
    ```
* - {py:obj}`test_login_fails_if_incorrect_username_is_provided <weasyl.test.login.test_authenticate_bcrypt.test_login_fails_if_incorrect_username_is_provided>`
  - ```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.test_login_fails_if_incorrect_username_is_provided
    :summary:
    ```
* - {py:obj}`test_login_fails_for_incorrect_credentials <weasyl.test.login.test_authenticate_bcrypt.test_login_fails_for_incorrect_credentials>`
  - ```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.test_login_fails_for_incorrect_credentials
    :summary:
    ```
* - {py:obj}`test_login_fails_for_invalid_auth_and_logs_failure_if_mod_account <weasyl.test.login.test_authenticate_bcrypt.test_login_fails_for_invalid_auth_and_logs_failure_if_mod_account>`
  - ```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.test_login_fails_for_invalid_auth_and_logs_failure_if_mod_account
    :summary:
    ```
* - {py:obj}`test_login_fails_if_user_is_banned <weasyl.test.login.test_authenticate_bcrypt.test_login_fails_if_user_is_banned>`
  - ```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.test_login_fails_if_user_is_banned
    :summary:
    ```
* - {py:obj}`test_login_fails_if_user_is_suspended <weasyl.test.login.test_authenticate_bcrypt.test_login_fails_if_user_is_suspended>`
  - ```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.test_login_fails_if_user_is_suspended
    :summary:
    ```
* - {py:obj}`test_login_succeeds_if_suspension_duration_has_expired <weasyl.test.login.test_authenticate_bcrypt.test_login_succeeds_if_suspension_duration_has_expired>`
  - ```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.test_login_succeeds_if_suspension_duration_has_expired
    :summary:
    ```
* - {py:obj}`test_login_succeeds_for_valid_username_and_password <weasyl.test.login.test_authenticate_bcrypt.test_login_succeeds_for_valid_username_and_password>`
  - ```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.test_login_succeeds_for_valid_username_and_password
    :summary:
    ```
* - {py:obj}`test_unicode_password <weasyl.test.login.test_authenticate_bcrypt.test_unicode_password>`
  - ```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.test_unicode_password
    :summary:
    ```
* - {py:obj}`test_unicode_attempts <weasyl.test.login.test_authenticate_bcrypt.test_unicode_attempts>`
  - ```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.test_unicode_attempts
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`user_name <weasyl.test.login.test_authenticate_bcrypt.user_name>`
  - ```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.user_name
    :summary:
    ```
* - {py:obj}`raw_password <weasyl.test.login.test_authenticate_bcrypt.raw_password>`
  - ```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.raw_password
    :summary:
    ```
````

### API

````{py:data} user_name
:canonical: weasyl.test.login.test_authenticate_bcrypt.user_name
:value: >
   'test'

```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.user_name
```

````

````{py:data} raw_password
:canonical: weasyl.test.login.test_authenticate_bcrypt.raw_password
:value: >
   '0123456789'

```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.raw_password
```

````

````{py:function} test_login_fails_if_no_username_provided()
:canonical: weasyl.test.login.test_authenticate_bcrypt.test_login_fails_if_no_username_provided

```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.test_login_fails_if_no_username_provided
```
````

````{py:function} test_login_fails_if_no_password_provided()
:canonical: weasyl.test.login.test_authenticate_bcrypt.test_login_fails_if_no_password_provided

```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.test_login_fails_if_no_password_provided
```
````

````{py:function} test_login_fails_if_incorrect_username_is_provided()
:canonical: weasyl.test.login.test_authenticate_bcrypt.test_login_fails_if_incorrect_username_is_provided

```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.test_login_fails_if_incorrect_username_is_provided
```
````

````{py:function} test_login_fails_for_incorrect_credentials()
:canonical: weasyl.test.login.test_authenticate_bcrypt.test_login_fails_for_incorrect_credentials

```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.test_login_fails_for_incorrect_credentials
```
````

````{py:function} test_login_fails_for_invalid_auth_and_logs_failure_if_mod_account(tmp_path, monkeypatch)
:canonical: weasyl.test.login.test_authenticate_bcrypt.test_login_fails_for_invalid_auth_and_logs_failure_if_mod_account

```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.test_login_fails_for_invalid_auth_and_logs_failure_if_mod_account
```
````

````{py:function} test_login_fails_if_user_is_banned()
:canonical: weasyl.test.login.test_authenticate_bcrypt.test_login_fails_if_user_is_banned

```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.test_login_fails_if_user_is_banned
```
````

````{py:function} test_login_fails_if_user_is_suspended()
:canonical: weasyl.test.login.test_authenticate_bcrypt.test_login_fails_if_user_is_suspended

```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.test_login_fails_if_user_is_suspended
```
````

````{py:function} test_login_succeeds_if_suspension_duration_has_expired()
:canonical: weasyl.test.login.test_authenticate_bcrypt.test_login_succeeds_if_suspension_duration_has_expired

```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.test_login_succeeds_if_suspension_duration_has_expired
```
````

````{py:function} test_login_succeeds_for_valid_username_and_password()
:canonical: weasyl.test.login.test_authenticate_bcrypt.test_login_succeeds_for_valid_username_and_password

```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.test_login_succeeds_for_valid_username_and_password
```
````

````{py:function} test_unicode_password()
:canonical: weasyl.test.login.test_authenticate_bcrypt.test_unicode_password

```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.test_unicode_password
```
````

````{py:function} test_unicode_attempts()
:canonical: weasyl.test.login.test_authenticate_bcrypt.test_unicode_attempts

```{autodoc2-docstring} weasyl.test.login.test_authenticate_bcrypt.test_unicode_attempts
```
````
