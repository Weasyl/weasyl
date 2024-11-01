# {py:mod}`weasyl.shout`

```{py:module} weasyl.shout
```

```{autodoc2-docstring} weasyl.shout
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`select <weasyl.shout.select>`
  - ```{autodoc2-docstring} weasyl.shout.select
    :summary:
    ```
* - {py:obj}`count_staff_notes <weasyl.shout.count_staff_notes>`
  - ```{autodoc2-docstring} weasyl.shout.count_staff_notes
    :summary:
    ```
* - {py:obj}`insert <weasyl.shout.insert>`
  - ```{autodoc2-docstring} weasyl.shout.insert
    :summary:
    ```
* - {py:obj}`remove <weasyl.shout.remove>`
  - ```{autodoc2-docstring} weasyl.shout.remove
    :summary:
    ```
````

### API

````{py:function} select(userid, ownerid, limit=None, staffnotes=False)
:canonical: weasyl.shout.select

```{autodoc2-docstring} weasyl.shout.select
```
````

````{py:function} count_staff_notes(ownerid)
:canonical: weasyl.shout.count_staff_notes

```{autodoc2-docstring} weasyl.shout.count_staff_notes
```
````

````{py:function} insert(userid, target_user, parentid, content, staffnotes)
:canonical: weasyl.shout.insert

```{autodoc2-docstring} weasyl.shout.insert
```
````

````{py:function} remove(userid, *, commentid)
:canonical: weasyl.shout.remove

```{autodoc2-docstring} weasyl.shout.remove
```
````
