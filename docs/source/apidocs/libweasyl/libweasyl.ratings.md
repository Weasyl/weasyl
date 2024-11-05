# {py:mod}`libweasyl.ratings`

```{py:module} libweasyl.ratings
```

```{autodoc2-docstring} libweasyl.ratings
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`Rating <libweasyl.ratings.Rating>`
  - ```{autodoc2-docstring} libweasyl.ratings.Rating
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`get_ratings_for_age <libweasyl.ratings.get_ratings_for_age>`
  - ```{autodoc2-docstring} libweasyl.ratings.get_ratings_for_age
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`GENERAL <libweasyl.ratings.GENERAL>`
  - ```{autodoc2-docstring} libweasyl.ratings.GENERAL
    :summary:
    ```
* - {py:obj}`MATURE <libweasyl.ratings.MATURE>`
  - ```{autodoc2-docstring} libweasyl.ratings.MATURE
    :summary:
    ```
* - {py:obj}`EXPLICIT <libweasyl.ratings.EXPLICIT>`
  - ```{autodoc2-docstring} libweasyl.ratings.EXPLICIT
    :summary:
    ```
* - {py:obj}`ALL_RATINGS <libweasyl.ratings.ALL_RATINGS>`
  - ```{autodoc2-docstring} libweasyl.ratings.ALL_RATINGS
    :summary:
    ```
* - {py:obj}`CODE_MAP <libweasyl.ratings.CODE_MAP>`
  - ```{autodoc2-docstring} libweasyl.ratings.CODE_MAP
    :summary:
    ```
* - {py:obj}`CHARACTER_MAP <libweasyl.ratings.CHARACTER_MAP>`
  - ```{autodoc2-docstring} libweasyl.ratings.CHARACTER_MAP
    :summary:
    ```
* - {py:obj}`CODE_TO_NAME <libweasyl.ratings.CODE_TO_NAME>`
  - ```{autodoc2-docstring} libweasyl.ratings.CODE_TO_NAME
    :summary:
    ```
````

### API

`````{py:class} Rating(code, character, name, nice_name, minimum_age, block_text, additional_description=None)
:canonical: libweasyl.ratings.Rating

```{autodoc2-docstring} libweasyl.ratings.Rating
```

```{rubric} Initialization
```

```{autodoc2-docstring} libweasyl.ratings.Rating.__init__
```

````{py:method} __repr__()
:canonical: libweasyl.ratings.Rating.__repr__

````

````{py:method} __eq__(other)
:canonical: libweasyl.ratings.Rating.__eq__

````

````{py:method} __lt__(other)
:canonical: libweasyl.ratings.Rating.__lt__

````

````{py:method} __hash__()
:canonical: libweasyl.ratings.Rating.__hash__

````

`````

````{py:data} GENERAL
:canonical: libweasyl.ratings.GENERAL
:value: >
   'Rating(...)'

```{autodoc2-docstring} libweasyl.ratings.GENERAL
```

````

````{py:data} MATURE
:canonical: libweasyl.ratings.MATURE
:value: >
   'Rating(...)'

```{autodoc2-docstring} libweasyl.ratings.MATURE
```

````

````{py:data} EXPLICIT
:canonical: libweasyl.ratings.EXPLICIT
:value: >
   'Rating(...)'

```{autodoc2-docstring} libweasyl.ratings.EXPLICIT
```

````

````{py:data} ALL_RATINGS
:canonical: libweasyl.ratings.ALL_RATINGS
:value: >
   None

```{autodoc2-docstring} libweasyl.ratings.ALL_RATINGS
```

````

````{py:data} CODE_MAP
:canonical: libweasyl.ratings.CODE_MAP
:value: >
   None

```{autodoc2-docstring} libweasyl.ratings.CODE_MAP
```

````

````{py:data} CHARACTER_MAP
:canonical: libweasyl.ratings.CHARACTER_MAP
:value: >
   None

```{autodoc2-docstring} libweasyl.ratings.CHARACTER_MAP
```

````

````{py:data} CODE_TO_NAME
:canonical: libweasyl.ratings.CODE_TO_NAME
:value: >
   None

```{autodoc2-docstring} libweasyl.ratings.CODE_TO_NAME
```

````

````{py:function} get_ratings_for_age(age)
:canonical: libweasyl.ratings.get_ratings_for_age

```{autodoc2-docstring} libweasyl.ratings.get_ratings_for_age
```
````
