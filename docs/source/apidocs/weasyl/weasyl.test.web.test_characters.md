# {py:mod}`weasyl.test.web.test_characters`

```{py:module} weasyl.test.web.test_characters
```

```{autodoc2-docstring} weasyl.test.web.test_characters
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_read_character_image <weasyl.test.web.test_characters._read_character_image>`
  - ```{autodoc2-docstring} weasyl.test.web.test_characters._read_character_image
    :summary:
    ```
* - {py:obj}`_character_user <weasyl.test.web.test_characters._character_user>`
  - ```{autodoc2-docstring} weasyl.test.web.test_characters._character_user
    :summary:
    ```
* - {py:obj}`create_character <weasyl.test.web.test_characters.create_character>`
  - ```{autodoc2-docstring} weasyl.test.web.test_characters.create_character
    :summary:
    ```
* - {py:obj}`_character <weasyl.test.web.test_characters._character>`
  - ```{autodoc2-docstring} weasyl.test.web.test_characters._character
    :summary:
    ```
* - {py:obj}`test_list_empty <weasyl.test.web.test_characters.test_list_empty>`
  - ```{autodoc2-docstring} weasyl.test.web.test_characters.test_list_empty
    :summary:
    ```
* - {py:obj}`test_create_default_thumbnail <weasyl.test.web.test_characters.test_create_default_thumbnail>`
  - ```{autodoc2-docstring} weasyl.test.web.test_characters.test_create_default_thumbnail
    :summary:
    ```
* - {py:obj}`test_owner_edit_details <weasyl.test.web.test_characters.test_owner_edit_details>`
  - ```{autodoc2-docstring} weasyl.test.web.test_characters.test_owner_edit_details
    :summary:
    ```
* - {py:obj}`test_owner_reupload <weasyl.test.web.test_characters.test_owner_reupload>`
  - ```{autodoc2-docstring} weasyl.test.web.test_characters.test_owner_reupload
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_BASE_FORM <weasyl.test.web.test_characters._BASE_FORM>`
  - ```{autodoc2-docstring} weasyl.test.web.test_characters._BASE_FORM
    :summary:
    ```
````

### API

````{py:data} _BASE_FORM
:canonical: weasyl.test.web.test_characters._BASE_FORM
:value: >
   None

```{autodoc2-docstring} weasyl.test.web.test_characters._BASE_FORM
```

````

````{py:function} _read_character_image(image_url)
:canonical: weasyl.test.web.test_characters._read_character_image

```{autodoc2-docstring} weasyl.test.web.test_characters._read_character_image
```
````

````{py:function} _character_user(db)
:canonical: weasyl.test.web.test_characters._character_user

```{autodoc2-docstring} weasyl.test.web.test_characters._character_user
```
````

````{py:function} create_character(app, character_user, **kwargs)
:canonical: weasyl.test.web.test_characters.create_character

```{autodoc2-docstring} weasyl.test.web.test_characters.create_character
```
````

````{py:function} _character(app, db, character_user)
:canonical: weasyl.test.web.test_characters._character

```{autodoc2-docstring} weasyl.test.web.test_characters._character
```
````

````{py:function} test_list_empty(app)
:canonical: weasyl.test.web.test_characters.test_list_empty

```{autodoc2-docstring} weasyl.test.web.test_characters.test_list_empty
```
````

````{py:function} test_create_default_thumbnail(app, character)
:canonical: weasyl.test.web.test_characters.test_create_default_thumbnail

```{autodoc2-docstring} weasyl.test.web.test_characters.test_create_default_thumbnail
```
````

````{py:function} test_owner_edit_details(app, character_user, character)
:canonical: weasyl.test.web.test_characters.test_owner_edit_details

```{autodoc2-docstring} weasyl.test.web.test_characters.test_owner_edit_details
```
````

````{py:function} test_owner_reupload(app, character_user, character)
:canonical: weasyl.test.web.test_characters.test_owner_reupload

```{autodoc2-docstring} weasyl.test.web.test_characters.test_owner_reupload
```
````
