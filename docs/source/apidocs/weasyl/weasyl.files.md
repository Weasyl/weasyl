# {py:mod}`weasyl.files`

```{py:module} weasyl.files
```

```{autodoc2-docstring} weasyl.files
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`read <weasyl.files.read>`
  - ```{autodoc2-docstring} weasyl.files.read
    :summary:
    ```
* - {py:obj}`ensure_file_directory <weasyl.files.ensure_file_directory>`
  - ```{autodoc2-docstring} weasyl.files.ensure_file_directory
    :summary:
    ```
* - {py:obj}`write <weasyl.files.write>`
  - ```{autodoc2-docstring} weasyl.files.write
    :summary:
    ```
* - {py:obj}`append <weasyl.files.append>`
  - ```{autodoc2-docstring} weasyl.files.append
    :summary:
    ```
* - {py:obj}`_remove_glob <weasyl.files._remove_glob>`
  - ```{autodoc2-docstring} weasyl.files._remove_glob
    :summary:
    ```
* - {py:obj}`get_temporary <weasyl.files.get_temporary>`
  - ```{autodoc2-docstring} weasyl.files.get_temporary
    :summary:
    ```
* - {py:obj}`clear_temporary <weasyl.files.clear_temporary>`
  - ```{autodoc2-docstring} weasyl.files.clear_temporary
    :summary:
    ```
* - {py:obj}`make_character_directory <weasyl.files.make_character_directory>`
  - ```{autodoc2-docstring} weasyl.files.make_character_directory
    :summary:
    ```
* - {py:obj}`make_resource <weasyl.files.make_resource>`
  - ```{autodoc2-docstring} weasyl.files.make_resource
    :summary:
    ```
* - {py:obj}`typeflag <weasyl.files.typeflag>`
  - ```{autodoc2-docstring} weasyl.files.typeflag
    :summary:
    ```
* - {py:obj}`get_extension_for_category <weasyl.files.get_extension_for_category>`
  - ```{autodoc2-docstring} weasyl.files.get_extension_for_category
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`copy <weasyl.files.copy>`
  - ```{autodoc2-docstring} weasyl.files.copy
    :summary:
    ```
* - {py:obj}`_feature_typeflags <weasyl.files._feature_typeflags>`
  - ```{autodoc2-docstring} weasyl.files._feature_typeflags
    :summary:
    ```
* - {py:obj}`_extension_typeflags <weasyl.files._extension_typeflags>`
  - ```{autodoc2-docstring} weasyl.files._extension_typeflags
    :summary:
    ```
* - {py:obj}`_categories <weasyl.files._categories>`
  - ```{autodoc2-docstring} weasyl.files._categories
    :summary:
    ```
````

### API

````{py:function} read(filename)
:canonical: weasyl.files.read

```{autodoc2-docstring} weasyl.files.read
```
````

````{py:function} ensure_file_directory(filename)
:canonical: weasyl.files.ensure_file_directory

```{autodoc2-docstring} weasyl.files.ensure_file_directory
```
````

````{py:function} write(filename, content)
:canonical: weasyl.files.write

```{autodoc2-docstring} weasyl.files.write
```
````

````{py:function} append(filename, content)
:canonical: weasyl.files.append

```{autodoc2-docstring} weasyl.files.append
```
````

````{py:data} copy
:canonical: weasyl.files.copy
:value: >
   None

```{autodoc2-docstring} weasyl.files.copy
```

````

````{py:function} _remove_glob(glob_path)
:canonical: weasyl.files._remove_glob

```{autodoc2-docstring} weasyl.files._remove_glob
```
````

````{py:function} get_temporary(userid, feature)
:canonical: weasyl.files.get_temporary

```{autodoc2-docstring} weasyl.files.get_temporary
```
````

````{py:function} clear_temporary(userid)
:canonical: weasyl.files.clear_temporary

```{autodoc2-docstring} weasyl.files.clear_temporary
```
````

````{py:function} make_character_directory(target)
:canonical: weasyl.files.make_character_directory

```{autodoc2-docstring} weasyl.files.make_character_directory
```
````

````{py:function} make_resource(userid, target, feature, extension=None)
:canonical: weasyl.files.make_resource

```{autodoc2-docstring} weasyl.files.make_resource
```
````

````{py:data} _feature_typeflags
:canonical: weasyl.files._feature_typeflags
:value: >
   None

```{autodoc2-docstring} weasyl.files._feature_typeflags
```

````

````{py:data} _extension_typeflags
:canonical: weasyl.files._extension_typeflags
:value: >
   None

```{autodoc2-docstring} weasyl.files._extension_typeflags
```

````

````{py:function} typeflag(feature, extension)
:canonical: weasyl.files.typeflag

```{autodoc2-docstring} weasyl.files.typeflag
```
````

````{py:data} _categories
:canonical: weasyl.files._categories
:value: >
   None

```{autodoc2-docstring} weasyl.files._categories
```

````

````{py:function} get_extension_for_category(filedata, category)
:canonical: weasyl.files.get_extension_for_category

```{autodoc2-docstring} weasyl.files.get_extension_for_category
```
````
