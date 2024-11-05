# {py:mod}`weasyl.login`

```{py:module} weasyl.login
```

```{autodoc2-docstring} weasyl.login
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`clean_display_name <weasyl.login.clean_display_name>`
  - ```{autodoc2-docstring} weasyl.login.clean_display_name
    :summary:
    ```
* - {py:obj}`signin <weasyl.login.signin>`
  - ```{autodoc2-docstring} weasyl.login.signin
    :summary:
    ```
* - {py:obj}`get_user_agent_id <weasyl.login.get_user_agent_id>`
  - ```{autodoc2-docstring} weasyl.login.get_user_agent_id
    :summary:
    ```
* - {py:obj}`signout <weasyl.login.signout>`
  - ```{autodoc2-docstring} weasyl.login.signout
    :summary:
    ```
* - {py:obj}`authenticate_bcrypt <weasyl.login.authenticate_bcrypt>`
  - ```{autodoc2-docstring} weasyl.login.authenticate_bcrypt
    :summary:
    ```
* - {py:obj}`passhash <weasyl.login.passhash>`
  - ```{autodoc2-docstring} weasyl.login.passhash
    :summary:
    ```
* - {py:obj}`password_secure <weasyl.login.password_secure>`
  - ```{autodoc2-docstring} weasyl.login.password_secure
    :summary:
    ```
* - {py:obj}`_delete_expired <weasyl.login._delete_expired>`
  - ```{autodoc2-docstring} weasyl.login._delete_expired
    :summary:
    ```
* - {py:obj}`create <weasyl.login.create>`
  - ```{autodoc2-docstring} weasyl.login.create
    :summary:
    ```
* - {py:obj}`verify <weasyl.login.verify>`
  - ```{autodoc2-docstring} weasyl.login.verify
    :summary:
    ```
* - {py:obj}`email_exists <weasyl.login.email_exists>`
  - ```{autodoc2-docstring} weasyl.login.email_exists
    :summary:
    ```
* - {py:obj}`username_exists <weasyl.login.username_exists>`
  - ```{autodoc2-docstring} weasyl.login.username_exists
    :summary:
    ```
* - {py:obj}`release_username <weasyl.login.release_username>`
  - ```{autodoc2-docstring} weasyl.login.release_username
    :summary:
    ```
* - {py:obj}`change_username <weasyl.login.change_username>`
  - ```{autodoc2-docstring} weasyl.login.change_username
    :summary:
    ```
* - {py:obj}`get_account_verification_token <weasyl.login.get_account_verification_token>`
  - ```{autodoc2-docstring} weasyl.login.get_account_verification_token
    :summary:
    ```
* - {py:obj}`is_email_blacklisted <weasyl.login.is_email_blacklisted>`
  - ```{autodoc2-docstring} weasyl.login.is_email_blacklisted
    :summary:
    ```
* - {py:obj}`authenticate_account_change <weasyl.login.authenticate_account_change>`
  - ```{autodoc2-docstring} weasyl.login.authenticate_account_change
    :summary:
    ```
* - {py:obj}`verify_email_change <weasyl.login.verify_email_change>`
  - ```{autodoc2-docstring} weasyl.login.verify_email_change
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_EMAIL <weasyl.login._EMAIL>`
  - ```{autodoc2-docstring} weasyl.login._EMAIL
    :summary:
    ```
* - {py:obj}`_PASSWORD <weasyl.login._PASSWORD>`
  - ```{autodoc2-docstring} weasyl.login._PASSWORD
    :summary:
    ```
* - {py:obj}`_USERNAME <weasyl.login._USERNAME>`
  - ```{autodoc2-docstring} weasyl.login._USERNAME
    :summary:
    ```
* - {py:obj}`_BANNED_SYSNAMES <weasyl.login._BANNED_SYSNAMES>`
  - ```{autodoc2-docstring} weasyl.login._BANNED_SYSNAMES
    :summary:
    ```
````

### API

````{py:data} _EMAIL
:canonical: weasyl.login._EMAIL
:value: >
   100

```{autodoc2-docstring} weasyl.login._EMAIL
```

````

````{py:data} _PASSWORD
:canonical: weasyl.login._PASSWORD
:value: >
   10

```{autodoc2-docstring} weasyl.login._PASSWORD
```

````

````{py:data} _USERNAME
:canonical: weasyl.login._USERNAME
:value: >
   25

```{autodoc2-docstring} weasyl.login._USERNAME
```

````

````{py:data} _BANNED_SYSNAMES
:canonical: weasyl.login._BANNED_SYSNAMES
:value: >
   'frozenset(...)'

```{autodoc2-docstring} weasyl.login._BANNED_SYSNAMES
```

````

````{py:function} clean_display_name(text)
:canonical: weasyl.login.clean_display_name

```{autodoc2-docstring} weasyl.login.clean_display_name
```
````

````{py:function} signin(request, userid, ip_address=None, user_agent=None)
:canonical: weasyl.login.signin

```{autodoc2-docstring} weasyl.login.signin
```
````

````{py:function} get_user_agent_id(ua_string=None)
:canonical: weasyl.login.get_user_agent_id

```{autodoc2-docstring} weasyl.login.get_user_agent_id
```
````

````{py:function} signout(request)
:canonical: weasyl.login.signout

```{autodoc2-docstring} weasyl.login.signout
```
````

````{py:function} authenticate_bcrypt(username, password, request, ip_address=None, user_agent=None)
:canonical: weasyl.login.authenticate_bcrypt

```{autodoc2-docstring} weasyl.login.authenticate_bcrypt
```
````

````{py:function} passhash(password)
:canonical: weasyl.login.passhash

```{autodoc2-docstring} weasyl.login.passhash
```
````

````{py:function} password_secure(password)
:canonical: weasyl.login.password_secure

```{autodoc2-docstring} weasyl.login.password_secure
```
````

````{py:function} _delete_expired()
:canonical: weasyl.login._delete_expired

```{autodoc2-docstring} weasyl.login._delete_expired
```
````

````{py:function} create(form)
:canonical: weasyl.login.create

```{autodoc2-docstring} weasyl.login.create
```
````

````{py:function} verify(token, ip_address=None)
:canonical: weasyl.login.verify

```{autodoc2-docstring} weasyl.login.verify
```
````

````{py:function} email_exists(email)
:canonical: weasyl.login.email_exists

```{autodoc2-docstring} weasyl.login.email_exists
```
````

````{py:function} username_exists(login_name)
:canonical: weasyl.login.username_exists

```{autodoc2-docstring} weasyl.login.username_exists
```
````

````{py:function} release_username(db, acting_user, target_user)
:canonical: weasyl.login.release_username

```{autodoc2-docstring} weasyl.login.release_username
```
````

````{py:function} change_username(acting_user, target_user, bypass_limit, new_username)
:canonical: weasyl.login.change_username

```{autodoc2-docstring} weasyl.login.change_username
```
````

````{py:function} get_account_verification_token(email=None, username=None)
:canonical: weasyl.login.get_account_verification_token

```{autodoc2-docstring} weasyl.login.get_account_verification_token
```
````

````{py:function} is_email_blacklisted(address)
:canonical: weasyl.login.is_email_blacklisted

```{autodoc2-docstring} weasyl.login.is_email_blacklisted
```
````

````{py:function} authenticate_account_change(*, userid, password)
:canonical: weasyl.login.authenticate_account_change

```{autodoc2-docstring} weasyl.login.authenticate_account_change
```
````

````{py:function} verify_email_change(userid, token)
:canonical: weasyl.login.verify_email_change

```{autodoc2-docstring} weasyl.login.verify_email_change
```
````
