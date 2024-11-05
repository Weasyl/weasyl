# {py:mod}`libweasyl.exceptions`

```{py:module} libweasyl.exceptions
```

```{autodoc2-docstring} libweasyl.exceptions
:allowtitles:
```

## Module Contents

### API

````{py:exception} WeasylError()
:canonical: libweasyl.exceptions.WeasylError

Bases: {py:obj}`Exception`

```{autodoc2-docstring} libweasyl.exceptions.WeasylError
```

```{rubric} Initialization
```

```{autodoc2-docstring} libweasyl.exceptions.WeasylError.__init__
```

````

`````{py:exception} ExpectedWeasylError()
:canonical: libweasyl.exceptions.ExpectedWeasylError

Bases: {py:obj}`libweasyl.exceptions.WeasylError`

```{autodoc2-docstring} libweasyl.exceptions.ExpectedWeasylError
```

```{rubric} Initialization
```

```{autodoc2-docstring} libweasyl.exceptions.ExpectedWeasylError.__init__
```

````{py:attribute} code
:canonical: libweasyl.exceptions.ExpectedWeasylError.code
:value: >
   403

```{autodoc2-docstring} libweasyl.exceptions.ExpectedWeasylError.code
```

````

`````

`````{py:exception} InvalidFileFormat()
:canonical: libweasyl.exceptions.InvalidFileFormat

Bases: {py:obj}`libweasyl.exceptions.ExpectedWeasylError`

```{autodoc2-docstring} libweasyl.exceptions.InvalidFileFormat
```

```{rubric} Initialization
```

```{autodoc2-docstring} libweasyl.exceptions.InvalidFileFormat.__init__
```

````{py:attribute} code
:canonical: libweasyl.exceptions.InvalidFileFormat.code
:value: >
   422

```{autodoc2-docstring} libweasyl.exceptions.InvalidFileFormat.code
```

````

`````

`````{py:exception} UnknownFileFormat()
:canonical: libweasyl.exceptions.UnknownFileFormat

Bases: {py:obj}`libweasyl.exceptions.ExpectedWeasylError`

```{autodoc2-docstring} libweasyl.exceptions.UnknownFileFormat
```

```{rubric} Initialization
```

```{autodoc2-docstring} libweasyl.exceptions.UnknownFileFormat.__init__
```

````{py:attribute} code
:canonical: libweasyl.exceptions.UnknownFileFormat.code
:value: >
   422

```{autodoc2-docstring} libweasyl.exceptions.UnknownFileFormat.code
```

````

`````

````{py:exception} ThumbnailingError()
:canonical: libweasyl.exceptions.ThumbnailingError

Bases: {py:obj}`libweasyl.exceptions.WeasylError`

```{autodoc2-docstring} libweasyl.exceptions.ThumbnailingError
```

```{rubric} Initialization
```

```{autodoc2-docstring} libweasyl.exceptions.ThumbnailingError.__init__
```

````
