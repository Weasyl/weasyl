# {py:mod}`weasyl.cache`

```{py:module} weasyl.cache
```

```{autodoc2-docstring} weasyl.cache
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`RequestMemcachedStats <weasyl.cache.RequestMemcachedStats>`
  - ```{autodoc2-docstring} weasyl.cache.RequestMemcachedStats
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_increments <weasyl.cache._increments>`
  - ```{autodoc2-docstring} weasyl.cache._increments
    :summary:
    ```
````

### API

````{py:function} _increments(func)
:canonical: weasyl.cache._increments

```{autodoc2-docstring} weasyl.cache._increments
```
````

`````{py:class} RequestMemcachedStats
:canonical: weasyl.cache.RequestMemcachedStats

Bases: {py:obj}`dogpile.cache.proxy.ProxyBackend`

```{autodoc2-docstring} weasyl.cache.RequestMemcachedStats
```

````{py:method} delete(key)
:canonical: weasyl.cache.RequestMemcachedStats.delete

```{autodoc2-docstring} weasyl.cache.RequestMemcachedStats.delete
```

````

````{py:method} delete_multi(keys)
:canonical: weasyl.cache.RequestMemcachedStats.delete_multi

```{autodoc2-docstring} weasyl.cache.RequestMemcachedStats.delete_multi
```

````

````{py:method} get(key)
:canonical: weasyl.cache.RequestMemcachedStats.get

```{autodoc2-docstring} weasyl.cache.RequestMemcachedStats.get
```

````

````{py:method} get_multi(keys)
:canonical: weasyl.cache.RequestMemcachedStats.get_multi

```{autodoc2-docstring} weasyl.cache.RequestMemcachedStats.get_multi
```

````

````{py:method} set(key, value)
:canonical: weasyl.cache.RequestMemcachedStats.set

```{autodoc2-docstring} weasyl.cache.RequestMemcachedStats.set
```

````

````{py:method} set_multi(mapping)
:canonical: weasyl.cache.RequestMemcachedStats.set_multi

```{autodoc2-docstring} weasyl.cache.RequestMemcachedStats.set_multi
```

````

`````
