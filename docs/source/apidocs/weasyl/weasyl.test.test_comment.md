# {py:mod}`weasyl.test.test_comment`

```{py:module} weasyl.test.test_comment
```

```{autodoc2-docstring} weasyl.test.test_comment
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`TestRemoveComment <weasyl.test.test_comment.TestRemoveComment>`
  - ```{autodoc2-docstring} weasyl.test.test_comment.TestRemoveComment
    :summary:
    ```
* - {py:obj}`CheckNotificationsTestCase <weasyl.test.test_comment.CheckNotificationsTestCase>`
  -
````

### API

`````{py:class} TestRemoveComment
:canonical: weasyl.test.test_comment.TestRemoveComment

```{autodoc2-docstring} weasyl.test.test_comment.TestRemoveComment
```

````{py:attribute} generation_parameters
:canonical: weasyl.test.test_comment.TestRemoveComment.generation_parameters
:value: >
   [('submit',), ('journal',), ('char',), (None,)]

```{autodoc2-docstring} weasyl.test.test_comment.TestRemoveComment.generation_parameters
```

````

````{py:method} setUp(request, monkeypatch)
:canonical: weasyl.test.test_comment.TestRemoveComment.setUp

```{autodoc2-docstring} weasyl.test.test_comment.TestRemoveComment.setUp
```

````

````{py:method} test_commenter_can_remove()
:canonical: weasyl.test.test_comment.TestRemoveComment.test_commenter_can_remove

```{autodoc2-docstring} weasyl.test.test_comment.TestRemoveComment.test_commenter_can_remove
```

````

````{py:method} test_commenter_can_not_remove_with_replies()
:canonical: weasyl.test.test_comment.TestRemoveComment.test_commenter_can_not_remove_with_replies

```{autodoc2-docstring} weasyl.test.test_comment.TestRemoveComment.test_commenter_can_not_remove_with_replies
```

````

````{py:method} test_owner_can_remove()
:canonical: weasyl.test.test_comment.TestRemoveComment.test_owner_can_remove

```{autodoc2-docstring} weasyl.test.test_comment.TestRemoveComment.test_owner_can_remove
```

````

````{py:method} test_mod_can_remove()
:canonical: weasyl.test.test_comment.TestRemoveComment.test_mod_can_remove

```{autodoc2-docstring} weasyl.test.test_comment.TestRemoveComment.test_mod_can_remove
```

````

````{py:method} test_other_user_can_not_remove()
:canonical: weasyl.test.test_comment.TestRemoveComment.test_other_user_can_not_remove

```{autodoc2-docstring} weasyl.test.test_comment.TestRemoveComment.test_other_user_can_not_remove
```

````

`````

`````{py:class} CheckNotificationsTestCase(methodName='runTest')
:canonical: weasyl.test.test_comment.CheckNotificationsTestCase

Bases: {py:obj}`unittest.TestCase`

````{py:method} setUp()
:canonical: weasyl.test.test_comment.CheckNotificationsTestCase.setUp

````

````{py:method} count_notifications(user)
:canonical: weasyl.test.test_comment.CheckNotificationsTestCase.count_notifications

```{autodoc2-docstring} weasyl.test.test_comment.CheckNotificationsTestCase.count_notifications
```

````

````{py:method} add_and_remove_comments(feature, **kwargs)
:canonical: weasyl.test.test_comment.CheckNotificationsTestCase.add_and_remove_comments

```{autodoc2-docstring} weasyl.test.test_comment.CheckNotificationsTestCase.add_and_remove_comments
```

````

````{py:method} test_add_and_remove_submission()
:canonical: weasyl.test.test_comment.CheckNotificationsTestCase.test_add_and_remove_submission

```{autodoc2-docstring} weasyl.test.test_comment.CheckNotificationsTestCase.test_add_and_remove_submission
```

````

````{py:method} test_add_and_remove_journal()
:canonical: weasyl.test.test_comment.CheckNotificationsTestCase.test_add_and_remove_journal

```{autodoc2-docstring} weasyl.test.test_comment.CheckNotificationsTestCase.test_add_and_remove_journal
```

````

````{py:method} test_add_and_remove_character()
:canonical: weasyl.test.test_comment.CheckNotificationsTestCase.test_add_and_remove_character

```{autodoc2-docstring} weasyl.test.test_comment.CheckNotificationsTestCase.test_add_and_remove_character
```

````

````{py:method} test_add_and_remove_shout()
:canonical: weasyl.test.test_comment.CheckNotificationsTestCase.test_add_and_remove_shout

```{autodoc2-docstring} weasyl.test.test_comment.CheckNotificationsTestCase.test_add_and_remove_shout
```

````

`````
