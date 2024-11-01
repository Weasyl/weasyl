# {py:mod}`weasyl.report`

```{py:module} weasyl.report
```

```{autodoc2-docstring} weasyl.report
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_convert_violation <weasyl.report._convert_violation>`
  - ```{autodoc2-docstring} weasyl.report._convert_violation
    :summary:
    ```
* - {py:obj}`_dict_of_targetid <weasyl.report._dict_of_targetid>`
  - ```{autodoc2-docstring} weasyl.report._dict_of_targetid
    :summary:
    ```
* - {py:obj}`create <weasyl.report.create>`
  - ```{autodoc2-docstring} weasyl.report.create
    :summary:
    ```
* - {py:obj}`select_list <weasyl.report.select_list>`
  - ```{autodoc2-docstring} weasyl.report.select_list
    :summary:
    ```
* - {py:obj}`select_view <weasyl.report.select_view>`
  - ```{autodoc2-docstring} weasyl.report.select_view
    :summary:
    ```
* - {py:obj}`close <weasyl.report.close>`
  - ```{autodoc2-docstring} weasyl.report.close
    :summary:
    ```
* - {py:obj}`check <weasyl.report.check>`
  - ```{autodoc2-docstring} weasyl.report.check
    :summary:
    ```
* - {py:obj}`select_reported_list <weasyl.report.select_reported_list>`
  - ```{autodoc2-docstring} weasyl.report.select_reported_list
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_CONTENT <weasyl.report._CONTENT>`
  - ```{autodoc2-docstring} weasyl.report._CONTENT
    :summary:
    ```
* - {py:obj}`_report_types <weasyl.report._report_types>`
  - ```{autodoc2-docstring} weasyl.report._report_types
    :summary:
    ```
* - {py:obj}`_closure_actions <weasyl.report._closure_actions>`
  - ```{autodoc2-docstring} weasyl.report._closure_actions
    :summary:
    ```
````

### API

````{py:data} _CONTENT
:canonical: weasyl.report._CONTENT
:value: >
   2000

```{autodoc2-docstring} weasyl.report._CONTENT
```

````

````{py:function} _convert_violation(target)
:canonical: weasyl.report._convert_violation

```{autodoc2-docstring} weasyl.report._convert_violation
```
````

````{py:function} _dict_of_targetid(submitid, charid, journalid)
:canonical: weasyl.report._dict_of_targetid

```{autodoc2-docstring} weasyl.report._dict_of_targetid
```
````

````{py:function} create(userid, form)
:canonical: weasyl.report.create

```{autodoc2-docstring} weasyl.report.create
```
````

````{py:data} _report_types
:canonical: weasyl.report._report_types
:value: >
   ['_target_sub', '_target_char', '_target_journal']

```{autodoc2-docstring} weasyl.report._report_types
```

````

````{py:function} select_list(userid, form)
:canonical: weasyl.report.select_list

```{autodoc2-docstring} weasyl.report.select_list
```
````

````{py:function} select_view(userid, *, reportid)
:canonical: weasyl.report.select_view

```{autodoc2-docstring} weasyl.report.select_view
```
````

````{py:data} _closure_actions
:canonical: weasyl.report._closure_actions
:value: >
   None

```{autodoc2-docstring} weasyl.report._closure_actions
```

````

````{py:function} close(userid, form)
:canonical: weasyl.report.close

```{autodoc2-docstring} weasyl.report.close
```
````

````{py:function} check(submitid=None, charid=None, journalid=None)
:canonical: weasyl.report.check

```{autodoc2-docstring} weasyl.report.check
```
````

````{py:function} select_reported_list(userid)
:canonical: weasyl.report.select_reported_list

```{autodoc2-docstring} weasyl.report.select_reported_list
```
````
