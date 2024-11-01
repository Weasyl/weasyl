# {py:mod}`weasyl.commishinfo`

```{py:module} weasyl.commishinfo
```

```{autodoc2-docstring} weasyl.commishinfo
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`parse_currency <weasyl.commishinfo.parse_currency>`
  - ```{autodoc2-docstring} weasyl.commishinfo.parse_currency
    :summary:
    ```
* - {py:obj}`_fetch_rates_no_cache_failure <weasyl.commishinfo._fetch_rates_no_cache_failure>`
  - ```{autodoc2-docstring} weasyl.commishinfo._fetch_rates_no_cache_failure
    :summary:
    ```
* - {py:obj}`_fetch_rates <weasyl.commishinfo._fetch_rates>`
  - ```{autodoc2-docstring} weasyl.commishinfo._fetch_rates
    :summary:
    ```
* - {py:obj}`_charmap_to_currency_code <weasyl.commishinfo._charmap_to_currency_code>`
  - ```{autodoc2-docstring} weasyl.commishinfo._charmap_to_currency_code
    :summary:
    ```
* - {py:obj}`convert_currency <weasyl.commishinfo.convert_currency>`
  - ```{autodoc2-docstring} weasyl.commishinfo.convert_currency
    :summary:
    ```
* - {py:obj}`currency_ratio <weasyl.commishinfo.currency_ratio>`
  - ```{autodoc2-docstring} weasyl.commishinfo.currency_ratio
    :summary:
    ```
* - {py:obj}`select_list <weasyl.commishinfo.select_list>`
  - ```{autodoc2-docstring} weasyl.commishinfo.select_list
    :summary:
    ```
* - {py:obj}`select_commissionable <weasyl.commishinfo.select_commissionable>`
  - ```{autodoc2-docstring} weasyl.commishinfo.select_commissionable
    :summary:
    ```
* - {py:obj}`create_commission_class <weasyl.commishinfo.create_commission_class>`
  - ```{autodoc2-docstring} weasyl.commishinfo.create_commission_class
    :summary:
    ```
* - {py:obj}`create_price <weasyl.commishinfo.create_price>`
  - ```{autodoc2-docstring} weasyl.commishinfo.create_price
    :summary:
    ```
* - {py:obj}`edit_class <weasyl.commishinfo.edit_class>`
  - ```{autodoc2-docstring} weasyl.commishinfo.edit_class
    :summary:
    ```
* - {py:obj}`edit_price <weasyl.commishinfo.edit_price>`
  - ```{autodoc2-docstring} weasyl.commishinfo.edit_price
    :summary:
    ```
* - {py:obj}`edit_content <weasyl.commishinfo.edit_content>`
  - ```{autodoc2-docstring} weasyl.commishinfo.edit_content
    :summary:
    ```
* - {py:obj}`remove_class <weasyl.commishinfo.remove_class>`
  - ```{autodoc2-docstring} weasyl.commishinfo.remove_class
    :summary:
    ```
* - {py:obj}`remove_price <weasyl.commishinfo.remove_price>`
  - ```{autodoc2-docstring} weasyl.commishinfo.remove_price
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`_MAX_PRICE <weasyl.commishinfo._MAX_PRICE>`
  - ```{autodoc2-docstring} weasyl.commishinfo._MAX_PRICE
    :summary:
    ```
* - {py:obj}`CURRENCY_PRECISION <weasyl.commishinfo.CURRENCY_PRECISION>`
  - ```{autodoc2-docstring} weasyl.commishinfo.CURRENCY_PRECISION
    :summary:
    ```
* - {py:obj}`Currency <weasyl.commishinfo.Currency>`
  - ```{autodoc2-docstring} weasyl.commishinfo.Currency
    :summary:
    ```
* - {py:obj}`CURRENCY_CHARMAP <weasyl.commishinfo.CURRENCY_CHARMAP>`
  - ```{autodoc2-docstring} weasyl.commishinfo.CURRENCY_CHARMAP
    :summary:
    ```
* - {py:obj}`PRESET_COMMISSION_CLASSES <weasyl.commishinfo.PRESET_COMMISSION_CLASSES>`
  - ```{autodoc2-docstring} weasyl.commishinfo.PRESET_COMMISSION_CLASSES
    :summary:
    ```
````

### API

````{py:data} _MAX_PRICE
:canonical: weasyl.commishinfo._MAX_PRICE
:value: >
   99999999

```{autodoc2-docstring} weasyl.commishinfo._MAX_PRICE
```

````

````{py:data} CURRENCY_PRECISION
:canonical: weasyl.commishinfo.CURRENCY_PRECISION
:value: >
   2

```{autodoc2-docstring} weasyl.commishinfo.CURRENCY_PRECISION
```

````

````{py:data} Currency
:canonical: weasyl.commishinfo.Currency
:value: >
   'namedtuple(...)'

```{autodoc2-docstring} weasyl.commishinfo.Currency
```

````

````{py:data} CURRENCY_CHARMAP
:canonical: weasyl.commishinfo.CURRENCY_CHARMAP
:value: >
   None

```{autodoc2-docstring} weasyl.commishinfo.CURRENCY_CHARMAP
```

````

````{py:data} PRESET_COMMISSION_CLASSES
:canonical: weasyl.commishinfo.PRESET_COMMISSION_CLASSES
:value: >
   [('Visual', ['Sketch', 'Badge', 'Icon', 'Reference', 'Fullbody', 'Headshot', 'Chibi']), ('Literary',...

```{autodoc2-docstring} weasyl.commishinfo.PRESET_COMMISSION_CLASSES
```

````

````{py:function} parse_currency(target)
:canonical: weasyl.commishinfo.parse_currency

```{autodoc2-docstring} weasyl.commishinfo.parse_currency
```
````

````{py:function} _fetch_rates_no_cache_failure()
:canonical: weasyl.commishinfo._fetch_rates_no_cache_failure

```{autodoc2-docstring} weasyl.commishinfo._fetch_rates_no_cache_failure
```
````

````{py:function} _fetch_rates()
:canonical: weasyl.commishinfo._fetch_rates

```{autodoc2-docstring} weasyl.commishinfo._fetch_rates
```
````

````{py:function} _charmap_to_currency_code(charmap)
:canonical: weasyl.commishinfo._charmap_to_currency_code

```{autodoc2-docstring} weasyl.commishinfo._charmap_to_currency_code
```
````

````{py:function} convert_currency(value, valuecode, targetcode)
:canonical: weasyl.commishinfo.convert_currency

```{autodoc2-docstring} weasyl.commishinfo.convert_currency
```
````

````{py:function} currency_ratio(valuecode, targetcode)
:canonical: weasyl.commishinfo.currency_ratio

```{autodoc2-docstring} weasyl.commishinfo.currency_ratio
```
````

````{py:function} select_list(userid)
:canonical: weasyl.commishinfo.select_list

```{autodoc2-docstring} weasyl.commishinfo.select_list
```
````

````{py:function} select_commissionable(userid, q, commishclass, min_price, max_price, currency, offset, limit)
:canonical: weasyl.commishinfo.select_commissionable

```{autodoc2-docstring} weasyl.commishinfo.select_commissionable
```
````

````{py:function} create_commission_class(userid, title)
:canonical: weasyl.commishinfo.create_commission_class

```{autodoc2-docstring} weasyl.commishinfo.create_commission_class
```
````

````{py:function} create_price(userid, price, currency='', settings='')
:canonical: weasyl.commishinfo.create_price

```{autodoc2-docstring} weasyl.commishinfo.create_price
```
````

````{py:function} edit_class(userid, commishclass)
:canonical: weasyl.commishinfo.edit_class

```{autodoc2-docstring} weasyl.commishinfo.edit_class
```
````

````{py:function} edit_price(userid, price, currency, settings, edit_prices)
:canonical: weasyl.commishinfo.edit_price

```{autodoc2-docstring} weasyl.commishinfo.edit_price
```
````

````{py:function} edit_content(userid, content)
:canonical: weasyl.commishinfo.edit_content

```{autodoc2-docstring} weasyl.commishinfo.edit_content
```
````

````{py:function} remove_class(userid, classid)
:canonical: weasyl.commishinfo.remove_class

```{autodoc2-docstring} weasyl.commishinfo.remove_class
```
````

````{py:function} remove_price(userid, priceid)
:canonical: weasyl.commishinfo.remove_price

```{autodoc2-docstring} weasyl.commishinfo.remove_price
```
````
