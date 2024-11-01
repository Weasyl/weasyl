# {py:mod}`libweasyl.cache`

```{py:module} libweasyl.cache
```

```{autodoc2-docstring} libweasyl.cache
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`ThreadCacheProxy <libweasyl.cache.ThreadCacheProxy>`
  - ```{autodoc2-docstring} libweasyl.cache.ThreadCacheProxy
    :summary:
    ```
* - {py:obj}`JsonClient <libweasyl.cache.JsonClient>`
  - ```{autodoc2-docstring} libweasyl.cache.JsonClient
    :summary:
    ```
* - {py:obj}`JsonPylibmcBackend <libweasyl.cache.JsonPylibmcBackend>`
  - ```{autodoc2-docstring} libweasyl.cache.JsonPylibmcBackend
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`region <libweasyl.cache.region>`
  - ```{autodoc2-docstring} libweasyl.cache.region
    :summary:
    ```
````

### API

````{py:data} region
:canonical: libweasyl.cache.region
:value: >
   'make_region(...)'

```{autodoc2-docstring} libweasyl.cache.region
```

````

`````{py:class} ThreadCacheProxy
:canonical: libweasyl.cache.ThreadCacheProxy

Bases: {py:obj}`dogpile.cache.proxy.ProxyBackend`

```{autodoc2-docstring} libweasyl.cache.ThreadCacheProxy
```

````{py:attribute} _local
:canonical: libweasyl.cache.ThreadCacheProxy._local
:value: >
   'local(...)'

```{autodoc2-docstring} libweasyl.cache.ThreadCacheProxy._local
```

````

````{py:method} zap_cache()
:canonical: libweasyl.cache.ThreadCacheProxy.zap_cache
:classmethod:

```{autodoc2-docstring} libweasyl.cache.ThreadCacheProxy.zap_cache
```

````

````{py:property} _dict
:canonical: libweasyl.cache.ThreadCacheProxy._dict

```{autodoc2-docstring} libweasyl.cache.ThreadCacheProxy._dict
```

````

````{py:method} get(key)
:canonical: libweasyl.cache.ThreadCacheProxy.get

```{autodoc2-docstring} libweasyl.cache.ThreadCacheProxy.get
```

````

````{py:method} get_multi(keys)
:canonical: libweasyl.cache.ThreadCacheProxy.get_multi

```{autodoc2-docstring} libweasyl.cache.ThreadCacheProxy.get_multi
```

````

````{py:method} set(key, value)
:canonical: libweasyl.cache.ThreadCacheProxy.set

```{autodoc2-docstring} libweasyl.cache.ThreadCacheProxy.set
```

````

````{py:method} set_multi(pairs)
:canonical: libweasyl.cache.ThreadCacheProxy.set_multi

```{autodoc2-docstring} libweasyl.cache.ThreadCacheProxy.set_multi
```

````

````{py:method} delete(key)
:canonical: libweasyl.cache.ThreadCacheProxy.delete

```{autodoc2-docstring} libweasyl.cache.ThreadCacheProxy.delete
```

````

````{py:method} delete_multi(keys)
:canonical: libweasyl.cache.ThreadCacheProxy.delete_multi

```{autodoc2-docstring} libweasyl.cache.ThreadCacheProxy.delete_multi
```

````

`````

`````{py:class} JsonClient
:canonical: libweasyl.cache.JsonClient

Bases: {py:obj}`pylibmc.Client`

```{autodoc2-docstring} libweasyl.cache.JsonClient
```

````{py:method} serialize(value)
:canonical: libweasyl.cache.JsonClient.serialize

```{autodoc2-docstring} libweasyl.cache.JsonClient.serialize
```

````

````{py:method} deserialize(bytestring, flag)
:canonical: libweasyl.cache.JsonClient.deserialize

```{autodoc2-docstring} libweasyl.cache.JsonClient.deserialize
```

````

`````

`````{py:class} JsonPylibmcBackend
:canonical: libweasyl.cache.JsonPylibmcBackend

Bases: {py:obj}`dogpile.cache.backends.memcached.PylibmcBackend`

```{autodoc2-docstring} libweasyl.cache.JsonPylibmcBackend
```

````{py:method} _imports()
:canonical: libweasyl.cache.JsonPylibmcBackend._imports

```{autodoc2-docstring} libweasyl.cache.JsonPylibmcBackend._imports
```

````

````{py:method} _create_client()
:canonical: libweasyl.cache.JsonPylibmcBackend._create_client

```{autodoc2-docstring} libweasyl.cache.JsonPylibmcBackend._create_client
```

````

````{py:method} register()
:canonical: libweasyl.cache.JsonPylibmcBackend.register
:classmethod:

```{autodoc2-docstring} libweasyl.cache.JsonPylibmcBackend.register
```

````

`````
