# {py:mod}`weasyl.middleware`

```{py:module} weasyl.middleware
```

```{autodoc2-docstring} weasyl.middleware
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`FieldStorage <weasyl.middleware.FieldStorage>`
  - ```{autodoc2-docstring} weasyl.middleware.FieldStorage
    :summary:
    ```
* - {py:obj}`Request <weasyl.middleware.Request>`
  - ```{autodoc2-docstring} weasyl.middleware.Request
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`utf8_path_tween_factory <weasyl.middleware.utf8_path_tween_factory>`
  - ```{autodoc2-docstring} weasyl.middleware.utf8_path_tween_factory
    :summary:
    ```
* - {py:obj}`cache_clear_tween_factory <weasyl.middleware.cache_clear_tween_factory>`
  - ```{autodoc2-docstring} weasyl.middleware.cache_clear_tween_factory
    :summary:
    ```
* - {py:obj}`db_timer_tween_factory <weasyl.middleware.db_timer_tween_factory>`
  - ```{autodoc2-docstring} weasyl.middleware.db_timer_tween_factory
    :summary:
    ```
* - {py:obj}`session_tween_factory <weasyl.middleware.session_tween_factory>`
  - ```{autodoc2-docstring} weasyl.middleware.session_tween_factory
    :summary:
    ```
* - {py:obj}`query_debug_tween_factory <weasyl.middleware.query_debug_tween_factory>`
  - ```{autodoc2-docstring} weasyl.middleware.query_debug_tween_factory
    :summary:
    ```
* - {py:obj}`status_check_tween_factory <weasyl.middleware.status_check_tween_factory>`
  - ```{autodoc2-docstring} weasyl.middleware.status_check_tween_factory
    :summary:
    ```
* - {py:obj}`database_session_cleanup_tween_factory <weasyl.middleware.database_session_cleanup_tween_factory>`
  - ```{autodoc2-docstring} weasyl.middleware.database_session_cleanup_tween_factory
    :summary:
    ```
* - {py:obj}`_generate_http2_server_push_headers <weasyl.middleware._generate_http2_server_push_headers>`
  - ```{autodoc2-docstring} weasyl.middleware._generate_http2_server_push_headers
    :summary:
    ```
* - {py:obj}`http2_server_push_tween_factory <weasyl.middleware.http2_server_push_tween_factory>`
  - ```{autodoc2-docstring} weasyl.middleware.http2_server_push_tween_factory
    :summary:
    ```
* - {py:obj}`pg_connection_request_property <weasyl.middleware.pg_connection_request_property>`
  - ```{autodoc2-docstring} weasyl.middleware.pg_connection_request_property
    :summary:
    ```
* - {py:obj}`userid_request_property <weasyl.middleware.userid_request_property>`
  - ```{autodoc2-docstring} weasyl.middleware.userid_request_property
    :summary:
    ```
* - {py:obj}`web_input_request_method <weasyl.middleware.web_input_request_method>`
  - ```{autodoc2-docstring} weasyl.middleware.web_input_request_method
    :summary:
    ```
* - {py:obj}`_redact_match <weasyl.middleware._redact_match>`
  - ```{autodoc2-docstring} weasyl.middleware._redact_match
    :summary:
    ```
* - {py:obj}`_log_request <weasyl.middleware._log_request>`
  - ```{autodoc2-docstring} weasyl.middleware._log_request
    :summary:
    ```
* - {py:obj}`weasyl_exception_view <weasyl.middleware.weasyl_exception_view>`
  - ```{autodoc2-docstring} weasyl.middleware.weasyl_exception_view
    :summary:
    ```
* - {py:obj}`before_cursor_execute <weasyl.middleware.before_cursor_execute>`
  - ```{autodoc2-docstring} weasyl.middleware.before_cursor_execute
    :summary:
    ```
* - {py:obj}`after_cursor_execute <weasyl.middleware.after_cursor_execute>`
  - ```{autodoc2-docstring} weasyl.middleware.after_cursor_execute
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_CLIENT_MAX_BODY_SIZE <weasyl.middleware._CLIENT_MAX_BODY_SIZE>`
  - ```{autodoc2-docstring} weasyl.middleware._CLIENT_MAX_BODY_SIZE
    :summary:
    ```
* - {py:obj}`request_duration <weasyl.middleware.request_duration>`
  - ```{autodoc2-docstring} weasyl.middleware.request_duration
    :summary:
    ```
* - {py:obj}`HTTP2_LINK_HEADER_PRELOADS <weasyl.middleware.HTTP2_LINK_HEADER_PRELOADS>`
  - ```{autodoc2-docstring} weasyl.middleware.HTTP2_LINK_HEADER_PRELOADS
    :summary:
    ```
````

### API

````{py:data} _CLIENT_MAX_BODY_SIZE
:canonical: weasyl.middleware._CLIENT_MAX_BODY_SIZE
:value: >
   None

```{autodoc2-docstring} weasyl.middleware._CLIENT_MAX_BODY_SIZE
```

````

`````{py:class} FieldStorage(multipart_part, /)
:canonical: weasyl.middleware.FieldStorage

```{autodoc2-docstring} weasyl.middleware.FieldStorage
```

```{rubric} Initialization
```

```{autodoc2-docstring} weasyl.middleware.FieldStorage.__init__
```

````{py:method} __getattr__(name)
:canonical: weasyl.middleware.FieldStorage.__getattr__

```{autodoc2-docstring} weasyl.middleware.FieldStorage.__getattr__
```

````

````{py:property} value
:canonical: weasyl.middleware.FieldStorage.value

```{autodoc2-docstring} weasyl.middleware.FieldStorage.value
```

````

`````

`````{py:class} Request
:canonical: weasyl.middleware.Request

Bases: {py:obj}`pyramid.request.Request`

```{autodoc2-docstring} weasyl.middleware.Request
```

````{py:property} request_body_tempfile_limit
:canonical: weasyl.middleware.Request.request_body_tempfile_limit
:abstractmethod:

```{autodoc2-docstring} weasyl.middleware.Request.request_body_tempfile_limit
```

````

````{py:method} decode()
:canonical: weasyl.middleware.Request.decode
:abstractmethod:

```{autodoc2-docstring} weasyl.middleware.Request.decode
```

````

````{py:property} body_file
:canonical: weasyl.middleware.Request.body_file

```{autodoc2-docstring} weasyl.middleware.Request.body_file
```

````

````{py:property} body_file_seekable
:canonical: weasyl.middleware.Request.body_file_seekable
:abstractmethod:

```{autodoc2-docstring} weasyl.middleware.Request.body_file_seekable
```

````

````{py:property} body
:canonical: weasyl.middleware.Request.body

```{autodoc2-docstring} weasyl.middleware.Request.body
```

````

````{py:method} POST()
:canonical: weasyl.middleware.Request.POST

```{autodoc2-docstring} weasyl.middleware.Request.POST
```

````

````{py:method} copy()
:canonical: weasyl.middleware.Request.copy
:abstractmethod:

```{autodoc2-docstring} weasyl.middleware.Request.copy
```

````

````{py:property} is_body_seekable
:canonical: weasyl.middleware.Request.is_body_seekable

```{autodoc2-docstring} weasyl.middleware.Request.is_body_seekable
```

````

````{py:method} make_body_seekable()
:canonical: weasyl.middleware.Request.make_body_seekable
:abstractmethod:

```{autodoc2-docstring} weasyl.middleware.Request.make_body_seekable
```

````

````{py:method} copy_body()
:canonical: weasyl.middleware.Request.copy_body
:abstractmethod:

```{autodoc2-docstring} weasyl.middleware.Request.copy_body
```

````

````{py:method} make_tempfile()
:canonical: weasyl.middleware.Request.make_tempfile
:abstractmethod:

```{autodoc2-docstring} weasyl.middleware.Request.make_tempfile
```

````

`````

````{py:function} utf8_path_tween_factory(handler, registry)
:canonical: weasyl.middleware.utf8_path_tween_factory

```{autodoc2-docstring} weasyl.middleware.utf8_path_tween_factory
```
````

````{py:function} cache_clear_tween_factory(handler, registry)
:canonical: weasyl.middleware.cache_clear_tween_factory

```{autodoc2-docstring} weasyl.middleware.cache_clear_tween_factory
```
````

````{py:data} request_duration
:canonical: weasyl.middleware.request_duration
:value: >
   'Histogram(...)'

```{autodoc2-docstring} weasyl.middleware.request_duration
```

````

````{py:function} db_timer_tween_factory(handler, registry)
:canonical: weasyl.middleware.db_timer_tween_factory

```{autodoc2-docstring} weasyl.middleware.db_timer_tween_factory
```
````

````{py:function} session_tween_factory(handler, registry)
:canonical: weasyl.middleware.session_tween_factory

```{autodoc2-docstring} weasyl.middleware.session_tween_factory
```
````

````{py:function} query_debug_tween_factory(handler, registry)
:canonical: weasyl.middleware.query_debug_tween_factory

```{autodoc2-docstring} weasyl.middleware.query_debug_tween_factory
```
````

````{py:function} status_check_tween_factory(handler, registry)
:canonical: weasyl.middleware.status_check_tween_factory

```{autodoc2-docstring} weasyl.middleware.status_check_tween_factory
```
````

````{py:function} database_session_cleanup_tween_factory(handler, registry)
:canonical: weasyl.middleware.database_session_cleanup_tween_factory

```{autodoc2-docstring} weasyl.middleware.database_session_cleanup_tween_factory
```
````

````{py:function} _generate_http2_server_push_headers()
:canonical: weasyl.middleware._generate_http2_server_push_headers

```{autodoc2-docstring} weasyl.middleware._generate_http2_server_push_headers
```
````

````{py:data} HTTP2_LINK_HEADER_PRELOADS
:canonical: weasyl.middleware.HTTP2_LINK_HEADER_PRELOADS
:value: >
   '_generate_http2_server_push_headers(...)'

```{autodoc2-docstring} weasyl.middleware.HTTP2_LINK_HEADER_PRELOADS
```

````

````{py:function} http2_server_push_tween_factory(handler, registry)
:canonical: weasyl.middleware.http2_server_push_tween_factory

```{autodoc2-docstring} weasyl.middleware.http2_server_push_tween_factory
```
````

````{py:function} pg_connection_request_property(request)
:canonical: weasyl.middleware.pg_connection_request_property

```{autodoc2-docstring} weasyl.middleware.pg_connection_request_property
```
````

````{py:function} userid_request_property(request)
:canonical: weasyl.middleware.userid_request_property

```{autodoc2-docstring} weasyl.middleware.userid_request_property
```
````

````{py:function} web_input_request_method(request, *required, **kwargs)
:canonical: weasyl.middleware.web_input_request_method

```{autodoc2-docstring} weasyl.middleware.web_input_request_method
```
````

````{py:function} _redact_match(match)
:canonical: weasyl.middleware._redact_match

```{autodoc2-docstring} weasyl.middleware._redact_match
```
````

````{py:function} _log_request(request, *, request_id=None)
:canonical: weasyl.middleware._log_request

```{autodoc2-docstring} weasyl.middleware._log_request
```
````

````{py:function} weasyl_exception_view(exc, request)
:canonical: weasyl.middleware.weasyl_exception_view

```{autodoc2-docstring} weasyl.middleware.weasyl_exception_view
```
````

````{py:function} before_cursor_execute(conn, cursor, statement, parameters, context, executemany)
:canonical: weasyl.middleware.before_cursor_execute

```{autodoc2-docstring} weasyl.middleware.before_cursor_execute
```
````

````{py:function} after_cursor_execute(conn, cursor, statement, parameters, context, executemany)
:canonical: weasyl.middleware.after_cursor_execute

```{autodoc2-docstring} weasyl.middleware.after_cursor_execute
```
````
