# {py:mod}`weasyl.submission`

```{py:module} weasyl.submission
```

```{autodoc2-docstring} weasyl.submission
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_limit <weasyl.submission._limit>`
  - ```{autodoc2-docstring} weasyl.submission._limit
    :summary:
    ```
* - {py:obj}`_create_notifications <weasyl.submission._create_notifications>`
  - ```{autodoc2-docstring} weasyl.submission._create_notifications
    :summary:
    ```
* - {py:obj}`check_for_duplicate_media <weasyl.submission.check_for_duplicate_media>`
  - ```{autodoc2-docstring} weasyl.submission.check_for_duplicate_media
    :summary:
    ```
* - {py:obj}`_create_submission <weasyl.submission._create_submission>`
  - ```{autodoc2-docstring} weasyl.submission._create_submission
    :summary:
    ```
* - {py:obj}`_http_get_if_crosspostable <weasyl.submission._http_get_if_crosspostable>`
  - ```{autodoc2-docstring} weasyl.submission._http_get_if_crosspostable
    :summary:
    ```
* - {py:obj}`create_visual <weasyl.submission.create_visual>`
  - ```{autodoc2-docstring} weasyl.submission.create_visual
    :summary:
    ```
* - {py:obj}`_normalize_google_docs_embed <weasyl.submission._normalize_google_docs_embed>`
  - ```{autodoc2-docstring} weasyl.submission._normalize_google_docs_embed
    :summary:
    ```
* - {py:obj}`create_literary <weasyl.submission.create_literary>`
  - ```{autodoc2-docstring} weasyl.submission.create_literary
    :summary:
    ```
* - {py:obj}`create_multimedia <weasyl.submission.create_multimedia>`
  - ```{autodoc2-docstring} weasyl.submission.create_multimedia
    :summary:
    ```
* - {py:obj}`reupload <weasyl.submission.reupload>`
  - ```{autodoc2-docstring} weasyl.submission.reupload
    :summary:
    ```
* - {py:obj}`get_google_docs_embed_url <weasyl.submission.get_google_docs_embed_url>`
  - ```{autodoc2-docstring} weasyl.submission.get_google_docs_embed_url
    :summary:
    ```
* - {py:obj}`select_view <weasyl.submission.select_view>`
  - ```{autodoc2-docstring} weasyl.submission.select_view
    :summary:
    ```
* - {py:obj}`select_view_api <weasyl.submission.select_view_api>`
  - ```{autodoc2-docstring} weasyl.submission.select_view_api
    :summary:
    ```
* - {py:obj}`_select_query <weasyl.submission._select_query>`
  - ```{autodoc2-docstring} weasyl.submission._select_query
    :summary:
    ```
* - {py:obj}`select_count <weasyl.submission.select_count>`
  - ```{autodoc2-docstring} weasyl.submission.select_count
    :summary:
    ```
* - {py:obj}`select_list <weasyl.submission.select_list>`
  - ```{autodoc2-docstring} weasyl.submission.select_list
    :summary:
    ```
* - {py:obj}`select_featured <weasyl.submission.select_featured>`
  - ```{autodoc2-docstring} weasyl.submission.select_featured
    :summary:
    ```
* - {py:obj}`select_near <weasyl.submission.select_near>`
  - ```{autodoc2-docstring} weasyl.submission.select_near
    :summary:
    ```
* - {py:obj}`_invalidate_collectors_posts_count <weasyl.submission._invalidate_collectors_posts_count>`
  - ```{autodoc2-docstring} weasyl.submission._invalidate_collectors_posts_count
    :summary:
    ```
* - {py:obj}`edit <weasyl.submission.edit>`
  - ```{autodoc2-docstring} weasyl.submission.edit
    :summary:
    ```
* - {py:obj}`remove <weasyl.submission.remove>`
  - ```{autodoc2-docstring} weasyl.submission.remove
    :summary:
    ```
* - {py:obj}`reupload_cover <weasyl.submission.reupload_cover>`
  - ```{autodoc2-docstring} weasyl.submission.reupload_cover
    :summary:
    ```
* - {py:obj}`select_recently_popular <weasyl.submission.select_recently_popular>`
  - ```{autodoc2-docstring} weasyl.submission.select_recently_popular
    :summary:
    ```
* - {py:obj}`select_critique <weasyl.submission.select_critique>`
  - ```{autodoc2-docstring} weasyl.submission.select_critique
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`COUNT_LIMIT <weasyl.submission.COUNT_LIMIT>`
  - ```{autodoc2-docstring} weasyl.submission.COUNT_LIMIT
    :summary:
    ```
* - {py:obj}`_MEGABYTE <weasyl.submission._MEGABYTE>`
  - ```{autodoc2-docstring} weasyl.submission._MEGABYTE
    :summary:
    ```
* - {py:obj}`_LIMITS <weasyl.submission._LIMITS>`
  - ```{autodoc2-docstring} weasyl.submission._LIMITS
    :summary:
    ```
* - {py:obj}`_ALLOWED_CROSSPOST_HOSTS <weasyl.submission._ALLOWED_CROSSPOST_HOSTS>`
  - ```{autodoc2-docstring} weasyl.submission._ALLOWED_CROSSPOST_HOSTS
    :summary:
    ```
* - {py:obj}`_ALLOWED_CROSSPOST_HOST <weasyl.submission._ALLOWED_CROSSPOST_HOST>`
  - ```{autodoc2-docstring} weasyl.submission._ALLOWED_CROSSPOST_HOST
    :summary:
    ```
* - {py:obj}`_GOOGLE_DOCS_EMBED <weasyl.submission._GOOGLE_DOCS_EMBED>`
  - ```{autodoc2-docstring} weasyl.submission._GOOGLE_DOCS_EMBED
    :summary:
    ```
* - {py:obj}`_GOOGLE_DOCS_EMBED_URL_QUERY <weasyl.submission._GOOGLE_DOCS_EMBED_URL_QUERY>`
  - ```{autodoc2-docstring} weasyl.submission._GOOGLE_DOCS_EMBED_URL_QUERY
    :summary:
    ```
````

### API

````{py:data} COUNT_LIMIT
:canonical: weasyl.submission.COUNT_LIMIT
:value: >
   250

```{autodoc2-docstring} weasyl.submission.COUNT_LIMIT
```

````

````{py:data} _MEGABYTE
:canonical: weasyl.submission._MEGABYTE
:value: >
   1048576

```{autodoc2-docstring} weasyl.submission._MEGABYTE
```

````

````{py:data} _LIMITS
:canonical: weasyl.submission._LIMITS
:value: >
   None

```{autodoc2-docstring} weasyl.submission._LIMITS
```

````

````{py:function} _limit(size, extension)
:canonical: weasyl.submission._limit

```{autodoc2-docstring} weasyl.submission._limit
```
````

````{py:function} _create_notifications(userid, submitid, rating, *, friends_only)
:canonical: weasyl.submission._create_notifications

```{autodoc2-docstring} weasyl.submission._create_notifications
```
````

````{py:function} check_for_duplicate_media(userid, mediaid)
:canonical: weasyl.submission.check_for_duplicate_media

```{autodoc2-docstring} weasyl.submission.check_for_duplicate_media
```
````

````{py:function} _create_submission(expected_type)
:canonical: weasyl.submission._create_submission

```{autodoc2-docstring} weasyl.submission._create_submission
```
````

````{py:data} _ALLOWED_CROSSPOST_HOSTS
:canonical: weasyl.submission._ALLOWED_CROSSPOST_HOSTS
:value: >
   'frozenset(...)'

```{autodoc2-docstring} weasyl.submission._ALLOWED_CROSSPOST_HOSTS
```

````

````{py:data} _ALLOWED_CROSSPOST_HOST
:canonical: weasyl.submission._ALLOWED_CROSSPOST_HOST
:value: >
   'compile(...)'

```{autodoc2-docstring} weasyl.submission._ALLOWED_CROSSPOST_HOST
```

````

````{py:function} _http_get_if_crosspostable(url)
:canonical: weasyl.submission._http_get_if_crosspostable

```{autodoc2-docstring} weasyl.submission._http_get_if_crosspostable
```
````

````{py:function} create_visual(userid, submission, friends_only, tags, imageURL, thumbfile, submitfile, critique, create_notifications)
:canonical: weasyl.submission.create_visual

```{autodoc2-docstring} weasyl.submission.create_visual
```
````

````{py:data} _GOOGLE_DOCS_EMBED
:canonical: weasyl.submission._GOOGLE_DOCS_EMBED
:value: >
   'compile(...)'

```{autodoc2-docstring} weasyl.submission._GOOGLE_DOCS_EMBED
```

````

````{py:function} _normalize_google_docs_embed(embedlink)
:canonical: weasyl.submission._normalize_google_docs_embed

```{autodoc2-docstring} weasyl.submission._normalize_google_docs_embed
```
````

````{py:function} create_literary(userid, submission, embedlink=None, friends_only=False, tags=None, coverfile=None, thumbfile=None, submitfile=None, critique=False, create_notifications=True)
:canonical: weasyl.submission.create_literary

```{autodoc2-docstring} weasyl.submission.create_literary
```
````

````{py:function} create_multimedia(userid, submission, embedlink=None, friends_only=None, tags=None, coverfile=None, thumbfile=None, submitfile=None, critique=False, create_notifications=True, auto_thumb=False)
:canonical: weasyl.submission.create_multimedia

```{autodoc2-docstring} weasyl.submission.create_multimedia
```
````

````{py:function} reupload(userid, submitid, submitfile)
:canonical: weasyl.submission.reupload

```{autodoc2-docstring} weasyl.submission.reupload
```
````

````{py:data} _GOOGLE_DOCS_EMBED_URL_QUERY
:canonical: weasyl.submission._GOOGLE_DOCS_EMBED_URL_QUERY
:value: >
   'where(...)'

```{autodoc2-docstring} weasyl.submission._GOOGLE_DOCS_EMBED_URL_QUERY
```

````

````{py:function} get_google_docs_embed_url(submitid)
:canonical: weasyl.submission.get_google_docs_embed_url

```{autodoc2-docstring} weasyl.submission.get_google_docs_embed_url
```
````

````{py:function} select_view(userid, submitid, rating, ignore=True, anyway=None)
:canonical: weasyl.submission.select_view

```{autodoc2-docstring} weasyl.submission.select_view
```
````

````{py:function} select_view_api(userid, submitid, anyway=False, increment_views=False)
:canonical: weasyl.submission.select_view_api

```{autodoc2-docstring} weasyl.submission.select_view_api
```
````

````{py:function} _select_query(*, userid, rating, otherid, folderid, backid, nextid, subcat, profile_page_filter, index_page_filter, featured_filter, critique_only)
:canonical: weasyl.submission._select_query

```{autodoc2-docstring} weasyl.submission._select_query
```
````

````{py:function} select_count(userid, rating, *, otherid=None, folderid=None, backid=None, nextid=None, subcat=None, profile_page_filter=False, index_page_filter=False, featured_filter=False, critique_only=False)
:canonical: weasyl.submission.select_count

```{autodoc2-docstring} weasyl.submission.select_count
```
````

````{py:function} select_list(userid, rating, *, limit, otherid=None, folderid=None, backid=None, nextid=None, subcat=None, profile_page_filter=False, index_page_filter=False, featured_filter=False, critique_only=False)
:canonical: weasyl.submission.select_list

```{autodoc2-docstring} weasyl.submission.select_list
```
````

````{py:function} select_featured(userid, otherid, rating)
:canonical: weasyl.submission.select_featured

```{autodoc2-docstring} weasyl.submission.select_featured
```
````

````{py:function} select_near(userid, rating, limit, otherid, folderid, submitid)
:canonical: weasyl.submission.select_near

```{autodoc2-docstring} weasyl.submission.select_near
```
````

````{py:function} _invalidate_collectors_posts_count(submitid)
:canonical: weasyl.submission._invalidate_collectors_posts_count

```{autodoc2-docstring} weasyl.submission._invalidate_collectors_posts_count
```
````

````{py:function} edit(userid, submission, embedlink=None, friends_only=False, critique=False)
:canonical: weasyl.submission.edit

```{autodoc2-docstring} weasyl.submission.edit
```
````

````{py:function} remove(userid, submitid)
:canonical: weasyl.submission.remove

```{autodoc2-docstring} weasyl.submission.remove
```
````

````{py:function} reupload_cover(userid, submitid, coverfile)
:canonical: weasyl.submission.reupload_cover

```{autodoc2-docstring} weasyl.submission.reupload_cover
```
````

````{py:function} select_recently_popular()
:canonical: weasyl.submission.select_recently_popular

```{autodoc2-docstring} weasyl.submission.select_recently_popular
```
````

````{py:function} select_critique()
:canonical: weasyl.submission.select_critique

```{autodoc2-docstring} weasyl.submission.select_critique
```
````
