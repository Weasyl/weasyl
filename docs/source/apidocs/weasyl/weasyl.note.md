# {py:mod}`weasyl.note`

```{py:module} weasyl.note
```

```{autodoc2-docstring} weasyl.note
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_select_inbox_query <weasyl.note._select_inbox_query>`
  - ```{autodoc2-docstring} weasyl.note._select_inbox_query
    :summary:
    ```
* - {py:obj}`_select_outbox_query <weasyl.note._select_outbox_query>`
  - ```{autodoc2-docstring} weasyl.note._select_outbox_query
    :summary:
    ```
* - {py:obj}`select_inbox <weasyl.note.select_inbox>`
  - ```{autodoc2-docstring} weasyl.note.select_inbox
    :summary:
    ```
* - {py:obj}`select_outbox <weasyl.note.select_outbox>`
  - ```{autodoc2-docstring} weasyl.note.select_outbox
    :summary:
    ```
* - {py:obj}`select_inbox_count <weasyl.note.select_inbox_count>`
  - ```{autodoc2-docstring} weasyl.note.select_inbox_count
    :summary:
    ```
* - {py:obj}`select_outbox_count <weasyl.note.select_outbox_count>`
  - ```{autodoc2-docstring} weasyl.note.select_outbox_count
    :summary:
    ```
* - {py:obj}`select_view <weasyl.note.select_view>`
  - ```{autodoc2-docstring} weasyl.note.select_view
    :summary:
    ```
* - {py:obj}`send <weasyl.note.send>`
  - ```{autodoc2-docstring} weasyl.note.send
    :summary:
    ```
* - {py:obj}`remove_list <weasyl.note.remove_list>`
  - ```{autodoc2-docstring} weasyl.note.remove_list
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`PAGE_SIZE <weasyl.note.PAGE_SIZE>`
  - ```{autodoc2-docstring} weasyl.note.PAGE_SIZE
    :summary:
    ```
* - {py:obj}`COUNT_LIMIT <weasyl.note.COUNT_LIMIT>`
  - ```{autodoc2-docstring} weasyl.note.COUNT_LIMIT
    :summary:
    ```
* - {py:obj}`unread_count <weasyl.note.unread_count>`
  - ```{autodoc2-docstring} weasyl.note.unread_count
    :summary:
    ```
````

### API

````{py:data} PAGE_SIZE
:canonical: weasyl.note.PAGE_SIZE
:value: >
   50

```{autodoc2-docstring} weasyl.note.PAGE_SIZE
```

````

````{py:data} COUNT_LIMIT
:canonical: weasyl.note.COUNT_LIMIT
:value: >
   1000

```{autodoc2-docstring} weasyl.note.COUNT_LIMIT
```

````

````{py:function} _select_inbox_query(with_backid: bool, with_nextid: bool, with_filter: bool)
:canonical: weasyl.note._select_inbox_query

```{autodoc2-docstring} weasyl.note._select_inbox_query
```
````

````{py:function} _select_outbox_query(with_backid: bool, with_nextid: bool, with_filter: bool)
:canonical: weasyl.note._select_outbox_query

```{autodoc2-docstring} weasyl.note._select_outbox_query
```
````

````{py:function} select_inbox(userid, *, limit: None, backid, nextid, filter)
:canonical: weasyl.note.select_inbox

```{autodoc2-docstring} weasyl.note.select_inbox
```
````

````{py:function} select_outbox(userid, *, limit: None, backid, nextid, filter)
:canonical: weasyl.note.select_outbox

```{autodoc2-docstring} weasyl.note.select_outbox
```
````

````{py:function} select_inbox_count(userid, *, backid, nextid, filter)
:canonical: weasyl.note.select_inbox_count

```{autodoc2-docstring} weasyl.note.select_inbox_count
```
````

````{py:function} select_outbox_count(userid, *, backid, nextid, filter)
:canonical: weasyl.note.select_outbox_count

```{autodoc2-docstring} weasyl.note.select_outbox_count
```
````

````{py:function} select_view(userid, noteid)
:canonical: weasyl.note.select_view

```{autodoc2-docstring} weasyl.note.select_view
```
````

````{py:function} send(userid, form)
:canonical: weasyl.note.send

```{autodoc2-docstring} weasyl.note.send
```
````

````{py:function} remove_list(userid, noteids)
:canonical: weasyl.note.remove_list

```{autodoc2-docstring} weasyl.note.remove_list
```
````

````{py:data} unread_count
:canonical: weasyl.note.unread_count
:value: >
   None

```{autodoc2-docstring} weasyl.note.unread_count
```

````
