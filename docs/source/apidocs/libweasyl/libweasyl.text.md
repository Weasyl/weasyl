# {py:mod}`libweasyl.text`

```{py:module} libweasyl.text
```

```{autodoc2-docstring} libweasyl.text
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`WeasylRenderer <libweasyl.text.WeasylRenderer>`
  - ```{autodoc2-docstring} libweasyl.text.WeasylRenderer
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`slug_for <libweasyl.text.slug_for>`
  - ```{autodoc2-docstring} libweasyl.text.slug_for
    :summary:
    ```
* - {py:obj}`_furaffinity <libweasyl.text._furaffinity>`
  - ```{autodoc2-docstring} libweasyl.text._furaffinity
    :summary:
    ```
* - {py:obj}`_inkbunny <libweasyl.text._inkbunny>`
  - ```{autodoc2-docstring} libweasyl.text._inkbunny
    :summary:
    ```
* - {py:obj}`_deviantart <libweasyl.text._deviantart>`
  - ```{autodoc2-docstring} libweasyl.text._deviantart
    :summary:
    ```
* - {py:obj}`_sofurry <libweasyl.text._sofurry>`
  - ```{autodoc2-docstring} libweasyl.text._sofurry
    :summary:
    ```
* - {py:obj}`strip_outer_tag <libweasyl.text.strip_outer_tag>`
  - ```{autodoc2-docstring} libweasyl.text.strip_outer_tag
    :summary:
    ```
* - {py:obj}`_markdown <libweasyl.text._markdown>`
  - ```{autodoc2-docstring} libweasyl.text._markdown
    :summary:
    ```
* - {py:obj}`create_link <libweasyl.text.create_link>`
  - ```{autodoc2-docstring} libweasyl.text.create_link
    :summary:
    ```
* - {py:obj}`add_user_links <libweasyl.text.add_user_links>`
  - ```{autodoc2-docstring} libweasyl.text.add_user_links
    :summary:
    ```
* - {py:obj}`_convert_autolinks <libweasyl.text._convert_autolinks>`
  - ```{autodoc2-docstring} libweasyl.text._convert_autolinks
    :summary:
    ```
* - {py:obj}`_markdown_fragment <libweasyl.text._markdown_fragment>`
  - ```{autodoc2-docstring} libweasyl.text._markdown_fragment
    :summary:
    ```
* - {py:obj}`markdown <libweasyl.text.markdown>`
  - ```{autodoc2-docstring} libweasyl.text.markdown
    :summary:
    ```
* - {py:obj}`_itertext_spaced <libweasyl.text._itertext_spaced>`
  - ```{autodoc2-docstring} libweasyl.text._itertext_spaced
    :summary:
    ```
* - {py:obj}`_normalize_whitespace <libweasyl.text._normalize_whitespace>`
  - ```{autodoc2-docstring} libweasyl.text._normalize_whitespace
    :summary:
    ```
* - {py:obj}`markdown_excerpt <libweasyl.text.markdown_excerpt>`
  - ```{autodoc2-docstring} libweasyl.text.markdown_excerpt
    :summary:
    ```
* - {py:obj}`markdown_link <libweasyl.text.markdown_link>`
  - ```{autodoc2-docstring} libweasyl.text.markdown_link
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`AUTOLINK_URL <libweasyl.text.AUTOLINK_URL>`
  - ```{autodoc2-docstring} libweasyl.text.AUTOLINK_URL
    :summary:
    ```
* - {py:obj}`url_regexp <libweasyl.text.url_regexp>`
  - ```{autodoc2-docstring} libweasyl.text.url_regexp
    :summary:
    ```
* - {py:obj}`USER_LINK <libweasyl.text.USER_LINK>`
  - ```{autodoc2-docstring} libweasyl.text.USER_LINK
    :summary:
    ```
* - {py:obj}`NON_USERNAME_CHARACTERS <libweasyl.text.NON_USERNAME_CHARACTERS>`
  - ```{autodoc2-docstring} libweasyl.text.NON_USERNAME_CHARACTERS
    :summary:
    ```
* - {py:obj}`_EXCERPT_BLOCK_ELEMENTS <libweasyl.text._EXCERPT_BLOCK_ELEMENTS>`
  - ```{autodoc2-docstring} libweasyl.text._EXCERPT_BLOCK_ELEMENTS
    :summary:
    ```
* - {py:obj}`MISAKA_EXT <libweasyl.text.MISAKA_EXT>`
  - ```{autodoc2-docstring} libweasyl.text.MISAKA_EXT
    :summary:
    ```
* - {py:obj}`MISAKA_FORMAT <libweasyl.text.MISAKA_FORMAT>`
  - ```{autodoc2-docstring} libweasyl.text.MISAKA_FORMAT
    :summary:
    ```
````

### API

````{py:function} slug_for(title)
:canonical: libweasyl.text.slug_for

```{autodoc2-docstring} libweasyl.text.slug_for
```
````

````{py:data} AUTOLINK_URL
:canonical: libweasyl.text.AUTOLINK_URL
:value: >
   '(?P<url>\\b(?:https?://|www\\d{,3}\\.|[a-z0-9.-]+\\.[a-z]{2,4}/)[^\\s()<>\\[\\]\\x02]+(?![^\\s`!()\\[\\]{};:\'\\"...'

```{autodoc2-docstring} libweasyl.text.AUTOLINK_URL
```

````

````{py:data} url_regexp
:canonical: libweasyl.text.url_regexp
:value: >
   'compile(...)'

```{autodoc2-docstring} libweasyl.text.url_regexp
```

````

````{py:data} USER_LINK
:canonical: libweasyl.text.USER_LINK
:value: >
   'compile(...)'

```{autodoc2-docstring} libweasyl.text.USER_LINK
```

````

````{py:data} NON_USERNAME_CHARACTERS
:canonical: libweasyl.text.NON_USERNAME_CHARACTERS
:value: >
   'compile(...)'

```{autodoc2-docstring} libweasyl.text.NON_USERNAME_CHARACTERS
```

````

````{py:data} _EXCERPT_BLOCK_ELEMENTS
:canonical: libweasyl.text._EXCERPT_BLOCK_ELEMENTS
:value: >
   'frozenset(...)'

```{autodoc2-docstring} libweasyl.text._EXCERPT_BLOCK_ELEMENTS
```

````

````{py:function} _furaffinity(target)
:canonical: libweasyl.text._furaffinity

```{autodoc2-docstring} libweasyl.text._furaffinity
```
````

````{py:function} _inkbunny(target)
:canonical: libweasyl.text._inkbunny

```{autodoc2-docstring} libweasyl.text._inkbunny
```
````

````{py:function} _deviantart(target)
:canonical: libweasyl.text._deviantart

```{autodoc2-docstring} libweasyl.text._deviantart
```
````

````{py:function} _sofurry(target)
:canonical: libweasyl.text._sofurry

```{autodoc2-docstring} libweasyl.text._sofurry
```
````

````{py:data} MISAKA_EXT
:canonical: libweasyl.text.MISAKA_EXT
:value: >
   None

```{autodoc2-docstring} libweasyl.text.MISAKA_EXT
```

````

````{py:data} MISAKA_FORMAT
:canonical: libweasyl.text.MISAKA_FORMAT
:value: >
   None

```{autodoc2-docstring} libweasyl.text.MISAKA_FORMAT
```

````

````{py:function} strip_outer_tag(html)
:canonical: libweasyl.text.strip_outer_tag

```{autodoc2-docstring} libweasyl.text.strip_outer_tag
```
````

`````{py:class} WeasylRenderer
:canonical: libweasyl.text.WeasylRenderer

Bases: {py:obj}`misaka.HtmlRenderer`

```{autodoc2-docstring} libweasyl.text.WeasylRenderer
```

````{py:method} block_html(raw_html)
:canonical: libweasyl.text.WeasylRenderer.block_html

```{autodoc2-docstring} libweasyl.text.WeasylRenderer.block_html
```

````

````{py:method} autolink(link, is_email)
:canonical: libweasyl.text.WeasylRenderer.autolink

```{autodoc2-docstring} libweasyl.text.WeasylRenderer.autolink
```

````

````{py:method} list(text, ordered, prefix)
:canonical: libweasyl.text.WeasylRenderer.list

```{autodoc2-docstring} libweasyl.text.WeasylRenderer.list
```

````

`````

````{py:function} _markdown(target)
:canonical: libweasyl.text._markdown

```{autodoc2-docstring} libweasyl.text._markdown
```
````

````{py:function} create_link(t, username)
:canonical: libweasyl.text.create_link

```{autodoc2-docstring} libweasyl.text.create_link
```
````

````{py:function} add_user_links(fragment, parent, can_contain)
:canonical: libweasyl.text.add_user_links

```{autodoc2-docstring} libweasyl.text.add_user_links
```
````

````{py:function} _convert_autolinks(fragment)
:canonical: libweasyl.text._convert_autolinks

```{autodoc2-docstring} libweasyl.text._convert_autolinks
```
````

````{py:function} _markdown_fragment(target)
:canonical: libweasyl.text._markdown_fragment

```{autodoc2-docstring} libweasyl.text._markdown_fragment
```
````

````{py:function} markdown(target)
:canonical: libweasyl.text.markdown

```{autodoc2-docstring} libweasyl.text.markdown
```
````

````{py:function} _itertext_spaced(element)
:canonical: libweasyl.text._itertext_spaced

```{autodoc2-docstring} libweasyl.text._itertext_spaced
```
````

````{py:function} _normalize_whitespace(text)
:canonical: libweasyl.text._normalize_whitespace

```{autodoc2-docstring} libweasyl.text._normalize_whitespace
```
````

````{py:function} markdown_excerpt(markdown_text, length=300)
:canonical: libweasyl.text.markdown_excerpt

```{autodoc2-docstring} libweasyl.text.markdown_excerpt
```
````

````{py:function} markdown_link(title, url)
:canonical: libweasyl.text.markdown_link

```{autodoc2-docstring} libweasyl.text.markdown_link
```
````
