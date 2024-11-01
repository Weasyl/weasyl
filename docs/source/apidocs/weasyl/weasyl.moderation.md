# {py:mod}`weasyl.moderation`

```{py:module} weasyl.moderation
```

```{autodoc2-docstring} weasyl.moderation
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`get_ban_reason <weasyl.moderation.get_ban_reason>`
  - ```{autodoc2-docstring} weasyl.moderation.get_ban_reason
    :summary:
    ```
* - {py:obj}`get_suspension <weasyl.moderation.get_suspension>`
  - ```{autodoc2-docstring} weasyl.moderation.get_suspension
    :summary:
    ```
* - {py:obj}`get_ban_message <weasyl.moderation.get_ban_message>`
  - ```{autodoc2-docstring} weasyl.moderation.get_ban_message
    :summary:
    ```
* - {py:obj}`get_suspension_message <weasyl.moderation.get_suspension_message>`
  - ```{autodoc2-docstring} weasyl.moderation.get_suspension_message
    :summary:
    ```
* - {py:obj}`finduser <weasyl.moderation.finduser>`
  - ```{autodoc2-docstring} weasyl.moderation.finduser
    :summary:
    ```
* - {py:obj}`setusermode <weasyl.moderation.setusermode>`
  - ```{autodoc2-docstring} weasyl.moderation.setusermode
    :summary:
    ```
* - {py:obj}`submissionsbyuser <weasyl.moderation.submissionsbyuser>`
  - ```{autodoc2-docstring} weasyl.moderation.submissionsbyuser
    :summary:
    ```
* - {py:obj}`charactersbyuser <weasyl.moderation.charactersbyuser>`
  - ```{autodoc2-docstring} weasyl.moderation.charactersbyuser
    :summary:
    ```
* - {py:obj}`journalsbyuser <weasyl.moderation.journalsbyuser>`
  - ```{autodoc2-docstring} weasyl.moderation.journalsbyuser
    :summary:
    ```
* - {py:obj}`gallery_blacklisted_tags <weasyl.moderation.gallery_blacklisted_tags>`
  - ```{autodoc2-docstring} weasyl.moderation.gallery_blacklisted_tags
    :summary:
    ```
* - {py:obj}`manageuser <weasyl.moderation.manageuser>`
  - ```{autodoc2-docstring} weasyl.moderation.manageuser
    :summary:
    ```
* - {py:obj}`removeavatar <weasyl.moderation.removeavatar>`
  - ```{autodoc2-docstring} weasyl.moderation.removeavatar
    :summary:
    ```
* - {py:obj}`removebanner <weasyl.moderation.removebanner>`
  - ```{autodoc2-docstring} weasyl.moderation.removebanner
    :summary:
    ```
* - {py:obj}`removecoverart <weasyl.moderation.removecoverart>`
  - ```{autodoc2-docstring} weasyl.moderation.removecoverart
    :summary:
    ```
* - {py:obj}`removethumbnail <weasyl.moderation.removethumbnail>`
  - ```{autodoc2-docstring} weasyl.moderation.removethumbnail
    :summary:
    ```
* - {py:obj}`editprofiletext <weasyl.moderation.editprofiletext>`
  - ```{autodoc2-docstring} weasyl.moderation.editprofiletext
    :summary:
    ```
* - {py:obj}`editcatchphrase <weasyl.moderation.editcatchphrase>`
  - ```{autodoc2-docstring} weasyl.moderation.editcatchphrase
    :summary:
    ```
* - {py:obj}`bulk_edit_rating <weasyl.moderation.bulk_edit_rating>`
  - ```{autodoc2-docstring} weasyl.moderation.bulk_edit_rating
    :summary:
    ```
* - {py:obj}`bulk_edit <weasyl.moderation.bulk_edit>`
  - ```{autodoc2-docstring} weasyl.moderation.bulk_edit
    :summary:
    ```
* - {py:obj}`note_about <weasyl.moderation.note_about>`
  - ```{autodoc2-docstring} weasyl.moderation.note_about
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`BAN_TEMPLATES <weasyl.moderation.BAN_TEMPLATES>`
  - ```{autodoc2-docstring} weasyl.moderation.BAN_TEMPLATES
    :summary:
    ```
* - {py:obj}`_mode_to_action_map <weasyl.moderation._mode_to_action_map>`
  - ```{autodoc2-docstring} weasyl.moderation._mode_to_action_map
    :summary:
    ```
* - {py:obj}`_tables <weasyl.moderation._tables>`
  - ```{autodoc2-docstring} weasyl.moderation._tables
    :summary:
    ```
````

### API

````{py:data} BAN_TEMPLATES
:canonical: weasyl.moderation.BAN_TEMPLATES
:value: >
   None

```{autodoc2-docstring} weasyl.moderation.BAN_TEMPLATES
```

````

````{py:function} get_ban_reason(userid)
:canonical: weasyl.moderation.get_ban_reason

```{autodoc2-docstring} weasyl.moderation.get_ban_reason
```
````

````{py:function} get_suspension(userid)
:canonical: weasyl.moderation.get_suspension

```{autodoc2-docstring} weasyl.moderation.get_suspension
```
````

````{py:function} get_ban_message(userid)
:canonical: weasyl.moderation.get_ban_message

```{autodoc2-docstring} weasyl.moderation.get_ban_message
```
````

````{py:function} get_suspension_message(userid)
:canonical: weasyl.moderation.get_suspension_message

```{autodoc2-docstring} weasyl.moderation.get_suspension_message
```
````

````{py:function} finduser(targetid, username: str, email: str, dateafter, datebefore, excludesuspended, excludebanned, excludeactive, ipaddr, row_offset)
:canonical: weasyl.moderation.finduser

```{autodoc2-docstring} weasyl.moderation.finduser
```
````

````{py:data} _mode_to_action_map
:canonical: weasyl.moderation._mode_to_action_map
:value: >
   None

```{autodoc2-docstring} weasyl.moderation._mode_to_action_map
```

````

````{py:function} setusermode(userid, form)
:canonical: weasyl.moderation.setusermode

```{autodoc2-docstring} weasyl.moderation.setusermode
```
````

````{py:function} submissionsbyuser(targetid)
:canonical: weasyl.moderation.submissionsbyuser

```{autodoc2-docstring} weasyl.moderation.submissionsbyuser
```
````

````{py:function} charactersbyuser(targetid)
:canonical: weasyl.moderation.charactersbyuser

```{autodoc2-docstring} weasyl.moderation.charactersbyuser
```
````

````{py:function} journalsbyuser(targetid)
:canonical: weasyl.moderation.journalsbyuser

```{autodoc2-docstring} weasyl.moderation.journalsbyuser
```
````

````{py:function} gallery_blacklisted_tags(userid, otherid)
:canonical: weasyl.moderation.gallery_blacklisted_tags

```{autodoc2-docstring} weasyl.moderation.gallery_blacklisted_tags
```
````

````{py:function} manageuser(userid, form)
:canonical: weasyl.moderation.manageuser

```{autodoc2-docstring} weasyl.moderation.manageuser
```
````

````{py:function} removeavatar(userid, otherid)
:canonical: weasyl.moderation.removeavatar

```{autodoc2-docstring} weasyl.moderation.removeavatar
```
````

````{py:function} removebanner(userid, otherid)
:canonical: weasyl.moderation.removebanner

```{autodoc2-docstring} weasyl.moderation.removebanner
```
````

````{py:function} removecoverart(userid, submitid)
:canonical: weasyl.moderation.removecoverart

```{autodoc2-docstring} weasyl.moderation.removecoverart
```
````

````{py:function} removethumbnail(userid, submitid)
:canonical: weasyl.moderation.removethumbnail

```{autodoc2-docstring} weasyl.moderation.removethumbnail
```
````

````{py:function} editprofiletext(userid, otherid, content)
:canonical: weasyl.moderation.editprofiletext

```{autodoc2-docstring} weasyl.moderation.editprofiletext
```
````

````{py:function} editcatchphrase(userid, otherid, content)
:canonical: weasyl.moderation.editcatchphrase

```{autodoc2-docstring} weasyl.moderation.editcatchphrase
```
````

````{py:data} _tables
:canonical: weasyl.moderation._tables
:value: >
   [(), (), ()]

```{autodoc2-docstring} weasyl.moderation._tables
```

````

````{py:function} bulk_edit_rating(userid, new_rating, submissions=(), characters=(), journals=())
:canonical: weasyl.moderation.bulk_edit_rating

```{autodoc2-docstring} weasyl.moderation.bulk_edit_rating
```
````

````{py:function} bulk_edit(userid, action, submissions=(), characters=(), journals=())
:canonical: weasyl.moderation.bulk_edit

```{autodoc2-docstring} weasyl.moderation.bulk_edit
```
````

````{py:function} note_about(userid, target_user, title, message=None)
:canonical: weasyl.moderation.note_about

```{autodoc2-docstring} weasyl.moderation.note_about
```
````
