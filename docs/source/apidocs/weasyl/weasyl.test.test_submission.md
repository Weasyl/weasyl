# {py:mod}`weasyl.test.test_submission`

```{py:module} weasyl.test.test_submission
```

```{autodoc2-docstring} weasyl.test.test_submission
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`SelectListTestCase <weasyl.test.test_submission.SelectListTestCase>`
  -
* - {py:obj}`SelectCountTestCase <weasyl.test.test_submission.SelectCountTestCase>`
  -
* - {py:obj}`SubmissionNotificationsTestCase <weasyl.test.test_submission.SubmissionNotificationsTestCase>`
  - ```{autodoc2-docstring} weasyl.test.test_submission.SubmissionNotificationsTestCase
    :summary:
    ```
````

### API

`````{py:class} SelectListTestCase(methodName='runTest')
:canonical: weasyl.test.test_submission.SelectListTestCase

Bases: {py:obj}`unittest.TestCase`

````{py:method} test_ratings()
:canonical: weasyl.test.test_submission.SelectListTestCase.test_ratings

```{autodoc2-docstring} weasyl.test.test_submission.SelectListTestCase.test_ratings
```

````

````{py:method} test_filters()
:canonical: weasyl.test.test_submission.SelectListTestCase.test_filters

```{autodoc2-docstring} weasyl.test.test_submission.SelectListTestCase.test_filters
```

````

````{py:method} test_select_list_limits()
:canonical: weasyl.test.test_submission.SelectListTestCase.test_select_list_limits

```{autodoc2-docstring} weasyl.test.test_submission.SelectListTestCase.test_select_list_limits
```

````

````{py:method} test_friends_only()
:canonical: weasyl.test.test_submission.SelectListTestCase.test_friends_only

```{autodoc2-docstring} weasyl.test.test_submission.SelectListTestCase.test_friends_only
```

````

````{py:method} test_ignored_user()
:canonical: weasyl.test.test_submission.SelectListTestCase.test_ignored_user

```{autodoc2-docstring} weasyl.test.test_submission.SelectListTestCase.test_ignored_user
```

````

````{py:method} test_blocked_tag()
:canonical: weasyl.test.test_submission.SelectListTestCase.test_blocked_tag

```{autodoc2-docstring} weasyl.test.test_submission.SelectListTestCase.test_blocked_tag
```

````

````{py:method} test_duplicate_blocked_tag()
:canonical: weasyl.test.test_submission.SelectListTestCase.test_duplicate_blocked_tag

```{autodoc2-docstring} weasyl.test.test_submission.SelectListTestCase.test_duplicate_blocked_tag
```

````

````{py:method} test_profile_page_filter()
:canonical: weasyl.test.test_submission.SelectListTestCase.test_profile_page_filter

```{autodoc2-docstring} weasyl.test.test_submission.SelectListTestCase.test_profile_page_filter
```

````

````{py:method} test_index_page_filter()
:canonical: weasyl.test.test_submission.SelectListTestCase.test_index_page_filter

```{autodoc2-docstring} weasyl.test.test_submission.SelectListTestCase.test_index_page_filter
```

````

````{py:method} test_feature_page_filter()
:canonical: weasyl.test.test_submission.SelectListTestCase.test_feature_page_filter

```{autodoc2-docstring} weasyl.test.test_submission.SelectListTestCase.test_feature_page_filter
```

````

````{py:method} test_retag()
:canonical: weasyl.test.test_submission.SelectListTestCase.test_retag

```{autodoc2-docstring} weasyl.test.test_submission.SelectListTestCase.test_retag
```

````

````{py:method} test_recently_popular()
:canonical: weasyl.test.test_submission.SelectListTestCase.test_recently_popular

```{autodoc2-docstring} weasyl.test.test_submission.SelectListTestCase.test_recently_popular
```

````

`````

`````{py:class} SelectCountTestCase(methodName='runTest')
:canonical: weasyl.test.test_submission.SelectCountTestCase

Bases: {py:obj}`unittest.TestCase`

````{py:method} setUp()
:canonical: weasyl.test.test_submission.SelectCountTestCase.setUp

````

````{py:method} test_count()
:canonical: weasyl.test.test_submission.SelectCountTestCase.test_count

```{autodoc2-docstring} weasyl.test.test_submission.SelectCountTestCase.test_count
```

````

````{py:method} test_count_backid()
:canonical: weasyl.test.test_submission.SelectCountTestCase.test_count_backid

```{autodoc2-docstring} weasyl.test.test_submission.SelectCountTestCase.test_count_backid
```

````

````{py:method} test_count_nextid()
:canonical: weasyl.test.test_submission.SelectCountTestCase.test_count_nextid

```{autodoc2-docstring} weasyl.test.test_submission.SelectCountTestCase.test_count_nextid
```

````

`````

`````{py:class} SubmissionNotificationsTestCase(methodName='runTest')
:canonical: weasyl.test.test_submission.SubmissionNotificationsTestCase

Bases: {py:obj}`unittest.TestCase`

```{autodoc2-docstring} weasyl.test.test_submission.SubmissionNotificationsTestCase
```

```{rubric} Initialization
```

```{autodoc2-docstring} weasyl.test.test_submission.SubmissionNotificationsTestCase.__init__
```

````{py:method} setUp()
:canonical: weasyl.test.test_submission.SubmissionNotificationsTestCase.setUp

````

````{py:method} _notification_count(userid)
:canonical: weasyl.test.test_submission.SubmissionNotificationsTestCase._notification_count

```{autodoc2-docstring} weasyl.test.test_submission.SubmissionNotificationsTestCase._notification_count
```

````

````{py:method} test_simple_submission()
:canonical: weasyl.test.test_submission.SubmissionNotificationsTestCase.test_simple_submission

```{autodoc2-docstring} weasyl.test.test_submission.SubmissionNotificationsTestCase.test_simple_submission
```

````

````{py:method} test_friends_only_submission()
:canonical: weasyl.test.test_submission.SubmissionNotificationsTestCase.test_friends_only_submission

```{autodoc2-docstring} weasyl.test.test_submission.SubmissionNotificationsTestCase.test_friends_only_submission
```

````

````{py:method} test_submission_becomes_friends_only()
:canonical: weasyl.test.test_submission.SubmissionNotificationsTestCase.test_submission_becomes_friends_only

```{autodoc2-docstring} weasyl.test.test_submission.SubmissionNotificationsTestCase.test_submission_becomes_friends_only
```

````

`````
