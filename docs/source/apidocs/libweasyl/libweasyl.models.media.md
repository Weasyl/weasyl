# {py:mod}`libweasyl.models.media`

```{py:module} libweasyl.models.media
```

```{autodoc2-docstring} libweasyl.models.media
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`MediaItem <libweasyl.models.media.MediaItem>`
  - ```{autodoc2-docstring} libweasyl.models.media.MediaItem
    :summary:
    ```
* - {py:obj}`_LinkMixin <libweasyl.models.media._LinkMixin>`
  - ```{autodoc2-docstring} libweasyl.models.media._LinkMixin
    :summary:
    ```
* - {py:obj}`SubmissionMediaLink <libweasyl.models.media.SubmissionMediaLink>`
  - ```{autodoc2-docstring} libweasyl.models.media.SubmissionMediaLink
    :summary:
    ```
* - {py:obj}`UserMediaLink <libweasyl.models.media.UserMediaLink>`
  - ```{autodoc2-docstring} libweasyl.models.media.UserMediaLink
    :summary:
    ```
````

### API

`````{py:class} MediaItem
:canonical: libweasyl.models.media.MediaItem

Bases: {py:obj}`libweasyl.models.meta.Base`

```{autodoc2-docstring} libweasyl.models.media.MediaItem
```

````{py:attribute} __table__
:canonical: libweasyl.models.media.MediaItem.__table__
:value: >
   None

```{autodoc2-docstring} libweasyl.models.media.MediaItem.__table__
```

````

````{py:method} fetch_or_create(data, file_type=None, im=None, attributes=())
:canonical: libweasyl.models.media.MediaItem.fetch_or_create
:classmethod:

```{autodoc2-docstring} libweasyl.models.media.MediaItem.fetch_or_create
```

````

````{py:attribute} _media_link_formatter_callback
:canonical: libweasyl.models.media.MediaItem._media_link_formatter_callback
:value: >
   None

```{autodoc2-docstring} libweasyl.models.media.MediaItem._media_link_formatter_callback
```

````

````{py:attribute} _base_file_path
:canonical: libweasyl.models.media.MediaItem._base_file_path
:value: >
   None

```{autodoc2-docstring} libweasyl.models.media.MediaItem._base_file_path
```

````

````{py:method} _to_dict()
:canonical: libweasyl.models.media.MediaItem._to_dict

```{autodoc2-docstring} libweasyl.models.media.MediaItem._to_dict
```

````

````{py:method} serialize(*, link)
:canonical: libweasyl.models.media.MediaItem.serialize

```{autodoc2-docstring} libweasyl.models.media.MediaItem.serialize
```

````

````{py:method} ensure_cover_image(source_image)
:canonical: libweasyl.models.media.MediaItem.ensure_cover_image

```{autodoc2-docstring} libweasyl.models.media.MediaItem.ensure_cover_image
```

````

````{py:property} display_url
:canonical: libweasyl.models.media.MediaItem.display_url

```{autodoc2-docstring} libweasyl.models.media.MediaItem.display_url
```

````

````{py:property} full_file_path
:canonical: libweasyl.models.media.MediaItem.full_file_path

```{autodoc2-docstring} libweasyl.models.media.MediaItem.full_file_path
```

````

````{py:method} as_image()
:canonical: libweasyl.models.media.MediaItem.as_image

```{autodoc2-docstring} libweasyl.models.media.MediaItem.as_image
```

````

````{py:property} _file_path_components
:canonical: libweasyl.models.media.MediaItem._file_path_components

```{autodoc2-docstring} libweasyl.models.media.MediaItem._file_path_components
```

````

````{py:property} file_url
:canonical: libweasyl.models.media.MediaItem.file_url

```{autodoc2-docstring} libweasyl.models.media.MediaItem.file_url
```

````

`````

`````{py:class} _LinkMixin
:canonical: libweasyl.models.media._LinkMixin

```{autodoc2-docstring} libweasyl.models.media._LinkMixin
```

````{py:attribute} cache_func
:canonical: libweasyl.models.media._LinkMixin.cache_func
:value: >
   None

```{autodoc2-docstring} libweasyl.models.media._LinkMixin.cache_func
```

````

````{py:method} refresh_cache(identity)
:canonical: libweasyl.models.media._LinkMixin.refresh_cache
:classmethod:

```{autodoc2-docstring} libweasyl.models.media._LinkMixin.refresh_cache
```

````

````{py:method} clear_link(identity, link_type)
:canonical: libweasyl.models.media._LinkMixin.clear_link
:classmethod:

```{autodoc2-docstring} libweasyl.models.media._LinkMixin.clear_link
```

````

````{py:method} make_or_replace_link(identity, link_type, media_item)
:canonical: libweasyl.models.media._LinkMixin.make_or_replace_link
:classmethod:

```{autodoc2-docstring} libweasyl.models.media._LinkMixin.make_or_replace_link
```

````

````{py:method} bucket_links(identities)
:canonical: libweasyl.models.media._LinkMixin.bucket_links
:classmethod:

```{autodoc2-docstring} libweasyl.models.media._LinkMixin.bucket_links
```

````

````{py:method} register_cache(func)
:canonical: libweasyl.models.media._LinkMixin.register_cache
:classmethod:

```{autodoc2-docstring} libweasyl.models.media._LinkMixin.register_cache
```

````

`````

`````{py:class} SubmissionMediaLink
:canonical: libweasyl.models.media.SubmissionMediaLink

Bases: {py:obj}`libweasyl.models.meta.Base`, {py:obj}`libweasyl.models.media._LinkMixin`

```{autodoc2-docstring} libweasyl.models.media.SubmissionMediaLink
```

````{py:attribute} __table__
:canonical: libweasyl.models.media.SubmissionMediaLink.__table__
:value: >
   None

```{autodoc2-docstring} libweasyl.models.media.SubmissionMediaLink.__table__
```

````

````{py:attribute} _identity
:canonical: libweasyl.models.media.SubmissionMediaLink._identity
:value: >
   'submitid'

```{autodoc2-docstring} libweasyl.models.media.SubmissionMediaLink._identity
```

````

````{py:attribute} submission
:canonical: libweasyl.models.media.SubmissionMediaLink.submission
:value: >
   'relationship(...)'

```{autodoc2-docstring} libweasyl.models.media.SubmissionMediaLink.submission
```

````

````{py:attribute} media_item
:canonical: libweasyl.models.media.SubmissionMediaLink.media_item
:value: >
   'relationship(...)'

```{autodoc2-docstring} libweasyl.models.media.SubmissionMediaLink.media_item
```

````

````{py:method} get_media_query()
:canonical: libweasyl.models.media.SubmissionMediaLink.get_media_query
:classmethod:

```{autodoc2-docstring} libweasyl.models.media.SubmissionMediaLink.get_media_query
```

````

`````

`````{py:class} UserMediaLink
:canonical: libweasyl.models.media.UserMediaLink

Bases: {py:obj}`libweasyl.models.meta.Base`, {py:obj}`libweasyl.models.media._LinkMixin`

```{autodoc2-docstring} libweasyl.models.media.UserMediaLink
```

````{py:attribute} __table__
:canonical: libweasyl.models.media.UserMediaLink.__table__
:value: >
   None

```{autodoc2-docstring} libweasyl.models.media.UserMediaLink.__table__
```

````

````{py:attribute} _identity
:canonical: libweasyl.models.media.UserMediaLink._identity
:value: >
   'userid'

```{autodoc2-docstring} libweasyl.models.media.UserMediaLink._identity
```

````

````{py:attribute} user
:canonical: libweasyl.models.media.UserMediaLink.user
:value: >
   'relationship(...)'

```{autodoc2-docstring} libweasyl.models.media.UserMediaLink.user
```

````

````{py:attribute} media_item
:canonical: libweasyl.models.media.UserMediaLink.media_item
:value: >
   'relationship(...)'

```{autodoc2-docstring} libweasyl.models.media.UserMediaLink.media_item
```

````

````{py:method} get_media_query()
:canonical: libweasyl.models.media.UserMediaLink.get_media_query
:classmethod:

```{autodoc2-docstring} libweasyl.models.media.UserMediaLink.get_media_query
```

````

`````
