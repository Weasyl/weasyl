# {py:mod}`weasyl.comment`

```{py:module} weasyl.comment
```

```{autodoc2-docstring} weasyl.comment
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`thread <weasyl.comment.thread>`
  - ```{autodoc2-docstring} weasyl.comment.thread
    :summary:
    ```
* - {py:obj}`select <weasyl.comment.select>`
  - ```{autodoc2-docstring} weasyl.comment.select
    :summary:
    ```
* - {py:obj}`insert <weasyl.comment.insert>`
  - ```{autodoc2-docstring} weasyl.comment.insert
    :summary:
    ```
* - {py:obj}`remove <weasyl.comment.remove>`
  - ```{autodoc2-docstring} weasyl.comment.remove
    :summary:
    ```
* - {py:obj}`count <weasyl.comment.count>`
  - ```{autodoc2-docstring} weasyl.comment.count
    :summary:
    ```
````

### API

````{py:function} thread(query, reverse_top_level)
:canonical: weasyl.comment.thread

```{autodoc2-docstring} weasyl.comment.thread
```
````

````{py:function} select(userid, submitid=None, charid=None, journalid=None, updateid=None)
:canonical: weasyl.comment.select

```{autodoc2-docstring} weasyl.comment.select
```
````

````{py:function} insert(userid, submitid=None, charid=None, journalid=None, updateid=None, parentid=None, content=None)
:canonical: weasyl.comment.insert

```{autodoc2-docstring} weasyl.comment.insert
```
````

````{py:function} remove(userid, *, feature, commentid)
:canonical: weasyl.comment.remove

```{autodoc2-docstring} weasyl.comment.remove
```
````

````{py:function} count(id, contenttype='submission')
:canonical: weasyl.comment.count

```{autodoc2-docstring} weasyl.comment.count
```
````
