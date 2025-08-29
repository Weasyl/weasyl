from collections.abc import Hashable
from collections.abc import Iterable
from typing import Generic
from typing import Literal
from typing import TypeVar


T = TypeVar("T", bound=Hashable)

_Inner = Literal[True] | dict[T, "_Inner[T]"]


class Trie(Generic[T]):
    """
    A set of sequences that supports an efficient `contains_prefix_of`.

    >>> t = Trie([("example", "foo"), ("example", "bar")])
    >>> t.contains_prefix_of(("example", "foo", "sub"))
    True
    >>> t.contains_prefix_of(("example", "bar"))
    True
    >>> t.contains_prefix_of(("example", "baz"))
    False
    >>> t.contains_prefix_of(("example",))
    False
    >>> Trie([()]).contains_prefix_of(("any", "sequence"))
    True
    >>> Trie([]).contains_prefix_of(("any", "sequence"))
    False
    """
    __slots__ = ("_root",)

    _root: _Inner[T]

    def __init__(self, items: Iterable[Iterable[T]]) -> None:
        self._root = {}

        for item in items:
            self.add(item)

    def add(self, item: Iterable[T]) -> None:
        prev = None
        node = self._root

        for component in item:
            if node is True:
                return

            prev = node
            node = node.setdefault(component, {})

        if prev is None:
            self._root = True
            return

        prev[component] = True

    def contains_prefix_of(self, path: Iterable[T]) -> bool:
        """
        Check whether the trie contains any prefix of the provided iterable.
        """
        node = self._root

        for component in path:
            if node is True:
                return True

            if component not in node:
                return False

            node = node[component]

        return node is True
