# {py:mod}`libweasyl.flash`

```{py:module} libweasyl.flash
```

```{autodoc2-docstring} libweasyl.flash
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`iter_decompressed_zlib <libweasyl.flash.iter_decompressed_zlib>`
  - ```{autodoc2-docstring} libweasyl.flash.iter_decompressed_zlib
    :summary:
    ```
* - {py:obj}`parse_flash_header <libweasyl.flash.parse_flash_header>`
  - ```{autodoc2-docstring} libweasyl.flash.parse_flash_header
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`SIZES <libweasyl.flash.SIZES>`
  - ```{autodoc2-docstring} libweasyl.flash.SIZES
    :summary:
    ```
* - {py:obj}`SIGNATURE_COMPRESSION <libweasyl.flash.SIGNATURE_COMPRESSION>`
  - ```{autodoc2-docstring} libweasyl.flash.SIGNATURE_COMPRESSION
    :summary:
    ```
````

### API

````{py:function} iter_decompressed_zlib(fobj, chunksize=1024)
:canonical: libweasyl.flash.iter_decompressed_zlib

```{autodoc2-docstring} libweasyl.flash.iter_decompressed_zlib
```
````

````{py:data} SIZES
:canonical: libweasyl.flash.SIZES
:value: >
   ('xmin', 'xmax', 'ymin', 'ymax')

```{autodoc2-docstring} libweasyl.flash.SIZES
```

````

````{py:data} SIGNATURE_COMPRESSION
:canonical: libweasyl.flash.SIGNATURE_COMPRESSION
:value: >
   None

```{autodoc2-docstring} libweasyl.flash.SIGNATURE_COMPRESSION
```

````

````{py:function} parse_flash_header(fobj)
:canonical: libweasyl.flash.parse_flash_header

```{autodoc2-docstring} libweasyl.flash.parse_flash_header
```
````
