# {py:mod}`weasyl.character`

```{py:module} weasyl.character
```

```{autodoc2-docstring} weasyl.character
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`create <weasyl.character.create>`
  - ```{autodoc2-docstring} weasyl.character.create
    :summary:
    ```
* - {py:obj}`reupload <weasyl.character.reupload>`
  - ```{autodoc2-docstring} weasyl.character.reupload
    :summary:
    ```
* - {py:obj}`_select_character_and_check <weasyl.character._select_character_and_check>`
  - ```{autodoc2-docstring} weasyl.character._select_character_and_check
    :summary:
    ```
* - {py:obj}`select_view <weasyl.character.select_view>`
  - ```{autodoc2-docstring} weasyl.character.select_view
    :summary:
    ```
* - {py:obj}`select_view_api <weasyl.character.select_view_api>`
  - ```{autodoc2-docstring} weasyl.character.select_view_api
    :summary:
    ```
* - {py:obj}`select_query <weasyl.character.select_query>`
  - ```{autodoc2-docstring} weasyl.character.select_query
    :summary:
    ```
* - {py:obj}`select_count <weasyl.character.select_count>`
  - ```{autodoc2-docstring} weasyl.character.select_count
    :summary:
    ```
* - {py:obj}`select_list <weasyl.character.select_list>`
  - ```{autodoc2-docstring} weasyl.character.select_list
    :summary:
    ```
* - {py:obj}`edit <weasyl.character.edit>`
  - ```{autodoc2-docstring} weasyl.character.edit
    :summary:
    ```
* - {py:obj}`remove <weasyl.character.remove>`
  - ```{autodoc2-docstring} weasyl.character.remove
    :summary:
    ```
* - {py:obj}`fake_media_items <weasyl.character.fake_media_items>`
  - ```{autodoc2-docstring} weasyl.character.fake_media_items
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_MEGABYTE <weasyl.character._MEGABYTE>`
  - ```{autodoc2-docstring} weasyl.character._MEGABYTE
    :summary:
    ```
* - {py:obj}`_MAIN_IMAGE_SIZE_LIMIT <weasyl.character._MAIN_IMAGE_SIZE_LIMIT>`
  - ```{autodoc2-docstring} weasyl.character._MAIN_IMAGE_SIZE_LIMIT
    :summary:
    ```
````

### API

````{py:data} _MEGABYTE
:canonical: weasyl.character._MEGABYTE
:value: >
   1048576

```{autodoc2-docstring} weasyl.character._MEGABYTE
```

````

````{py:data} _MAIN_IMAGE_SIZE_LIMIT
:canonical: weasyl.character._MAIN_IMAGE_SIZE_LIMIT
:value: >
   None

```{autodoc2-docstring} weasyl.character._MAIN_IMAGE_SIZE_LIMIT
```

````

````{py:function} create(userid, character, friends, tags, thumbfile, submitfile)
:canonical: weasyl.character.create

```{autodoc2-docstring} weasyl.character.create
```
````

````{py:function} reupload(userid, charid, submitdata)
:canonical: weasyl.character.reupload

```{autodoc2-docstring} weasyl.character.reupload
```
````

````{py:function} _select_character_and_check(userid, charid, *, rating, ignore, anyway, increment_views=True)
:canonical: weasyl.character._select_character_and_check

```{autodoc2-docstring} weasyl.character._select_character_and_check
```
````

````{py:function} select_view(userid, charid, rating, ignore=True, anyway=None)
:canonical: weasyl.character.select_view

```{autodoc2-docstring} weasyl.character.select_view
```
````

````{py:function} select_view_api(userid, charid, anyway=False, increment_views=False)
:canonical: weasyl.character.select_view_api

```{autodoc2-docstring} weasyl.character.select_view_api
```
````

````{py:function} select_query(userid, rating, otherid=None, backid=None, nextid=None)
:canonical: weasyl.character.select_query

```{autodoc2-docstring} weasyl.character.select_query
```
````

````{py:function} select_count(userid, rating, otherid=None, backid=None, nextid=None)
:canonical: weasyl.character.select_count

```{autodoc2-docstring} weasyl.character.select_count
```
````

````{py:function} select_list(userid, rating, limit, otherid=None, backid=None, nextid=None)
:canonical: weasyl.character.select_list

```{autodoc2-docstring} weasyl.character.select_list
```
````

````{py:function} edit(userid, character, friends_only)
:canonical: weasyl.character.edit

```{autodoc2-docstring} weasyl.character.edit
```
````

````{py:function} remove(userid, charid)
:canonical: weasyl.character.remove

```{autodoc2-docstring} weasyl.character.remove
```
````

````{py:function} fake_media_items(charid, userid, login, settings)
:canonical: weasyl.character.fake_media_items

```{autodoc2-docstring} weasyl.character.fake_media_items
```
````
