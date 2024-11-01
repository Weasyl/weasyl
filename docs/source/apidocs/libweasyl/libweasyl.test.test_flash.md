# {py:mod}`libweasyl.test.test_flash`

```{py:module} libweasyl.test.test_flash
```

```{autodoc2-docstring} libweasyl.test.test_flash
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`test_iter_decompressed_zlib_lazily_reads_chunks <libweasyl.test.test_flash.test_iter_decompressed_zlib_lazily_reads_chunks>`
  - ```{autodoc2-docstring} libweasyl.test.test_flash.test_iter_decompressed_zlib_lazily_reads_chunks
    :summary:
    ```
* - {py:obj}`test_iter_decompressed_zlib_reads_by_chunksize <libweasyl.test.test_flash.test_iter_decompressed_zlib_reads_by_chunksize>`
  - ```{autodoc2-docstring} libweasyl.test.test_flash.test_iter_decompressed_zlib_reads_by_chunksize
    :summary:
    ```
* - {py:obj}`test_iter_decompressed_zlib_can_read_all_bytes <libweasyl.test.test_flash.test_iter_decompressed_zlib_can_read_all_bytes>`
  - ```{autodoc2-docstring} libweasyl.test.test_flash.test_iter_decompressed_zlib_can_read_all_bytes
    :summary:
    ```
* - {py:obj}`test_read_uncompressed_flash_header <libweasyl.test.test_flash.test_read_uncompressed_flash_header>`
  - ```{autodoc2-docstring} libweasyl.test.test_flash.test_read_uncompressed_flash_header
    :summary:
    ```
* - {py:obj}`test_read_zlib_compressed_flash_header <libweasyl.test.test_flash.test_read_zlib_compressed_flash_header>`
  - ```{autodoc2-docstring} libweasyl.test.test_flash.test_read_zlib_compressed_flash_header
    :summary:
    ```
* - {py:obj}`test_read_lzma_compressed_flash_header <libweasyl.test.test_flash.test_read_lzma_compressed_flash_header>`
  - ```{autodoc2-docstring} libweasyl.test.test_flash.test_read_lzma_compressed_flash_header
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`compressed_data <libweasyl.test.test_flash.compressed_data>`
  - ```{autodoc2-docstring} libweasyl.test.test_flash.compressed_data
    :summary:
    ```
* - {py:obj}`decompressed_data <libweasyl.test.test_flash.decompressed_data>`
  - ```{autodoc2-docstring} libweasyl.test.test_flash.decompressed_data
    :summary:
    ```
````

### API

````{py:data} compressed_data
:canonical: libweasyl.test.test_flash.compressed_data
:value: >
   'b64decode(...)'

```{autodoc2-docstring} libweasyl.test.test_flash.compressed_data
```

````

````{py:data} decompressed_data
:canonical: libweasyl.test.test_flash.decompressed_data
:value: >
   'b64decode(...)'

```{autodoc2-docstring} libweasyl.test.test_flash.decompressed_data
```

````

````{py:function} test_iter_decompressed_zlib_lazily_reads_chunks()
:canonical: libweasyl.test.test_flash.test_iter_decompressed_zlib_lazily_reads_chunks

```{autodoc2-docstring} libweasyl.test.test_flash.test_iter_decompressed_zlib_lazily_reads_chunks
```
````

````{py:function} test_iter_decompressed_zlib_reads_by_chunksize()
:canonical: libweasyl.test.test_flash.test_iter_decompressed_zlib_reads_by_chunksize

```{autodoc2-docstring} libweasyl.test.test_flash.test_iter_decompressed_zlib_reads_by_chunksize
```
````

````{py:function} test_iter_decompressed_zlib_can_read_all_bytes()
:canonical: libweasyl.test.test_flash.test_iter_decompressed_zlib_can_read_all_bytes

```{autodoc2-docstring} libweasyl.test.test_flash.test_iter_decompressed_zlib_can_read_all_bytes
```
````

````{py:function} test_read_uncompressed_flash_header()
:canonical: libweasyl.test.test_flash.test_read_uncompressed_flash_header

```{autodoc2-docstring} libweasyl.test.test_flash.test_read_uncompressed_flash_header
```
````

````{py:function} test_read_zlib_compressed_flash_header()
:canonical: libweasyl.test.test_flash.test_read_zlib_compressed_flash_header

```{autodoc2-docstring} libweasyl.test.test_flash.test_read_zlib_compressed_flash_header
```
````

````{py:function} test_read_lzma_compressed_flash_header()
:canonical: libweasyl.test.test_flash.test_read_lzma_compressed_flash_header

```{autodoc2-docstring} libweasyl.test.test_flash.test_read_lzma_compressed_flash_header
```
````
