In general, code should follow [PEP 8]; `make check` can be used to automatically check changes in the working tree against it.

Miscellaneous other guidelines follow.

## Trailing commas

When a comma-separated list spans multiple lines, the last line should include a trailing comma.

```python
numbers = [
    "one",
    "two",
    "three",  # a trailing comma
]
```

```python
translations = {
    "apple": "pomme",
    "banana": "banane",
    "carrot": "carotte",  # another
}
```

```python
engine.execute(
    "INSERT INTO temperatures (high, low, average) "
    "VALUES (%(high)s, %(low)s, %(average)s)",
    high=34.0,
    low=-4.0,
    average=19.6,  # here too
)
```

## Docstrings

Docstrings should generally follow [google's style guide], including arguments and return blocks for methods. Be sure to include types for all parameters and the return value, either at the start of the description or in parenthesis and default values if any.  reStructuredText formatting is great where appropriate. Example:
```
def image_extension(im):
    """
    Given a sanpera ``Image``, return the file extension corresponding with the
    original format of the image.
    Parameters:
        im: A sanpera ``Image``.
    Returns:
        :term:`native string`: one of ``.jpg``, ``.png``, ``.gif``, or ``None``
        if the format was unknown.
    """
```

See libweasyl and [sphinx-napoleon] for more examples.

## Line length

We don't enforce a line length limit. That being said, lines longer than 100 characters should be avoided.

  [PEP 8]: https://www.python.org/dev/peps/pep-0008/ "PEP 8 -- Style Guide for Python Code"
  [google's style guide]: http://google.github.io/styleguide/pyguide.html?showone=Comments#Comments "Google's guidelines for docstrings"
  [sphinx-napoleon]: https://pypi.python.org/pypi/sphinxcontrib-napoleon 'the Sphinx "napoleon" extension documentation'