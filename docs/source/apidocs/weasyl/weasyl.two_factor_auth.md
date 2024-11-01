# {py:mod}`weasyl.two_factor_auth`

```{py:module} weasyl.two_factor_auth
```

```{autodoc2-docstring} weasyl.two_factor_auth
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_encrypt_totp_secret <weasyl.two_factor_auth._encrypt_totp_secret>`
  - ```{autodoc2-docstring} weasyl.two_factor_auth._encrypt_totp_secret
    :summary:
    ```
* - {py:obj}`_decrypt_totp_secret <weasyl.two_factor_auth._decrypt_totp_secret>`
  - ```{autodoc2-docstring} weasyl.two_factor_auth._decrypt_totp_secret
    :summary:
    ```
* - {py:obj}`init <weasyl.two_factor_auth.init>`
  - ```{autodoc2-docstring} weasyl.two_factor_auth.init
    :summary:
    ```
* - {py:obj}`generate_tfa_qrcode <weasyl.two_factor_auth.generate_tfa_qrcode>`
  - ```{autodoc2-docstring} weasyl.two_factor_auth.generate_tfa_qrcode
    :summary:
    ```
* - {py:obj}`init_verify_tfa <weasyl.two_factor_auth.init_verify_tfa>`
  - ```{autodoc2-docstring} weasyl.two_factor_auth.init_verify_tfa
    :summary:
    ```
* - {py:obj}`activate <weasyl.two_factor_auth.activate>`
  - ```{autodoc2-docstring} weasyl.two_factor_auth.activate
    :summary:
    ```
* - {py:obj}`verify <weasyl.two_factor_auth.verify>`
  - ```{autodoc2-docstring} weasyl.two_factor_auth.verify
    :summary:
    ```
* - {py:obj}`get_number_of_recovery_codes <weasyl.two_factor_auth.get_number_of_recovery_codes>`
  - ```{autodoc2-docstring} weasyl.two_factor_auth.get_number_of_recovery_codes
    :summary:
    ```
* - {py:obj}`generate_recovery_codes <weasyl.two_factor_auth.generate_recovery_codes>`
  - ```{autodoc2-docstring} weasyl.two_factor_auth.generate_recovery_codes
    :summary:
    ```
* - {py:obj}`store_recovery_codes <weasyl.two_factor_auth.store_recovery_codes>`
  - ```{autodoc2-docstring} weasyl.two_factor_auth.store_recovery_codes
    :summary:
    ```
* - {py:obj}`is_recovery_code_valid <weasyl.two_factor_auth.is_recovery_code_valid>`
  - ```{autodoc2-docstring} weasyl.two_factor_auth.is_recovery_code_valid
    :summary:
    ```
* - {py:obj}`is_2fa_enabled <weasyl.two_factor_auth.is_2fa_enabled>`
  - ```{autodoc2-docstring} weasyl.two_factor_auth.is_2fa_enabled
    :summary:
    ```
* - {py:obj}`deactivate <weasyl.two_factor_auth.deactivate>`
  - ```{autodoc2-docstring} weasyl.two_factor_auth.deactivate
    :summary:
    ```
* - {py:obj}`force_deactivate <weasyl.two_factor_auth.force_deactivate>`
  - ```{autodoc2-docstring} weasyl.two_factor_auth.force_deactivate
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_TFA_RECOVERY_CODES <weasyl.two_factor_auth._TFA_RECOVERY_CODES>`
  - ```{autodoc2-docstring} weasyl.two_factor_auth._TFA_RECOVERY_CODES
    :summary:
    ```
* - {py:obj}`BCRYPT_WORK_FACTOR <weasyl.two_factor_auth.BCRYPT_WORK_FACTOR>`
  - ```{autodoc2-docstring} weasyl.two_factor_auth.BCRYPT_WORK_FACTOR
    :summary:
    ```
* - {py:obj}`LENGTH_RECOVERY_CODE <weasyl.two_factor_auth.LENGTH_RECOVERY_CODE>`
  - ```{autodoc2-docstring} weasyl.two_factor_auth.LENGTH_RECOVERY_CODE
    :summary:
    ```
* - {py:obj}`LENGTH_TOTP_CODE <weasyl.two_factor_auth.LENGTH_TOTP_CODE>`
  - ```{autodoc2-docstring} weasyl.two_factor_auth.LENGTH_TOTP_CODE
    :summary:
    ```
````

### API

````{py:data} _TFA_RECOVERY_CODES
:canonical: weasyl.two_factor_auth._TFA_RECOVERY_CODES
:value: >
   10

```{autodoc2-docstring} weasyl.two_factor_auth._TFA_RECOVERY_CODES
```

````

````{py:data} BCRYPT_WORK_FACTOR
:canonical: weasyl.two_factor_auth.BCRYPT_WORK_FACTOR
:value: >
   4

```{autodoc2-docstring} weasyl.two_factor_auth.BCRYPT_WORK_FACTOR
```

````

````{py:data} LENGTH_RECOVERY_CODE
:canonical: weasyl.two_factor_auth.LENGTH_RECOVERY_CODE
:value: >
   20

```{autodoc2-docstring} weasyl.two_factor_auth.LENGTH_RECOVERY_CODE
```

````

````{py:data} LENGTH_TOTP_CODE
:canonical: weasyl.two_factor_auth.LENGTH_TOTP_CODE
:value: >
   6

```{autodoc2-docstring} weasyl.two_factor_auth.LENGTH_TOTP_CODE
```

````

````{py:function} _encrypt_totp_secret(totp_secret)
:canonical: weasyl.two_factor_auth._encrypt_totp_secret

```{autodoc2-docstring} weasyl.two_factor_auth._encrypt_totp_secret
```
````

````{py:function} _decrypt_totp_secret(totp_secret)
:canonical: weasyl.two_factor_auth._decrypt_totp_secret

```{autodoc2-docstring} weasyl.two_factor_auth._decrypt_totp_secret
```
````

````{py:function} init(userid)
:canonical: weasyl.two_factor_auth.init

```{autodoc2-docstring} weasyl.two_factor_auth.init
```
````

````{py:function} generate_tfa_qrcode(userid, tfa_secret)
:canonical: weasyl.two_factor_auth.generate_tfa_qrcode

```{autodoc2-docstring} weasyl.two_factor_auth.generate_tfa_qrcode
```
````

````{py:function} init_verify_tfa(tfa_secret, tfa_response)
:canonical: weasyl.two_factor_auth.init_verify_tfa

```{autodoc2-docstring} weasyl.two_factor_auth.init_verify_tfa
```
````

````{py:function} activate(userid, tfa_secret, tfa_response)
:canonical: weasyl.two_factor_auth.activate

```{autodoc2-docstring} weasyl.two_factor_auth.activate
```
````

````{py:function} verify(userid, tfa_response, consume_recovery_code=True)
:canonical: weasyl.two_factor_auth.verify

```{autodoc2-docstring} weasyl.two_factor_auth.verify
```
````

````{py:function} get_number_of_recovery_codes(userid)
:canonical: weasyl.two_factor_auth.get_number_of_recovery_codes

```{autodoc2-docstring} weasyl.two_factor_auth.get_number_of_recovery_codes
```
````

````{py:function} generate_recovery_codes()
:canonical: weasyl.two_factor_auth.generate_recovery_codes

```{autodoc2-docstring} weasyl.two_factor_auth.generate_recovery_codes
```
````

````{py:function} store_recovery_codes(userid, recovery_codes)
:canonical: weasyl.two_factor_auth.store_recovery_codes

```{autodoc2-docstring} weasyl.two_factor_auth.store_recovery_codes
```
````

````{py:function} is_recovery_code_valid(userid, tfa_code, consume_recovery_code=True)
:canonical: weasyl.two_factor_auth.is_recovery_code_valid

```{autodoc2-docstring} weasyl.two_factor_auth.is_recovery_code_valid
```
````

````{py:function} is_2fa_enabled(userid)
:canonical: weasyl.two_factor_auth.is_2fa_enabled

```{autodoc2-docstring} weasyl.two_factor_auth.is_2fa_enabled
```
````

````{py:function} deactivate(userid, tfa_response)
:canonical: weasyl.two_factor_auth.deactivate

```{autodoc2-docstring} weasyl.two_factor_auth.deactivate
```
````

````{py:function} force_deactivate(userid)
:canonical: weasyl.two_factor_auth.force_deactivate

```{autodoc2-docstring} weasyl.two_factor_auth.force_deactivate
```
````
