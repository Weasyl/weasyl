# {py:mod}`weasyl.message`

```{py:module} weasyl.message
```

```{autodoc2-docstring} weasyl.message
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_fake_media_items <weasyl.message._fake_media_items>`
  - ```{autodoc2-docstring} weasyl.message._fake_media_items
    :summary:
    ```
* - {py:obj}`remove <weasyl.message.remove>`
  - ```{autodoc2-docstring} weasyl.message.remove
    :summary:
    ```
* - {py:obj}`remove_all_before <weasyl.message.remove_all_before>`
  - ```{autodoc2-docstring} weasyl.message.remove_all_before
    :summary:
    ```
* - {py:obj}`remove_all_submissions <weasyl.message.remove_all_submissions>`
  - ```{autodoc2-docstring} weasyl.message.remove_all_submissions
    :summary:
    ```
* - {py:obj}`select_journals <weasyl.message.select_journals>`
  - ```{autodoc2-docstring} weasyl.message.select_journals
    :summary:
    ```
* - {py:obj}`select_submissions <weasyl.message.select_submissions>`
  - ```{autodoc2-docstring} weasyl.message.select_submissions
    :summary:
    ```
* - {py:obj}`select_site_updates <weasyl.message.select_site_updates>`
  - ```{autodoc2-docstring} weasyl.message.select_site_updates
    :summary:
    ```
* - {py:obj}`select_notifications <weasyl.message.select_notifications>`
  - ```{autodoc2-docstring} weasyl.message.select_notifications
    :summary:
    ```
* - {py:obj}`select_comments <weasyl.message.select_comments>`
  - ```{autodoc2-docstring} weasyl.message.select_comments
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`notification_clusters <weasyl.message.notification_clusters>`
  - ```{autodoc2-docstring} weasyl.message.notification_clusters
    :summary:
    ```
* - {py:obj}`_CONTYPE_CHAR <weasyl.message._CONTYPE_CHAR>`
  - ```{autodoc2-docstring} weasyl.message._CONTYPE_CHAR
    :summary:
    ```
````

### API

````{py:data} notification_clusters
:canonical: weasyl.message.notification_clusters
:value: >
   None

```{autodoc2-docstring} weasyl.message.notification_clusters
```

````

````{py:data} _CONTYPE_CHAR
:canonical: weasyl.message._CONTYPE_CHAR
:value: >
   20

```{autodoc2-docstring} weasyl.message._CONTYPE_CHAR
```

````

````{py:function} _fake_media_items(i)
:canonical: weasyl.message._fake_media_items

```{autodoc2-docstring} weasyl.message._fake_media_items
```
````

````{py:function} remove(userid, messages)
:canonical: weasyl.message.remove

```{autodoc2-docstring} weasyl.message.remove
```
````

````{py:function} remove_all_before(userid, before)
:canonical: weasyl.message.remove_all_before

```{autodoc2-docstring} weasyl.message.remove_all_before
```
````

````{py:function} remove_all_submissions(userid, only_before)
:canonical: weasyl.message.remove_all_submissions

```{autodoc2-docstring} weasyl.message.remove_all_submissions
```
````

````{py:function} select_journals(userid)
:canonical: weasyl.message.select_journals

```{autodoc2-docstring} weasyl.message.select_journals
```
````

````{py:function} select_submissions(userid, limit, include_tags, backtime=None, nexttime=None)
:canonical: weasyl.message.select_submissions

```{autodoc2-docstring} weasyl.message.select_submissions
```
````

````{py:function} select_site_updates(userid)
:canonical: weasyl.message.select_site_updates

```{autodoc2-docstring} weasyl.message.select_site_updates
```
````

````{py:function} select_notifications(userid)
:canonical: weasyl.message.select_notifications

```{autodoc2-docstring} weasyl.message.select_notifications
```
````

````{py:function} select_comments(userid)
:canonical: weasyl.message.select_comments

```{autodoc2-docstring} weasyl.message.select_comments
```
````
