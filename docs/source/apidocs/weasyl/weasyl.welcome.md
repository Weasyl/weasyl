# {py:mod}`weasyl.welcome`

```{py:module} weasyl.welcome
```

```{autodoc2-docstring} weasyl.welcome
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_insert <weasyl.welcome._insert>`
  - ```{autodoc2-docstring} weasyl.welcome._insert
    :summary:
    ```
* - {py:obj}`submission_insert <weasyl.welcome.submission_insert>`
  - ```{autodoc2-docstring} weasyl.welcome.submission_insert
    :summary:
    ```
* - {py:obj}`_queries_for_submission_notifications <weasyl.welcome._queries_for_submission_notifications>`
  - ```{autodoc2-docstring} weasyl.welcome._queries_for_submission_notifications
    :summary:
    ```
* - {py:obj}`submission_remove <weasyl.welcome.submission_remove>`
  - ```{autodoc2-docstring} weasyl.welcome.submission_remove
    :summary:
    ```
* - {py:obj}`submission_became_friends_only <weasyl.welcome.submission_became_friends_only>`
  - ```{autodoc2-docstring} weasyl.welcome.submission_became_friends_only
    :summary:
    ```
* - {py:obj}`character_insert <weasyl.welcome.character_insert>`
  - ```{autodoc2-docstring} weasyl.welcome.character_insert
    :summary:
    ```
* - {py:obj}`character_remove <weasyl.welcome.character_remove>`
  - ```{autodoc2-docstring} weasyl.welcome.character_remove
    :summary:
    ```
* - {py:obj}`collection_insert <weasyl.welcome.collection_insert>`
  - ```{autodoc2-docstring} weasyl.welcome.collection_insert
    :summary:
    ```
* - {py:obj}`collection_remove <weasyl.welcome.collection_remove>`
  - ```{autodoc2-docstring} weasyl.welcome.collection_remove
    :summary:
    ```
* - {py:obj}`journal_insert <weasyl.welcome.journal_insert>`
  - ```{autodoc2-docstring} weasyl.welcome.journal_insert
    :summary:
    ```
* - {py:obj}`journal_remove <weasyl.welcome.journal_remove>`
  - ```{autodoc2-docstring} weasyl.welcome.journal_remove
    :summary:
    ```
* - {py:obj}`collectoffer_insert <weasyl.welcome.collectoffer_insert>`
  - ```{autodoc2-docstring} weasyl.welcome.collectoffer_insert
    :summary:
    ```
* - {py:obj}`collectrequest_insert <weasyl.welcome.collectrequest_insert>`
  - ```{autodoc2-docstring} weasyl.welcome.collectrequest_insert
    :summary:
    ```
* - {py:obj}`collectrequest_remove <weasyl.welcome.collectrequest_remove>`
  - ```{autodoc2-docstring} weasyl.welcome.collectrequest_remove
    :summary:
    ```
* - {py:obj}`favorite_insert <weasyl.welcome.favorite_insert>`
  - ```{autodoc2-docstring} weasyl.welcome.favorite_insert
    :summary:
    ```
* - {py:obj}`favorite_remove <weasyl.welcome.favorite_remove>`
  - ```{autodoc2-docstring} weasyl.welcome.favorite_remove
    :summary:
    ```
* - {py:obj}`shout_insert <weasyl.welcome.shout_insert>`
  - ```{autodoc2-docstring} weasyl.welcome.shout_insert
    :summary:
    ```
* - {py:obj}`shoutreply_insert <weasyl.welcome.shoutreply_insert>`
  - ```{autodoc2-docstring} weasyl.welcome.shoutreply_insert
    :summary:
    ```
* - {py:obj}`comment_insert <weasyl.welcome.comment_insert>`
  - ```{autodoc2-docstring} weasyl.welcome.comment_insert
    :summary:
    ```
* - {py:obj}`comment_remove <weasyl.welcome.comment_remove>`
  - ```{autodoc2-docstring} weasyl.welcome.comment_remove
    :summary:
    ```
* - {py:obj}`commentreply_insert <weasyl.welcome.commentreply_insert>`
  - ```{autodoc2-docstring} weasyl.welcome.commentreply_insert
    :summary:
    ```
* - {py:obj}`stream_insert <weasyl.welcome.stream_insert>`
  - ```{autodoc2-docstring} weasyl.welcome.stream_insert
    :summary:
    ```
* - {py:obj}`followuser_insert <weasyl.welcome.followuser_insert>`
  - ```{autodoc2-docstring} weasyl.welcome.followuser_insert
    :summary:
    ```
* - {py:obj}`followuser_remove <weasyl.welcome.followuser_remove>`
  - ```{autodoc2-docstring} weasyl.welcome.followuser_remove
    :summary:
    ```
* - {py:obj}`frienduserrequest_insert <weasyl.welcome.frienduserrequest_insert>`
  - ```{autodoc2-docstring} weasyl.welcome.frienduserrequest_insert
    :summary:
    ```
* - {py:obj}`frienduserrequest_remove <weasyl.welcome.frienduserrequest_remove>`
  - ```{autodoc2-docstring} weasyl.welcome.frienduserrequest_remove
    :summary:
    ```
* - {py:obj}`frienduseraccept_insert <weasyl.welcome.frienduseraccept_insert>`
  - ```{autodoc2-docstring} weasyl.welcome.frienduseraccept_insert
    :summary:
    ```
* - {py:obj}`frienduseraccept_remove <weasyl.welcome.frienduseraccept_remove>`
  - ```{autodoc2-docstring} weasyl.welcome.frienduseraccept_remove
    :summary:
    ```
* - {py:obj}`site_update_insert <weasyl.welcome.site_update_insert>`
  - ```{autodoc2-docstring} weasyl.welcome.site_update_insert
    :summary:
    ```
````

### API

````{py:function} _insert(sender, referid, targetid, type, notify_users)
:canonical: weasyl.welcome._insert

```{autodoc2-docstring} weasyl.welcome._insert
```
````

````{py:function} submission_insert(userid, submitid, rating=ratings.GENERAL.code, friends_only=False)
:canonical: weasyl.welcome.submission_insert

```{autodoc2-docstring} weasyl.welcome.submission_insert
```
````

````{py:function} _queries_for_submission_notifications(submitid)
:canonical: weasyl.welcome._queries_for_submission_notifications

```{autodoc2-docstring} weasyl.welcome._queries_for_submission_notifications
```
````

````{py:function} submission_remove(submitid)
:canonical: weasyl.welcome.submission_remove

```{autodoc2-docstring} weasyl.welcome.submission_remove
```
````

````{py:function} submission_became_friends_only(submitid, ownerid)
:canonical: weasyl.welcome.submission_became_friends_only

```{autodoc2-docstring} weasyl.welcome.submission_became_friends_only
```
````

````{py:function} character_insert(userid, charid, rating=ratings.GENERAL.code, *, friends_only)
:canonical: weasyl.welcome.character_insert

```{autodoc2-docstring} weasyl.welcome.character_insert
```
````

````{py:function} character_remove(charid)
:canonical: weasyl.welcome.character_remove

```{autodoc2-docstring} weasyl.welcome.character_remove
```
````

````{py:function} collection_insert(userid, submitid)
:canonical: weasyl.welcome.collection_insert

```{autodoc2-docstring} weasyl.welcome.collection_insert
```
````

````{py:function} collection_remove(userid, remove)
:canonical: weasyl.welcome.collection_remove

```{autodoc2-docstring} weasyl.welcome.collection_remove
```
````

````{py:function} journal_insert(userid, journalid, *, rating, friends_only)
:canonical: weasyl.welcome.journal_insert

```{autodoc2-docstring} weasyl.welcome.journal_insert
```
````

````{py:function} journal_remove(journalid)
:canonical: weasyl.welcome.journal_remove

```{autodoc2-docstring} weasyl.welcome.journal_remove
```
````

````{py:function} collectoffer_insert(userid, otherid, submitid)
:canonical: weasyl.welcome.collectoffer_insert

```{autodoc2-docstring} weasyl.welcome.collectoffer_insert
```
````

````{py:function} collectrequest_insert(userid, otherid, submitid)
:canonical: weasyl.welcome.collectrequest_insert

```{autodoc2-docstring} weasyl.welcome.collectrequest_insert
```
````

````{py:function} collectrequest_remove(userid, otherid, submitid)
:canonical: weasyl.welcome.collectrequest_remove

```{autodoc2-docstring} weasyl.welcome.collectrequest_remove
```
````

````{py:function} favorite_insert(db, userid, *, submitid, charid, journalid, otherid)
:canonical: weasyl.welcome.favorite_insert

```{autodoc2-docstring} weasyl.welcome.favorite_insert
```
````

````{py:function} favorite_remove(db, userid, submitid=None, charid=None, journalid=None)
:canonical: weasyl.welcome.favorite_remove

```{autodoc2-docstring} weasyl.welcome.favorite_remove
```
````

````{py:function} shout_insert(userid, commentid, otherid)
:canonical: weasyl.welcome.shout_insert

```{autodoc2-docstring} weasyl.welcome.shout_insert
```
````

````{py:function} shoutreply_insert(userid, commentid, otherid, parentid, staffnote=False)
:canonical: weasyl.welcome.shoutreply_insert

```{autodoc2-docstring} weasyl.welcome.shoutreply_insert
```
````

````{py:function} comment_insert(userid, commentid, otherid, submitid, charid, journalid, updateid)
:canonical: weasyl.welcome.comment_insert

```{autodoc2-docstring} weasyl.welcome.comment_insert
```
````

````{py:function} comment_remove(commentid, feature)
:canonical: weasyl.welcome.comment_remove

```{autodoc2-docstring} weasyl.welcome.comment_remove
```
````

````{py:function} commentreply_insert(userid, commentid, otherid, parentid, submitid, charid, journalid, updateid)
:canonical: weasyl.welcome.commentreply_insert

```{autodoc2-docstring} weasyl.welcome.commentreply_insert
```
````

````{py:function} stream_insert(userid, status)
:canonical: weasyl.welcome.stream_insert

```{autodoc2-docstring} weasyl.welcome.stream_insert
```
````

````{py:function} followuser_insert(userid, otherid)
:canonical: weasyl.welcome.followuser_insert

```{autodoc2-docstring} weasyl.welcome.followuser_insert
```
````

````{py:function} followuser_remove(userid, otherid)
:canonical: weasyl.welcome.followuser_remove

```{autodoc2-docstring} weasyl.welcome.followuser_remove
```
````

````{py:function} frienduserrequest_insert(userid, otherid)
:canonical: weasyl.welcome.frienduserrequest_insert

```{autodoc2-docstring} weasyl.welcome.frienduserrequest_insert
```
````

````{py:function} frienduserrequest_remove(userid, otherid)
:canonical: weasyl.welcome.frienduserrequest_remove

```{autodoc2-docstring} weasyl.welcome.frienduserrequest_remove
```
````

````{py:function} frienduseraccept_insert(userid, otherid)
:canonical: weasyl.welcome.frienduseraccept_insert

```{autodoc2-docstring} weasyl.welcome.frienduseraccept_insert
```
````

````{py:function} frienduseraccept_remove(userid, otherid)
:canonical: weasyl.welcome.frienduseraccept_remove

```{autodoc2-docstring} weasyl.welcome.frienduseraccept_remove
```
````

````{py:function} site_update_insert(updateid)
:canonical: weasyl.welcome.site_update_insert

```{autodoc2-docstring} weasyl.welcome.site_update_insert
```
````
