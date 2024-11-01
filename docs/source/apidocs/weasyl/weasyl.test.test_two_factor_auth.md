# {py:mod}`weasyl.test.test_two_factor_auth`

```{py:module} weasyl.test.test_two_factor_auth
```

```{autodoc2-docstring} weasyl.test.test_two_factor_auth
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_insert_recovery_code <weasyl.test.test_two_factor_auth._insert_recovery_code>`
  - ```{autodoc2-docstring} weasyl.test.test_two_factor_auth._insert_recovery_code
    :summary:
    ```
* - {py:obj}`_insert_2fa_secret <weasyl.test.test_two_factor_auth._insert_2fa_secret>`
  - ```{autodoc2-docstring} weasyl.test.test_two_factor_auth._insert_2fa_secret
    :summary:
    ```
* - {py:obj}`test_get_number_of_recovery_codes <weasyl.test.test_two_factor_auth.test_get_number_of_recovery_codes>`
  - ```{autodoc2-docstring} weasyl.test.test_two_factor_auth.test_get_number_of_recovery_codes
    :summary:
    ```
* - {py:obj}`test_generate_recovery_codes <weasyl.test.test_two_factor_auth.test_generate_recovery_codes>`
  - ```{autodoc2-docstring} weasyl.test.test_two_factor_auth.test_generate_recovery_codes
    :summary:
    ```
* - {py:obj}`test_store_recovery_codes <weasyl.test.test_two_factor_auth.test_store_recovery_codes>`
  - ```{autodoc2-docstring} weasyl.test.test_two_factor_auth.test_store_recovery_codes
    :summary:
    ```
* - {py:obj}`test_is_recovery_code_valid <weasyl.test.test_two_factor_auth.test_is_recovery_code_valid>`
  - ```{autodoc2-docstring} weasyl.test.test_two_factor_auth.test_is_recovery_code_valid
    :summary:
    ```
* - {py:obj}`test_init <weasyl.test.test_two_factor_auth.test_init>`
  - ```{autodoc2-docstring} weasyl.test.test_two_factor_auth.test_init
    :summary:
    ```
* - {py:obj}`test_init_verify_tfa <weasyl.test.test_two_factor_auth.test_init_verify_tfa>`
  - ```{autodoc2-docstring} weasyl.test.test_two_factor_auth.test_init_verify_tfa
    :summary:
    ```
* - {py:obj}`test_activate <weasyl.test.test_two_factor_auth.test_activate>`
  - ```{autodoc2-docstring} weasyl.test.test_two_factor_auth.test_activate
    :summary:
    ```
* - {py:obj}`test_is_2fa_enabled <weasyl.test.test_two_factor_auth.test_is_2fa_enabled>`
  - ```{autodoc2-docstring} weasyl.test.test_two_factor_auth.test_is_2fa_enabled
    :summary:
    ```
* - {py:obj}`test_deactivate <weasyl.test.test_two_factor_auth.test_deactivate>`
  - ```{autodoc2-docstring} weasyl.test.test_two_factor_auth.test_deactivate
    :summary:
    ```
* - {py:obj}`test_force_deactivate <weasyl.test.test_two_factor_auth.test_force_deactivate>`
  - ```{autodoc2-docstring} weasyl.test.test_two_factor_auth.test_force_deactivate
    :summary:
    ```
* - {py:obj}`test_verify <weasyl.test.test_two_factor_auth.test_verify>`
  - ```{autodoc2-docstring} weasyl.test.test_two_factor_auth.test_verify
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`recovery_code <weasyl.test.test_two_factor_auth.recovery_code>`
  - ```{autodoc2-docstring} weasyl.test.test_two_factor_auth.recovery_code
    :summary:
    ```
* - {py:obj}`recovery_code_hashed <weasyl.test.test_two_factor_auth.recovery_code_hashed>`
  - ```{autodoc2-docstring} weasyl.test.test_two_factor_auth.recovery_code_hashed
    :summary:
    ```
````

### API

````{py:data} recovery_code
:canonical: weasyl.test.test_two_factor_auth.recovery_code
:value: >
   None

```{autodoc2-docstring} weasyl.test.test_two_factor_auth.recovery_code
```

````

````{py:data} recovery_code_hashed
:canonical: weasyl.test.test_two_factor_auth.recovery_code_hashed
:value: >
   'decode(...)'

```{autodoc2-docstring} weasyl.test.test_two_factor_auth.recovery_code_hashed
```

````

````{py:function} _insert_recovery_code(userid)
:canonical: weasyl.test.test_two_factor_auth._insert_recovery_code

```{autodoc2-docstring} weasyl.test.test_two_factor_auth._insert_recovery_code
```
````

````{py:function} _insert_2fa_secret(user_id, tfa_secret_encrypted)
:canonical: weasyl.test.test_two_factor_auth._insert_2fa_secret

```{autodoc2-docstring} weasyl.test.test_two_factor_auth._insert_2fa_secret
```
````

````{py:function} test_get_number_of_recovery_codes()
:canonical: weasyl.test.test_two_factor_auth.test_get_number_of_recovery_codes

```{autodoc2-docstring} weasyl.test.test_two_factor_auth.test_get_number_of_recovery_codes
```
````

````{py:function} test_generate_recovery_codes()
:canonical: weasyl.test.test_two_factor_auth.test_generate_recovery_codes

```{autodoc2-docstring} weasyl.test.test_two_factor_auth.test_generate_recovery_codes
```
````

````{py:function} test_store_recovery_codes()
:canonical: weasyl.test.test_two_factor_auth.test_store_recovery_codes

```{autodoc2-docstring} weasyl.test.test_two_factor_auth.test_store_recovery_codes
```
````

````{py:function} test_is_recovery_code_valid()
:canonical: weasyl.test.test_two_factor_auth.test_is_recovery_code_valid

```{autodoc2-docstring} weasyl.test.test_two_factor_auth.test_is_recovery_code_valid
```
````

````{py:function} test_init()
:canonical: weasyl.test.test_two_factor_auth.test_init

```{autodoc2-docstring} weasyl.test.test_two_factor_auth.test_init
```
````

````{py:function} test_init_verify_tfa()
:canonical: weasyl.test.test_two_factor_auth.test_init_verify_tfa

```{autodoc2-docstring} weasyl.test.test_two_factor_auth.test_init_verify_tfa
```
````

````{py:function} test_activate()
:canonical: weasyl.test.test_two_factor_auth.test_activate

```{autodoc2-docstring} weasyl.test.test_two_factor_auth.test_activate
```
````

````{py:function} test_is_2fa_enabled()
:canonical: weasyl.test.test_two_factor_auth.test_is_2fa_enabled

```{autodoc2-docstring} weasyl.test.test_two_factor_auth.test_is_2fa_enabled
```
````

````{py:function} test_deactivate()
:canonical: weasyl.test.test_two_factor_auth.test_deactivate

```{autodoc2-docstring} weasyl.test.test_two_factor_auth.test_deactivate
```
````

````{py:function} test_force_deactivate()
:canonical: weasyl.test.test_two_factor_auth.test_force_deactivate

```{autodoc2-docstring} weasyl.test.test_two_factor_auth.test_force_deactivate
```
````

````{py:function} test_verify()
:canonical: weasyl.test.test_two_factor_auth.test_verify

```{autodoc2-docstring} weasyl.test.test_two_factor_auth.test_verify
```
````
