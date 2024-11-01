# {py:mod}`weasyl.journal`

```{py:module} weasyl.journal
```

```{autodoc2-docstring} weasyl.journal
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`create <weasyl.journal.create>`
  - ```{autodoc2-docstring} weasyl.journal.create
    :summary:
    ```
* - {py:obj}`_select_journal_and_check <weasyl.journal._select_journal_and_check>`
  - ```{autodoc2-docstring} weasyl.journal._select_journal_and_check
    :summary:
    ```
* - {py:obj}`select_view <weasyl.journal.select_view>`
  - ```{autodoc2-docstring} weasyl.journal.select_view
    :summary:
    ```
* - {py:obj}`select_view_api <weasyl.journal.select_view_api>`
  - ```{autodoc2-docstring} weasyl.journal.select_view_api
    :summary:
    ```
* - {py:obj}`select_user_list <weasyl.journal.select_user_list>`
  - ```{autodoc2-docstring} weasyl.journal.select_user_list
    :summary:
    ```
* - {py:obj}`select_list <weasyl.journal.select_list>`
  - ```{autodoc2-docstring} weasyl.journal.select_list
    :summary:
    ```
* - {py:obj}`select_latest <weasyl.journal.select_latest>`
  - ```{autodoc2-docstring} weasyl.journal.select_latest
    :summary:
    ```
* - {py:obj}`edit <weasyl.journal.edit>`
  - ```{autodoc2-docstring} weasyl.journal.edit
    :summary:
    ```
* - {py:obj}`remove <weasyl.journal.remove>`
  - ```{autodoc2-docstring} weasyl.journal.remove
    :summary:
    ```
````

### API

````{py:function} create(userid, journal, friends_only=False, tags=None)
:canonical: weasyl.journal.create

```{autodoc2-docstring} weasyl.journal.create
```
````

````{py:function} _select_journal_and_check(userid, journalid, *, rating, ignore, anyway, increment_views=True)
:canonical: weasyl.journal._select_journal_and_check

```{autodoc2-docstring} weasyl.journal._select_journal_and_check
```
````

````{py:function} select_view(userid, rating, journalid, ignore=True, anyway=None)
:canonical: weasyl.journal.select_view

```{autodoc2-docstring} weasyl.journal.select_view
```
````

````{py:function} select_view_api(userid, journalid, anyway=False, increment_views=False)
:canonical: weasyl.journal.select_view_api

```{autodoc2-docstring} weasyl.journal.select_view_api
```
````

````{py:function} select_user_list(userid, rating, limit, backid=None, nextid=None)
:canonical: weasyl.journal.select_user_list

```{autodoc2-docstring} weasyl.journal.select_user_list
```
````

````{py:function} select_list(userid, rating, otherid)
:canonical: weasyl.journal.select_list

```{autodoc2-docstring} weasyl.journal.select_list
```
````

````{py:function} select_latest(userid, rating, otherid)
:canonical: weasyl.journal.select_latest

```{autodoc2-docstring} weasyl.journal.select_latest
```
````

````{py:function} edit(userid, journal, friends_only=False)
:canonical: weasyl.journal.edit

```{autodoc2-docstring} weasyl.journal.edit
```
````

````{py:function} remove(userid, journalid)
:canonical: weasyl.journal.remove

```{autodoc2-docstring} weasyl.journal.remove
```
````
