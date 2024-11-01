# {py:mod}`weasyl.favorite`

```{py:module} weasyl.favorite
```

```{autodoc2-docstring} weasyl.favorite
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`select_submit_query <weasyl.favorite.select_submit_query>`
  - ```{autodoc2-docstring} weasyl.favorite.select_submit_query
    :summary:
    ```
* - {py:obj}`select_submit_count <weasyl.favorite.select_submit_count>`
  - ```{autodoc2-docstring} weasyl.favorite.select_submit_count
    :summary:
    ```
* - {py:obj}`select_submit <weasyl.favorite.select_submit>`
  - ```{autodoc2-docstring} weasyl.favorite.select_submit
    :summary:
    ```
* - {py:obj}`select_char <weasyl.favorite.select_char>`
  - ```{autodoc2-docstring} weasyl.favorite.select_char
    :summary:
    ```
* - {py:obj}`select_journal <weasyl.favorite.select_journal>`
  - ```{autodoc2-docstring} weasyl.favorite.select_journal
    :summary:
    ```
* - {py:obj}`insert <weasyl.favorite.insert>`
  - ```{autodoc2-docstring} weasyl.favorite.insert
    :summary:
    ```
* - {py:obj}`remove <weasyl.favorite.remove>`
  - ```{autodoc2-docstring} weasyl.favorite.remove
    :summary:
    ```
* - {py:obj}`check <weasyl.favorite.check>`
  - ```{autodoc2-docstring} weasyl.favorite.check
    :summary:
    ```
* - {py:obj}`count <weasyl.favorite.count>`
  - ```{autodoc2-docstring} weasyl.favorite.count
    :summary:
    ```
````

### API

````{py:function} select_submit_query(userid, rating, otherid=None, backid=None, nextid=None)
:canonical: weasyl.favorite.select_submit_query

```{autodoc2-docstring} weasyl.favorite.select_submit_query
```
````

````{py:function} select_submit_count(userid, rating, otherid, backid=None, nextid=None)
:canonical: weasyl.favorite.select_submit_count

```{autodoc2-docstring} weasyl.favorite.select_submit_count
```
````

````{py:function} select_submit(userid, rating, limit, otherid, backid=None, nextid=None)
:canonical: weasyl.favorite.select_submit

```{autodoc2-docstring} weasyl.favorite.select_submit
```
````

````{py:function} select_char(userid, rating, limit, otherid, backid=None, nextid=None)
:canonical: weasyl.favorite.select_char

```{autodoc2-docstring} weasyl.favorite.select_char
```
````

````{py:function} select_journal(userid, rating, limit, otherid, backid=None, nextid=None)
:canonical: weasyl.favorite.select_journal

```{autodoc2-docstring} weasyl.favorite.select_journal
```
````

````{py:function} insert(userid, submitid=None, charid=None, journalid=None)
:canonical: weasyl.favorite.insert

```{autodoc2-docstring} weasyl.favorite.insert
```
````

````{py:function} remove(userid, submitid=None, charid=None, journalid=None)
:canonical: weasyl.favorite.remove

```{autodoc2-docstring} weasyl.favorite.remove
```
````

````{py:function} check(userid, submitid=None, charid=None, journalid=None)
:canonical: weasyl.favorite.check

```{autodoc2-docstring} weasyl.favorite.check
```
````

````{py:function} count(id, contenttype='submission')
:canonical: weasyl.favorite.count

```{autodoc2-docstring} weasyl.favorite.count
```
````
