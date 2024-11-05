# {py:mod}`weasyl.media`

```{py:module} weasyl.media
```

```{autodoc2-docstring} weasyl.media
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`make_resized_media_item <weasyl.media.make_resized_media_item>`
  - ```{autodoc2-docstring} weasyl.media.make_resized_media_item
    :summary:
    ```
* - {py:obj}`make_cover_media_item <weasyl.media.make_cover_media_item>`
  - ```{autodoc2-docstring} weasyl.media.make_cover_media_item
    :summary:
    ```
* - {py:obj}`get_multi_submission_media <weasyl.media.get_multi_submission_media>`
  - ```{autodoc2-docstring} weasyl.media.get_multi_submission_media
    :summary:
    ```
* - {py:obj}`get_multi_user_media <weasyl.media.get_multi_user_media>`
  - ```{autodoc2-docstring} weasyl.media.get_multi_user_media
    :summary:
    ```
* - {py:obj}`get_submission_media <weasyl.media.get_submission_media>`
  - ```{autodoc2-docstring} weasyl.media.get_submission_media
    :summary:
    ```
* - {py:obj}`get_user_media <weasyl.media.get_user_media>`
  - ```{autodoc2-docstring} weasyl.media.get_user_media
    :summary:
    ```
* - {py:obj}`build_populator <weasyl.media.build_populator>`
  - ```{autodoc2-docstring} weasyl.media.build_populator
    :summary:
    ```
* - {py:obj}`format_media_link <weasyl.media.format_media_link>`
  - ```{autodoc2-docstring} weasyl.media.format_media_link
    :summary:
    ```
* - {py:obj}`strip_non_thumbnail_media <weasyl.media.strip_non_thumbnail_media>`
  - ```{autodoc2-docstring} weasyl.media.strip_non_thumbnail_media
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`populate_with_submission_media <weasyl.media.populate_with_submission_media>`
  - ```{autodoc2-docstring} weasyl.media.populate_with_submission_media
    :summary:
    ```
* - {py:obj}`populate_with_user_media <weasyl.media.populate_with_user_media>`
  - ```{autodoc2-docstring} weasyl.media.populate_with_user_media
    :summary:
    ```
````

### API

````{py:function} make_resized_media_item(filedata, size, error_type='FileType')
:canonical: weasyl.media.make_resized_media_item

```{autodoc2-docstring} weasyl.media.make_resized_media_item
```
````

````{py:function} make_cover_media_item(coverfile, error_type='coverType')
:canonical: weasyl.media.make_cover_media_item

```{autodoc2-docstring} weasyl.media.make_cover_media_item
```
````

````{py:function} get_multi_submission_media(*submitids)
:canonical: weasyl.media.get_multi_submission_media

```{autodoc2-docstring} weasyl.media.get_multi_submission_media
```
````

````{py:function} get_multi_user_media(*userids)
:canonical: weasyl.media.get_multi_user_media

```{autodoc2-docstring} weasyl.media.get_multi_user_media
```
````

````{py:function} get_submission_media(submitid)
:canonical: weasyl.media.get_submission_media

```{autodoc2-docstring} weasyl.media.get_submission_media
```
````

````{py:function} get_user_media(userid)
:canonical: weasyl.media.get_user_media

```{autodoc2-docstring} weasyl.media.get_user_media
```
````

````{py:function} build_populator(identity, media_key, multi_get)
:canonical: weasyl.media.build_populator

```{autodoc2-docstring} weasyl.media.build_populator
```
````

````{py:data} populate_with_submission_media
:canonical: weasyl.media.populate_with_submission_media
:value: >
   'build_populator(...)'

```{autodoc2-docstring} weasyl.media.populate_with_submission_media
```

````

````{py:data} populate_with_user_media
:canonical: weasyl.media.populate_with_user_media
:value: >
   'build_populator(...)'

```{autodoc2-docstring} weasyl.media.populate_with_user_media
```

````

````{py:function} format_media_link(media, link)
:canonical: weasyl.media.format_media_link

```{autodoc2-docstring} weasyl.media.format_media_link
```
````

````{py:function} strip_non_thumbnail_media(submissions)
:canonical: weasyl.media.strip_non_thumbnail_media

```{autodoc2-docstring} weasyl.media.strip_non_thumbnail_media
```
````
