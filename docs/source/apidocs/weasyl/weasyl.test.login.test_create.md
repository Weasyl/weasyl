# {py:mod}`weasyl.test.login.test_create`

```{py:module} weasyl.test.login.test_create
```

```{autodoc2-docstring} weasyl.test.login.test_create
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`TestAccountCreationBlacklist <weasyl.test.login.test_create.TestAccountCreationBlacklist>`
  - ```{autodoc2-docstring} weasyl.test.login.test_create.TestAccountCreationBlacklist
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`test_age_minimum <weasyl.test.login.test_create.test_age_minimum>`
  - ```{autodoc2-docstring} weasyl.test.login.test_create.test_age_minimum
    :summary:
    ```
* - {py:obj}`test_passwords_must_be_of_sufficient_length <weasyl.test.login.test_create.test_passwords_must_be_of_sufficient_length>`
  - ```{autodoc2-docstring} weasyl.test.login.test_create.test_passwords_must_be_of_sufficient_length
    :summary:
    ```
* - {py:obj}`test_create_fails_if_email_is_invalid <weasyl.test.login.test_create.test_create_fails_if_email_is_invalid>`
  - ```{autodoc2-docstring} weasyl.test.login.test_create.test_create_fails_if_email_is_invalid
    :summary:
    ```
* - {py:obj}`test_create_fails_if_another_account_has_email_linked_to_their_account <weasyl.test.login.test_create.test_create_fails_if_another_account_has_email_linked_to_their_account>`
  - ```{autodoc2-docstring} weasyl.test.login.test_create.test_create_fails_if_another_account_has_email_linked_to_their_account
    :summary:
    ```
* - {py:obj}`test_create_fails_if_pending_account_has_same_email <weasyl.test.login.test_create.test_create_fails_if_pending_account_has_same_email>`
  - ```{autodoc2-docstring} weasyl.test.login.test_create.test_create_fails_if_pending_account_has_same_email
    :summary:
    ```
* - {py:obj}`test_username_cant_be_blank_or_have_semicolon <weasyl.test.login.test_create.test_username_cant_be_blank_or_have_semicolon>`
  - ```{autodoc2-docstring} weasyl.test.login.test_create.test_username_cant_be_blank_or_have_semicolon
    :summary:
    ```
* - {py:obj}`test_create_fails_if_username_is_a_prohibited_name <weasyl.test.login.test_create.test_create_fails_if_username_is_a_prohibited_name>`
  - ```{autodoc2-docstring} weasyl.test.login.test_create.test_create_fails_if_username_is_a_prohibited_name
    :summary:
    ```
* - {py:obj}`test_usernames_must_be_unique <weasyl.test.login.test_create.test_usernames_must_be_unique>`
  - ```{autodoc2-docstring} weasyl.test.login.test_create.test_usernames_must_be_unique
    :summary:
    ```
* - {py:obj}`test_usernames_cannot_match_pending_account_usernames <weasyl.test.login.test_create.test_usernames_cannot_match_pending_account_usernames>`
  - ```{autodoc2-docstring} weasyl.test.login.test_create.test_usernames_cannot_match_pending_account_usernames
    :summary:
    ```
* - {py:obj}`test_username_cannot_match_an_active_alias <weasyl.test.login.test_create.test_username_cannot_match_an_active_alias>`
  - ```{autodoc2-docstring} weasyl.test.login.test_create.test_username_cannot_match_an_active_alias
    :summary:
    ```
* - {py:obj}`test_verify_correct_information_creates_account <weasyl.test.login.test_create.test_verify_correct_information_creates_account>`
  - ```{autodoc2-docstring} weasyl.test.login.test_create.test_verify_correct_information_creates_account
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`user_name <weasyl.test.login.test_create.user_name>`
  - ```{autodoc2-docstring} weasyl.test.login.test_create.user_name
    :summary:
    ```
* - {py:obj}`email_addr <weasyl.test.login.test_create.email_addr>`
  - ```{autodoc2-docstring} weasyl.test.login.test_create.email_addr
    :summary:
    ```
* - {py:obj}`raw_password <weasyl.test.login.test_create.raw_password>`
  - ```{autodoc2-docstring} weasyl.test.login.test_create.raw_password
    :summary:
    ```
````

### API

````{py:data} user_name
:canonical: weasyl.test.login.test_create.user_name
:value: >
   'test'

```{autodoc2-docstring} weasyl.test.login.test_create.user_name
```

````

````{py:data} email_addr
:canonical: weasyl.test.login.test_create.email_addr
:value: >
   'test@weasyl.com'

```{autodoc2-docstring} weasyl.test.login.test_create.email_addr
```

````

````{py:data} raw_password
:canonical: weasyl.test.login.test_create.raw_password
:value: >
   '0123456789'

```{autodoc2-docstring} weasyl.test.login.test_create.raw_password
```

````

````{py:function} test_age_minimum()
:canonical: weasyl.test.login.test_create.test_age_minimum

```{autodoc2-docstring} weasyl.test.login.test_create.test_age_minimum
```
````

````{py:function} test_passwords_must_be_of_sufficient_length()
:canonical: weasyl.test.login.test_create.test_passwords_must_be_of_sufficient_length

```{autodoc2-docstring} weasyl.test.login.test_create.test_passwords_must_be_of_sufficient_length
```
````

````{py:function} test_create_fails_if_email_is_invalid()
:canonical: weasyl.test.login.test_create.test_create_fails_if_email_is_invalid

```{autodoc2-docstring} weasyl.test.login.test_create.test_create_fails_if_email_is_invalid
```
````

````{py:function} test_create_fails_if_another_account_has_email_linked_to_their_account()
:canonical: weasyl.test.login.test_create.test_create_fails_if_another_account_has_email_linked_to_their_account

```{autodoc2-docstring} weasyl.test.login.test_create.test_create_fails_if_another_account_has_email_linked_to_their_account
```
````

````{py:function} test_create_fails_if_pending_account_has_same_email()
:canonical: weasyl.test.login.test_create.test_create_fails_if_pending_account_has_same_email

```{autodoc2-docstring} weasyl.test.login.test_create.test_create_fails_if_pending_account_has_same_email
```
````

````{py:function} test_username_cant_be_blank_or_have_semicolon()
:canonical: weasyl.test.login.test_create.test_username_cant_be_blank_or_have_semicolon

```{autodoc2-docstring} weasyl.test.login.test_create.test_username_cant_be_blank_or_have_semicolon
```
````

````{py:function} test_create_fails_if_username_is_a_prohibited_name()
:canonical: weasyl.test.login.test_create.test_create_fails_if_username_is_a_prohibited_name

```{autodoc2-docstring} weasyl.test.login.test_create.test_create_fails_if_username_is_a_prohibited_name
```
````

````{py:function} test_usernames_must_be_unique()
:canonical: weasyl.test.login.test_create.test_usernames_must_be_unique

```{autodoc2-docstring} weasyl.test.login.test_create.test_usernames_must_be_unique
```
````

````{py:function} test_usernames_cannot_match_pending_account_usernames()
:canonical: weasyl.test.login.test_create.test_usernames_cannot_match_pending_account_usernames

```{autodoc2-docstring} weasyl.test.login.test_create.test_usernames_cannot_match_pending_account_usernames
```
````

````{py:function} test_username_cannot_match_an_active_alias()
:canonical: weasyl.test.login.test_create.test_username_cannot_match_an_active_alias

```{autodoc2-docstring} weasyl.test.login.test_create.test_username_cannot_match_an_active_alias
```
````

````{py:function} test_verify_correct_information_creates_account()
:canonical: weasyl.test.login.test_create.test_verify_correct_information_creates_account

```{autodoc2-docstring} weasyl.test.login.test_create.test_verify_correct_information_creates_account
```
````

`````{py:class} TestAccountCreationBlacklist
:canonical: weasyl.test.login.test_create.TestAccountCreationBlacklist

```{autodoc2-docstring} weasyl.test.login.test_create.TestAccountCreationBlacklist
```

````{py:method} test_create_fails_if_email_domain_is_blacklisted()
:canonical: weasyl.test.login.test_create.TestAccountCreationBlacklist.test_create_fails_if_email_domain_is_blacklisted

```{autodoc2-docstring} weasyl.test.login.test_create.TestAccountCreationBlacklist.test_create_fails_if_email_domain_is_blacklisted
```

````

````{py:method} test_verify_subdomains_of_blocked_sites_blocked()
:canonical: weasyl.test.login.test_create.TestAccountCreationBlacklist.test_verify_subdomains_of_blocked_sites_blocked

```{autodoc2-docstring} weasyl.test.login.test_create.TestAccountCreationBlacklist.test_verify_subdomains_of_blocked_sites_blocked
```

````

````{py:method} test_similarly_named_domains_are_not_blocked()
:canonical: weasyl.test.login.test_create.TestAccountCreationBlacklist.test_similarly_named_domains_are_not_blocked

```{autodoc2-docstring} weasyl.test.login.test_create.TestAccountCreationBlacklist.test_similarly_named_domains_are_not_blocked
```

````

`````
