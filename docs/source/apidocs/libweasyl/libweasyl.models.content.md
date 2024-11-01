# {py:mod}`libweasyl.models.content`

```{py:module} libweasyl.models.content
```

```{autodoc2-docstring} libweasyl.models.content
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`Submission <libweasyl.models.content.Submission>`
  - ```{autodoc2-docstring} libweasyl.models.content.Submission
    :summary:
    ```
* - {py:obj}`Comment <libweasyl.models.content.Comment>`
  - ```{autodoc2-docstring} libweasyl.models.content.Comment
    :summary:
    ```
* - {py:obj}`Folder <libweasyl.models.content.Folder>`
  - ```{autodoc2-docstring} libweasyl.models.content.Folder
    :summary:
    ```
* - {py:obj}`Journal <libweasyl.models.content.Journal>`
  - ```{autodoc2-docstring} libweasyl.models.content.Journal
    :summary:
    ```
* - {py:obj}`JournalComment <libweasyl.models.content.JournalComment>`
  - ```{autodoc2-docstring} libweasyl.models.content.JournalComment
    :summary:
    ```
* - {py:obj}`Character <libweasyl.models.content.Character>`
  - ```{autodoc2-docstring} libweasyl.models.content.Character
    :summary:
    ```
* - {py:obj}`CharacterComment <libweasyl.models.content.CharacterComment>`
  - ```{autodoc2-docstring} libweasyl.models.content.CharacterComment
    :summary:
    ```
* - {py:obj}`Favorite <libweasyl.models.content.Favorite>`
  - ```{autodoc2-docstring} libweasyl.models.content.Favorite
    :summary:
    ```
* - {py:obj}`ReportComment <libweasyl.models.content.ReportComment>`
  - ```{autodoc2-docstring} libweasyl.models.content.ReportComment
    :summary:
    ```
* - {py:obj}`Report <libweasyl.models.content.Report>`
  - ```{autodoc2-docstring} libweasyl.models.content.Report
    :summary:
    ```
````

### API

`````{py:class} Submission
:canonical: libweasyl.models.content.Submission

Bases: {py:obj}`libweasyl.models.meta.Base`

```{autodoc2-docstring} libweasyl.models.content.Submission
```

````{py:attribute} __table__
:canonical: libweasyl.models.content.Submission.__table__
:value: >
   None

```{autodoc2-docstring} libweasyl.models.content.Submission.__table__
```

````

````{py:attribute} owner
:canonical: libweasyl.models.content.Submission.owner
:value: >
   'relationship(...)'

```{autodoc2-docstring} libweasyl.models.content.Submission.owner
```

````

````{py:method} legacy_path(mod=False)
:canonical: libweasyl.models.content.Submission.legacy_path

```{autodoc2-docstring} libweasyl.models.content.Submission.legacy_path
```

````

````{py:method} media()
:canonical: libweasyl.models.content.Submission.media

```{autodoc2-docstring} libweasyl.models.content.Submission.media
```

````

````{py:method} submission_media()
:canonical: libweasyl.models.content.Submission.submission_media

```{autodoc2-docstring} libweasyl.models.content.Submission.submission_media
```

````

````{py:method} cover_media()
:canonical: libweasyl.models.content.Submission.cover_media

```{autodoc2-docstring} libweasyl.models.content.Submission.cover_media
```

````

`````

`````{py:class} Comment
:canonical: libweasyl.models.content.Comment

Bases: {py:obj}`libweasyl.models.meta.Base`

```{autodoc2-docstring} libweasyl.models.content.Comment
```

````{py:attribute} __table__
:canonical: libweasyl.models.content.Comment.__table__
:value: >
   None

```{autodoc2-docstring} libweasyl.models.content.Comment.__table__
```

````

````{py:attribute} _target_user
:canonical: libweasyl.models.content.Comment._target_user
:value: >
   'relationship(...)'

```{autodoc2-docstring} libweasyl.models.content.Comment._target_user
```

````

````{py:attribute} _target_sub
:canonical: libweasyl.models.content.Comment._target_sub
:value: >
   'relationship(...)'

```{autodoc2-docstring} libweasyl.models.content.Comment._target_sub
```

````

````{py:attribute} poster
:canonical: libweasyl.models.content.Comment.poster
:value: >
   'relationship(...)'

```{autodoc2-docstring} libweasyl.models.content.Comment.poster
```

````

````{py:property} target
:canonical: libweasyl.models.content.Comment.target

```{autodoc2-docstring} libweasyl.models.content.Comment.target
```

````

`````

`````{py:class} Folder
:canonical: libweasyl.models.content.Folder

Bases: {py:obj}`libweasyl.models.meta.Base`

```{autodoc2-docstring} libweasyl.models.content.Folder
```

````{py:attribute} __table__
:canonical: libweasyl.models.content.Folder.__table__
:value: >
   None

```{autodoc2-docstring} libweasyl.models.content.Folder.__table__
```

````

````{py:attribute} owner
:canonical: libweasyl.models.content.Folder.owner
:value: >
   'relationship(...)'

```{autodoc2-docstring} libweasyl.models.content.Folder.owner
```

````

````{py:attribute} submissions
:canonical: libweasyl.models.content.Folder.submissions
:value: >
   'relationship(...)'

```{autodoc2-docstring} libweasyl.models.content.Folder.submissions
```

````

`````

`````{py:class} Journal
:canonical: libweasyl.models.content.Journal

Bases: {py:obj}`libweasyl.models.meta.Base`

```{autodoc2-docstring} libweasyl.models.content.Journal
```

````{py:attribute} __table__
:canonical: libweasyl.models.content.Journal.__table__
:value: >
   None

```{autodoc2-docstring} libweasyl.models.content.Journal.__table__
```

````

````{py:attribute} owner
:canonical: libweasyl.models.content.Journal.owner
:value: >
   'relationship(...)'

```{autodoc2-docstring} libweasyl.models.content.Journal.owner
```

````

````{py:method} legacy_path(mod=False)
:canonical: libweasyl.models.content.Journal.legacy_path

```{autodoc2-docstring} libweasyl.models.content.Journal.legacy_path
```

````

`````

`````{py:class} JournalComment
:canonical: libweasyl.models.content.JournalComment

Bases: {py:obj}`libweasyl.models.meta.Base`

```{autodoc2-docstring} libweasyl.models.content.JournalComment
```

````{py:attribute} __table__
:canonical: libweasyl.models.content.JournalComment.__table__
:value: >
   None

```{autodoc2-docstring} libweasyl.models.content.JournalComment.__table__
```

````

`````

`````{py:class} Character
:canonical: libweasyl.models.content.Character

Bases: {py:obj}`libweasyl.models.meta.Base`

```{autodoc2-docstring} libweasyl.models.content.Character
```

````{py:attribute} __table__
:canonical: libweasyl.models.content.Character.__table__
:value: >
   None

```{autodoc2-docstring} libweasyl.models.content.Character.__table__
```

````

````{py:attribute} owner
:canonical: libweasyl.models.content.Character.owner
:value: >
   'relationship(...)'

```{autodoc2-docstring} libweasyl.models.content.Character.owner
```

````

````{py:property} title
:canonical: libweasyl.models.content.Character.title

```{autodoc2-docstring} libweasyl.models.content.Character.title
```

````

````{py:method} legacy_path(mod=False)
:canonical: libweasyl.models.content.Character.legacy_path

```{autodoc2-docstring} libweasyl.models.content.Character.legacy_path
```

````

`````

`````{py:class} CharacterComment
:canonical: libweasyl.models.content.CharacterComment

Bases: {py:obj}`libweasyl.models.meta.Base`

```{autodoc2-docstring} libweasyl.models.content.CharacterComment
```

````{py:attribute} __table__
:canonical: libweasyl.models.content.CharacterComment.__table__
:value: >
   None

```{autodoc2-docstring} libweasyl.models.content.CharacterComment.__table__
```

````

`````

`````{py:class} Favorite
:canonical: libweasyl.models.content.Favorite

Bases: {py:obj}`libweasyl.models.meta.Base`

```{autodoc2-docstring} libweasyl.models.content.Favorite
```

````{py:attribute} __table__
:canonical: libweasyl.models.content.Favorite.__table__
:value: >
   None

```{autodoc2-docstring} libweasyl.models.content.Favorite.__table__
```

````

`````

`````{py:class} ReportComment
:canonical: libweasyl.models.content.ReportComment

Bases: {py:obj}`libweasyl.models.meta.Base`

```{autodoc2-docstring} libweasyl.models.content.ReportComment
```

````{py:attribute} __table__
:canonical: libweasyl.models.content.ReportComment.__table__
:value: >
   None

```{autodoc2-docstring} libweasyl.models.content.ReportComment.__table__
```

````

````{py:attribute} poster
:canonical: libweasyl.models.content.ReportComment.poster
:value: >
   'relationship(...)'

```{autodoc2-docstring} libweasyl.models.content.ReportComment.poster
```

````

`````

`````{py:class} Report
:canonical: libweasyl.models.content.Report

Bases: {py:obj}`libweasyl.models.meta.Base`

```{autodoc2-docstring} libweasyl.models.content.Report
```

````{py:attribute} __table__
:canonical: libweasyl.models.content.Report.__table__
:value: >
   None

```{autodoc2-docstring} libweasyl.models.content.Report.__table__
```

````

````{py:attribute} _target_user
:canonical: libweasyl.models.content.Report._target_user
:value: >
   'relationship(...)'

```{autodoc2-docstring} libweasyl.models.content.Report._target_user
```

````

````{py:attribute} _target_sub
:canonical: libweasyl.models.content.Report._target_sub
:value: >
   'relationship(...)'

```{autodoc2-docstring} libweasyl.models.content.Report._target_sub
```

````

````{py:attribute} _target_char
:canonical: libweasyl.models.content.Report._target_char
:value: >
   'relationship(...)'

```{autodoc2-docstring} libweasyl.models.content.Report._target_char
```

````

````{py:attribute} _target_journal
:canonical: libweasyl.models.content.Report._target_journal
:value: >
   'relationship(...)'

```{autodoc2-docstring} libweasyl.models.content.Report._target_journal
```

````

````{py:attribute} _target_comment
:canonical: libweasyl.models.content.Report._target_comment
:value: >
   'relationship(...)'

```{autodoc2-docstring} libweasyl.models.content.Report._target_comment
```

````

````{py:attribute} comments
:canonical: libweasyl.models.content.Report.comments
:value: >
   'relationship(...)'

```{autodoc2-docstring} libweasyl.models.content.Report.comments
```

````

````{py:attribute} owner
:canonical: libweasyl.models.content.Report.owner
:value: >
   'relationship(...)'

```{autodoc2-docstring} libweasyl.models.content.Report.owner
```

````

````{py:property} target
:canonical: libweasyl.models.content.Report.target

```{autodoc2-docstring} libweasyl.models.content.Report.target
```

````

````{py:property} target_type
:canonical: libweasyl.models.content.Report.target_type

```{autodoc2-docstring} libweasyl.models.content.Report.target_type
```

````

````{py:property} status
:canonical: libweasyl.models.content.Report.status

```{autodoc2-docstring} libweasyl.models.content.Report.status
```

````

````{py:method} is_closed()
:canonical: libweasyl.models.content.Report.is_closed

```{autodoc2-docstring} libweasyl.models.content.Report.is_closed
```

````

````{py:method} related_reports()
:canonical: libweasyl.models.content.Report.related_reports

```{autodoc2-docstring} libweasyl.models.content.Report.related_reports
```

````

`````
