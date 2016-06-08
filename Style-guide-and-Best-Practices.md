# Style

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

# Branch Hygiene

Master should always be deployable. This means that no pull request should be merged until we consider it ready for production. Some rules of thumb for what that means in practice:

 * New features should have tests to maintain or improve our codebase's test coverage.
 * Changes to the web api should have documentation ready to go before being merged.
 * Changes should pass style checks.

If we ever put master in a state where it is not deployable, we should revert the merge commit.

## Commit messages

 1. Separate subject from body with a blank line
 2. Try to limit the subject line to 50 characters
 3. Capitalize the subject line
 4. Do not end the subject line with a period
 5. Use the imperative mood in the subject line (e.g. 'Fix a bug in page header notification display' and not 'Fixes a bug' or 'Header notification stuff' etc.)
 6. Wrap the body at 72 characters
 7. Use the body to explain what and why vs. how

  [PEP 8]: https://www.python.org/dev/peps/pep-0008/ "PEP 8 -- Style Guide for Python Code"
  [google's style guide]: http://google.github.io/styleguide/pyguide.html?showone=Comments#Comments "Google's guidelines for docstrings"
  [sphinx-napoleon]: https://pypi.python.org/pypi/sphinxcontrib-napoleon 'the Sphinx "napoleon" extension documentation'