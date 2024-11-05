# {py:mod}`weasyl.test.test_collection`

```{py:module} weasyl.test.test_collection
```

```{autodoc2-docstring} weasyl.test.test_collection
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`Counts <weasyl.test.test_collection.Counts>`
  - ```{autodoc2-docstring} weasyl.test.test_collection.Counts
    :summary:
    ```
* - {py:obj}`CollectionsTestCase <weasyl.test.test_collection.CollectionsTestCase>`
  -
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_test_decide_unrelated <weasyl.test.test_collection._test_decide_unrelated>`
  - ```{autodoc2-docstring} weasyl.test.test_collection._test_decide_unrelated
    :summary:
    ```
````

### API

`````{py:class} Counts
:canonical: weasyl.test.test_collection.Counts

```{autodoc2-docstring} weasyl.test.test_collection.Counts
```

````{py:attribute} active
:canonical: weasyl.test.test_collection.Counts.active
:type: int
:value: >
   None

```{autodoc2-docstring} weasyl.test.test_collection.Counts.active
```

````

````{py:attribute} pending
:canonical: weasyl.test.test_collection.Counts.pending
:type: int
:value: >
   None

```{autodoc2-docstring} weasyl.test.test_collection.Counts.pending
```

````

`````

````{py:function} _test_decide_unrelated(decide)
:canonical: weasyl.test.test_collection._test_decide_unrelated

```{autodoc2-docstring} weasyl.test.test_collection._test_decide_unrelated
```
````

`````{py:class} CollectionsTestCase(methodName='runTest')
:canonical: weasyl.test.test_collection.CollectionsTestCase

Bases: {py:obj}`unittest.TestCase`

````{py:method} setUp()
:canonical: weasyl.test.test_collection.CollectionsTestCase.setUp

````

````{py:method} offer()
:canonical: weasyl.test.test_collection.CollectionsTestCase.offer

```{autodoc2-docstring} weasyl.test.test_collection.CollectionsTestCase.offer
```

````

````{py:method} request()
:canonical: weasyl.test.test_collection.CollectionsTestCase.request

```{autodoc2-docstring} weasyl.test.test_collection.CollectionsTestCase.request
```

````

````{py:method} count_collections(userid)
:canonical: weasyl.test.test_collection.CollectionsTestCase.count_collections

```{autodoc2-docstring} weasyl.test.test_collection.CollectionsTestCase.count_collections
```

````

````{py:method} test_offer_and_accept()
:canonical: weasyl.test.test_collection.CollectionsTestCase.test_offer_and_accept

```{autodoc2-docstring} weasyl.test.test_collection.CollectionsTestCase.test_offer_and_accept
```

````

````{py:method} test_offer_with_errors()
:canonical: weasyl.test.test_collection.CollectionsTestCase.test_offer_with_errors

```{autodoc2-docstring} weasyl.test.test_collection.CollectionsTestCase.test_offer_with_errors
```

````

````{py:method} test_offer_and_reject()
:canonical: weasyl.test.test_collection.CollectionsTestCase.test_offer_and_reject

```{autodoc2-docstring} weasyl.test.test_collection.CollectionsTestCase.test_offer_and_reject
```

````

````{py:method} test_offer_accept_and_remove()
:canonical: weasyl.test.test_collection.CollectionsTestCase.test_offer_accept_and_remove

```{autodoc2-docstring} weasyl.test.test_collection.CollectionsTestCase.test_offer_accept_and_remove
```

````

````{py:method} test_offer_and_impersonate_accept()
:canonical: weasyl.test.test_collection.CollectionsTestCase.test_offer_and_impersonate_accept

```{autodoc2-docstring} weasyl.test.test_collection.CollectionsTestCase.test_offer_and_impersonate_accept
```

````

````{py:method} test_request_and_accept()
:canonical: weasyl.test.test_collection.CollectionsTestCase.test_request_and_accept

```{autodoc2-docstring} weasyl.test.test_collection.CollectionsTestCase.test_request_and_accept
```

````

````{py:method} test_request_and_impersonate_accept()
:canonical: weasyl.test.test_collection.CollectionsTestCase.test_request_and_impersonate_accept

```{autodoc2-docstring} weasyl.test.test_collection.CollectionsTestCase.test_request_and_impersonate_accept
```

````

````{py:attribute} test_accept_unrelated
:canonical: weasyl.test.test_collection.CollectionsTestCase.test_accept_unrelated
:value: >
   '_test_decide_unrelated(...)'

```{autodoc2-docstring} weasyl.test.test_collection.CollectionsTestCase.test_accept_unrelated
```

````

````{py:attribute} test_reject_unrelated
:canonical: weasyl.test.test_collection.CollectionsTestCase.test_reject_unrelated
:value: >
   '_test_decide_unrelated(...)'

```{autodoc2-docstring} weasyl.test.test_collection.CollectionsTestCase.test_reject_unrelated
```

````

````{py:method} test_duplicate_offer()
:canonical: weasyl.test.test_collection.CollectionsTestCase.test_duplicate_offer

```{autodoc2-docstring} weasyl.test.test_collection.CollectionsTestCase.test_duplicate_offer
```

````

````{py:method} test_duplicate_request()
:canonical: weasyl.test.test_collection.CollectionsTestCase.test_duplicate_request

```{autodoc2-docstring} weasyl.test.test_collection.CollectionsTestCase.test_duplicate_request
```

````

````{py:method} test_offer_and_request()
:canonical: weasyl.test.test_collection.CollectionsTestCase.test_offer_and_request

```{autodoc2-docstring} weasyl.test.test_collection.CollectionsTestCase.test_offer_and_request
```

````

`````
