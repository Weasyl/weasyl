# Style

In general, code should follow [PEP 8]; `./wzl check` can be used to automatically check changes in the working tree against it.

Miscellaneous other guidelines follow.

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

## Commit messages

Shamelessly stolen from http://chris.beams.io/posts/git-commit/ and tweaked

 1. Separate subject from body with a blank line
 1. Capitalize the subject line
 1. Use the imperative mood in the subject line (e.g. 'Fix a bug in page header notification display' and not 'Fixes a bug' or 'Header notification stuff' etc.)
 1. Use the body to explain what and why vs. how

  [PEP 8]: https://www.python.org/dev/peps/pep-0008/ "PEP 8 -- Style Guide for Python Code"
  [google's style guide]: http://google.github.io/styleguide/pyguide.html?showone=Comments#Comments "Google's guidelines for docstrings"
  [sphinx-napoleon]: https://pypi.python.org/pypi/sphinxcontrib-napoleon 'the Sphinx "napoleon" extension documentation'
