# {py:mod}`weasyl.image`

```{py:module} weasyl.image
```

```{autodoc2-docstring} weasyl.image
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`read <weasyl.image.read>`
  - ```{autodoc2-docstring} weasyl.image.read
    :summary:
    ```
* - {py:obj}`from_string <weasyl.image.from_string>`
  - ```{autodoc2-docstring} weasyl.image.from_string
    :summary:
    ```
* - {py:obj}`image_setting <weasyl.image.image_setting>`
  - ```{autodoc2-docstring} weasyl.image.image_setting
    :summary:
    ```
* - {py:obj}`check_crop <weasyl.image.check_crop>`
  - ```{autodoc2-docstring} weasyl.image.check_crop
    :summary:
    ```
* - {py:obj}`check_type <weasyl.image.check_type>`
  - ```{autodoc2-docstring} weasyl.image.check_type
    :summary:
    ```
* - {py:obj}`_resize <weasyl.image._resize>`
  - ```{autodoc2-docstring} weasyl.image._resize
    :summary:
    ```
* - {py:obj}`make_cover <weasyl.image.make_cover>`
  - ```{autodoc2-docstring} weasyl.image.make_cover
    :summary:
    ```
* - {py:obj}`_shrinkcrop <weasyl.image._shrinkcrop>`
  - ```{autodoc2-docstring} weasyl.image._shrinkcrop
    :summary:
    ```
* - {py:obj}`shrinkcrop <weasyl.image.shrinkcrop>`
  - ```{autodoc2-docstring} weasyl.image.shrinkcrop
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`COVER_SIZE <weasyl.image.COVER_SIZE>`
  - ```{autodoc2-docstring} weasyl.image.COVER_SIZE
    :summary:
    ```
````

### API

````{py:data} COVER_SIZE
:canonical: weasyl.image.COVER_SIZE
:value: >
   (1024, 3000)

```{autodoc2-docstring} weasyl.image.COVER_SIZE
```

````

````{py:function} read(filename)
:canonical: weasyl.image.read

```{autodoc2-docstring} weasyl.image.read
```
````

````{py:function} from_string(filedata)
:canonical: weasyl.image.from_string

```{autodoc2-docstring} weasyl.image.from_string
```
````

````{py:function} image_setting(im)
:canonical: weasyl.image.image_setting

```{autodoc2-docstring} weasyl.image.image_setting
```
````

````{py:function} check_crop(dim, x1, y1, x2, y2)
:canonical: weasyl.image.check_crop

```{autodoc2-docstring} weasyl.image.check_crop
```
````

````{py:function} check_type(filename)
:canonical: weasyl.image.check_type

```{autodoc2-docstring} weasyl.image.check_type
```
````

````{py:function} _resize(filename, width, height, destination=None)
:canonical: weasyl.image._resize

```{autodoc2-docstring} weasyl.image._resize
```
````

````{py:function} make_cover(filename, destination=None)
:canonical: weasyl.image.make_cover

```{autodoc2-docstring} weasyl.image.make_cover
```
````

````{py:function} _shrinkcrop(im, size, bounds=None)
:canonical: weasyl.image._shrinkcrop

```{autodoc2-docstring} weasyl.image._shrinkcrop
```
````

````{py:function} shrinkcrop(im, size, bounds=None)
:canonical: weasyl.image.shrinkcrop

```{autodoc2-docstring} weasyl.image.shrinkcrop
```
````
