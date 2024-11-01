# {py:mod}`weasyl.test.web.test_submissions`

```{py:module} weasyl.test.web.test_submissions
```

```{autodoc2-docstring} weasyl.test.web.test_submissions
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`CrosspostHandler <weasyl.test.web.test_submissions.CrosspostHandler>`
  -
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_image_hash <weasyl.test.web.test_submissions._image_hash>`
  - ```{autodoc2-docstring} weasyl.test.web.test_submissions._image_hash
    :summary:
    ```
* - {py:obj}`test_rating_accessibility <weasyl.test.web.test_submissions.test_rating_accessibility>`
  - ```{autodoc2-docstring} weasyl.test.web.test_submissions.test_rating_accessibility
    :summary:
    ```
* - {py:obj}`test_gif_thumbnail_static <weasyl.test.web.test_submissions.test_gif_thumbnail_static>`
  - ```{autodoc2-docstring} weasyl.test.web.test_submissions.test_gif_thumbnail_static
    :summary:
    ```
* - {py:obj}`test_visual_reupload_thumbnail_and_cover <weasyl.test.web.test_submissions.test_visual_reupload_thumbnail_and_cover>`
  - ```{autodoc2-docstring} weasyl.test.web.test_submissions.test_visual_reupload_thumbnail_and_cover
    :summary:
    ```
* - {py:obj}`test_google_docs_embed_create <weasyl.test.web.test_submissions.test_google_docs_embed_create>`
  - ```{autodoc2-docstring} weasyl.test.web.test_submissions.test_google_docs_embed_create
    :summary:
    ```
* - {py:obj}`test_google_docs_embed_edit <weasyl.test.web.test_submissions.test_google_docs_embed_edit>`
  - ```{autodoc2-docstring} weasyl.test.web.test_submissions.test_google_docs_embed_edit
    :summary:
    ```
* - {py:obj}`test_crosspost <weasyl.test.web.test_submissions.test_crosspost>`
  - ```{autodoc2-docstring} weasyl.test.web.test_submissions.test_crosspost
    :summary:
    ```
* - {py:obj}`test_folder_navigation_sfw_mode <weasyl.test.web.test_submissions.test_folder_navigation_sfw_mode>`
  - ```{autodoc2-docstring} weasyl.test.web.test_submissions.test_folder_navigation_sfw_mode
    :summary:
    ```
````

### API

````{py:function} _image_hash(image)
:canonical: weasyl.test.web.test_submissions._image_hash

```{autodoc2-docstring} weasyl.test.web.test_submissions._image_hash
```
````

````{py:function} test_rating_accessibility(app, age)
:canonical: weasyl.test.web.test_submissions.test_rating_accessibility

```{autodoc2-docstring} weasyl.test.web.test_submissions.test_rating_accessibility
```
````

````{py:function} test_gif_thumbnail_static(app, submission_user)
:canonical: weasyl.test.web.test_submissions.test_gif_thumbnail_static

```{autodoc2-docstring} weasyl.test.web.test_submissions.test_gif_thumbnail_static
```
````

````{py:function} test_visual_reupload_thumbnail_and_cover(app, submission_user)
:canonical: weasyl.test.web.test_submissions.test_visual_reupload_thumbnail_and_cover

```{autodoc2-docstring} weasyl.test.web.test_submissions.test_visual_reupload_thumbnail_and_cover
```
````

````{py:function} test_google_docs_embed_create(app, submission_user, link, normalized)
:canonical: weasyl.test.web.test_submissions.test_google_docs_embed_create

```{autodoc2-docstring} weasyl.test.web.test_submissions.test_google_docs_embed_create
```
````

````{py:function} test_google_docs_embed_edit(app, submission_user)
:canonical: weasyl.test.web.test_submissions.test_google_docs_embed_edit

```{autodoc2-docstring} weasyl.test.web.test_submissions.test_google_docs_embed_edit
```
````

`````{py:class} CrosspostHandler(request, client_address, server)
:canonical: weasyl.test.web.test_submissions.CrosspostHandler

Bases: {py:obj}`http.server.BaseHTTPRequestHandler`

````{py:method} do_GET()
:canonical: weasyl.test.web.test_submissions.CrosspostHandler.do_GET

```{autodoc2-docstring} weasyl.test.web.test_submissions.CrosspostHandler.do_GET
```

````

````{py:method} log_message(format, *args)
:canonical: weasyl.test.web.test_submissions.CrosspostHandler.log_message

````

`````

````{py:function} test_crosspost(app, submission_user, monkeypatch)
:canonical: weasyl.test.web.test_submissions.test_crosspost

```{autodoc2-docstring} weasyl.test.web.test_submissions.test_crosspost
```
````

````{py:function} test_folder_navigation_sfw_mode(app, submission_user)
:canonical: weasyl.test.web.test_submissions.test_folder_navigation_sfw_mode

```{autodoc2-docstring} weasyl.test.web.test_submissions.test_folder_navigation_sfw_mode
```
````
