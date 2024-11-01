# {py:mod}`weasyl.test.test_journal`

```{py:module} weasyl.test.test_journal
```

```{autodoc2-docstring} weasyl.test.test_journal
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`SelectUserCountTestCase <weasyl.test.test_journal.SelectUserCountTestCase>`
  -
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`select_user_count <weasyl.test.test_journal.select_user_count>`
  - ```{autodoc2-docstring} weasyl.test.test_journal.select_user_count
    :summary:
    ```
````

### API

````{py:function} select_user_count(userid, rating, **kwargs)
:canonical: weasyl.test.test_journal.select_user_count

```{autodoc2-docstring} weasyl.test.test_journal.select_user_count
```
````

`````{py:class} SelectUserCountTestCase(methodName='runTest')
:canonical: weasyl.test.test_journal.SelectUserCountTestCase

Bases: {py:obj}`unittest.TestCase`

````{py:method} setUp()
:canonical: weasyl.test.test_journal.SelectUserCountTestCase.setUp

````

````{py:method} test_count_backid()
:canonical: weasyl.test.test_journal.SelectUserCountTestCase.test_count_backid

```{autodoc2-docstring} weasyl.test.test_journal.SelectUserCountTestCase.test_count_backid
```

````

````{py:method} test_count_nextid()
:canonical: weasyl.test.test_journal.SelectUserCountTestCase.test_count_nextid

```{autodoc2-docstring} weasyl.test.test_journal.SelectUserCountTestCase.test_count_nextid
```

````

````{py:method} test_see_friends_journal()
:canonical: weasyl.test.test_journal.SelectUserCountTestCase.test_see_friends_journal

```{autodoc2-docstring} weasyl.test.test_journal.SelectUserCountTestCase.test_see_friends_journal
```

````

````{py:method} test_cannot_see_non_friends_journal()
:canonical: weasyl.test.test_journal.SelectUserCountTestCase.test_cannot_see_non_friends_journal

```{autodoc2-docstring} weasyl.test.test_journal.SelectUserCountTestCase.test_cannot_see_non_friends_journal
```

````

````{py:method} test_can_see_own_blocktag_journal()
:canonical: weasyl.test.test_journal.SelectUserCountTestCase.test_can_see_own_blocktag_journal

```{autodoc2-docstring} weasyl.test.test_journal.SelectUserCountTestCase.test_can_see_own_blocktag_journal
```

````

````{py:method} test_can_see_own_rating_journal()
:canonical: weasyl.test.test_journal.SelectUserCountTestCase.test_can_see_own_rating_journal

```{autodoc2-docstring} weasyl.test.test_journal.SelectUserCountTestCase.test_can_see_own_rating_journal
```

````

````{py:method} test_remove()
:canonical: weasyl.test.test_journal.SelectUserCountTestCase.test_remove

```{autodoc2-docstring} weasyl.test.test_journal.SelectUserCountTestCase.test_remove
```

````

`````
