# {py:mod}`weasyl.followuser`

```{py:module} weasyl.followuser
```

```{autodoc2-docstring} weasyl.followuser
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`list_followed <weasyl.followuser.list_followed>`
  - ```{autodoc2-docstring} weasyl.followuser.list_followed
    :summary:
    ```
* - {py:obj}`select_settings <weasyl.followuser.select_settings>`
  - ```{autodoc2-docstring} weasyl.followuser.select_settings
    :summary:
    ```
* - {py:obj}`select_followed <weasyl.followuser.select_followed>`
  - ```{autodoc2-docstring} weasyl.followuser.select_followed
    :summary:
    ```
* - {py:obj}`select_following <weasyl.followuser.select_following>`
  - ```{autodoc2-docstring} weasyl.followuser.select_following
    :summary:
    ```
* - {py:obj}`manage_following <weasyl.followuser.manage_following>`
  - ```{autodoc2-docstring} weasyl.followuser.manage_following
    :summary:
    ```
* - {py:obj}`insert <weasyl.followuser.insert>`
  - ```{autodoc2-docstring} weasyl.followuser.insert
    :summary:
    ```
* - {py:obj}`update <weasyl.followuser.update>`
  - ```{autodoc2-docstring} weasyl.followuser.update
    :summary:
    ```
* - {py:obj}`remove <weasyl.followuser.remove>`
  - ```{autodoc2-docstring} weasyl.followuser.remove
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`WatchSettings <weasyl.followuser.WatchSettings>`
  - ```{autodoc2-docstring} weasyl.followuser.WatchSettings
    :summary:
    ```
````

### API

````{py:data} WatchSettings
:canonical: weasyl.followuser.WatchSettings
:value: >
   'create_configuration(...)'

```{autodoc2-docstring} weasyl.followuser.WatchSettings
```

````

````{py:function} list_followed(userid, settings, rating=ratings.GENERAL.code, friends=False)
:canonical: weasyl.followuser.list_followed

```{autodoc2-docstring} weasyl.followuser.list_followed
```
````

````{py:function} select_settings(userid, otherid)
:canonical: weasyl.followuser.select_settings

```{autodoc2-docstring} weasyl.followuser.select_settings
```
````

````{py:function} select_followed(userid, otherid, limit=None, backid=None, nextid=None, following=False)
:canonical: weasyl.followuser.select_followed

```{autodoc2-docstring} weasyl.followuser.select_followed
```
````

````{py:function} select_following(userid, otherid, limit=None, backid=None, nextid=None)
:canonical: weasyl.followuser.select_following

```{autodoc2-docstring} weasyl.followuser.select_following
```
````

````{py:function} manage_following(userid, limit, backid=None, nextid=None)
:canonical: weasyl.followuser.manage_following

```{autodoc2-docstring} weasyl.followuser.manage_following
```
````

````{py:function} insert(userid, otherid)
:canonical: weasyl.followuser.insert

```{autodoc2-docstring} weasyl.followuser.insert
```
````

````{py:function} update(userid, otherid, watch_settings)
:canonical: weasyl.followuser.update

```{autodoc2-docstring} weasyl.followuser.update
```
````

````{py:function} remove(userid, otherid)
:canonical: weasyl.followuser.remove

```{autodoc2-docstring} weasyl.followuser.remove
```
````
