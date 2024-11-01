# {py:mod}`weasyl.collection`

```{py:module} weasyl.collection
```

```{autodoc2-docstring} weasyl.collection
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`select_query <weasyl.collection.select_query>`
  - ```{autodoc2-docstring} weasyl.collection.select_query
    :summary:
    ```
* - {py:obj}`select_count <weasyl.collection.select_count>`
  - ```{autodoc2-docstring} weasyl.collection.select_count
    :summary:
    ```
* - {py:obj}`select_list <weasyl.collection.select_list>`
  - ```{autodoc2-docstring} weasyl.collection.select_list
    :summary:
    ```
* - {py:obj}`find_owners <weasyl.collection.find_owners>`
  - ```{autodoc2-docstring} weasyl.collection.find_owners
    :summary:
    ```
* - {py:obj}`owns <weasyl.collection.owns>`
  - ```{autodoc2-docstring} weasyl.collection.owns
    :summary:
    ```
* - {py:obj}`offer <weasyl.collection.offer>`
  - ```{autodoc2-docstring} weasyl.collection.offer
    :summary:
    ```
* - {py:obj}`_check_throttle <weasyl.collection._check_throttle>`
  - ```{autodoc2-docstring} weasyl.collection._check_throttle
    :summary:
    ```
* - {py:obj}`request <weasyl.collection.request>`
  - ```{autodoc2-docstring} weasyl.collection.request
    :summary:
    ```
* - {py:obj}`pending_accept <weasyl.collection.pending_accept>`
  - ```{autodoc2-docstring} weasyl.collection.pending_accept
    :summary:
    ```
* - {py:obj}`pending_reject <weasyl.collection.pending_reject>`
  - ```{autodoc2-docstring} weasyl.collection.pending_reject
    :summary:
    ```
* - {py:obj}`remove <weasyl.collection.remove>`
  - ```{autodoc2-docstring} weasyl.collection.remove
    :summary:
    ```
````

### API

````{py:function} select_query(userid, *, rating, otherid, pending=False, backid=None, nextid=None)
:canonical: weasyl.collection.select_query

```{autodoc2-docstring} weasyl.collection.select_query
```
````

````{py:function} select_count(userid, rating, *, otherid, pending=False, backid=None, nextid=None)
:canonical: weasyl.collection.select_count

```{autodoc2-docstring} weasyl.collection.select_count
```
````

````{py:function} select_list(userid, rating, limit, *, otherid, pending=False, backid=None, nextid=None)
:canonical: weasyl.collection.select_list

```{autodoc2-docstring} weasyl.collection.select_list
```
````

````{py:function} find_owners(submitid)
:canonical: weasyl.collection.find_owners

```{autodoc2-docstring} weasyl.collection.find_owners
```
````

````{py:function} owns(userid, submitid)
:canonical: weasyl.collection.owns

```{autodoc2-docstring} weasyl.collection.owns
```
````

````{py:function} offer(userid, submitid, otherid)
:canonical: weasyl.collection.offer

```{autodoc2-docstring} weasyl.collection.offer
```
````

````{py:function} _check_throttle(userid, otherid)
:canonical: weasyl.collection._check_throttle

```{autodoc2-docstring} weasyl.collection._check_throttle
```
````

````{py:function} request(userid, submitid, otherid)
:canonical: weasyl.collection.request

```{autodoc2-docstring} weasyl.collection.request
```
````

````{py:function} pending_accept(userid, submissions)
:canonical: weasyl.collection.pending_accept

```{autodoc2-docstring} weasyl.collection.pending_accept
```
````

````{py:function} pending_reject(userid, submissions)
:canonical: weasyl.collection.pending_reject

```{autodoc2-docstring} weasyl.collection.pending_reject
```
````

````{py:function} remove(userid, submissions)
:canonical: weasyl.collection.remove

```{autodoc2-docstring} weasyl.collection.remove
```
````
