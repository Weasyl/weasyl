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

  [PEP 8]: https://www.python.org/dev/peps/pep-0008/ "PEP 8 -- Style Guide for Python Code"