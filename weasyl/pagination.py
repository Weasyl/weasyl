from __future__ import annotations

from typing import NamedTuple
from typing import TypeVar


class PaginatedResult:
    # We expect select_list to have at least the following keyword arguments:
    # limit, back_id, next_id
    def __init__(self, select_list, select_count, id_field, url_format, *args, limit=None, count_limit=None, **kwargs):
        self.count_limit = count_limit
        self._query = select_list(*args, limit=limit, **kwargs)
        self._url_format = url_format

        if self._query:
            self._back_index = self._query[0][id_field]
            self._next_index = self._query[-1][id_field]

        if select_count and self._query:
            self._has_counts = True

            kwargs['backid'] = self._back_index
            kwargs['nextid'] = None
            self._back_count = select_count(*args, **kwargs)

            kwargs['backid'] = None
            kwargs['nextid'] = self._next_index
            self._next_count = select_count(*args, **kwargs)
        else:
            self._has_counts = False

    @property
    def query(self):
        return self._query

    @property
    def next_count(self):
        return self._next_count if self._has_counts else 0

    @property
    def back_count(self):
        return self._back_count if self._has_counts else 0

    @property
    def has_counts(self):
        return self._has_counts

    @property
    def back_url(self):
        return self._url_format % ("backid=" + str(self._back_index))

    @property
    def next_url(self):
        return self._url_format % ("nextid=" + str(self._next_index))


class _FirstPage:
    __slots__ = ()
    is_back = False

    def compat(self) -> tuple[int, int]:
        return (0, 0)


FIRST_PAGE = _FirstPage()


class PrevFilter(NamedTuple):
    is_back = True
    backid: int

    def compat(self) -> tuple[int, int]:
        return (self.backid, 0)


class NextFilter(NamedTuple):
    is_back = False
    nextid: int

    def compat(self) -> tuple[int, int]:
        return (0, self.nextid)


PageFilter = _FirstPage | PrevFilter | NextFilter

T = TypeVar("T")


def paginate(items: list[T], *, limit: int, page: PageFilter, key: str) -> tuple[PageFilter | None, PageFilter | None]:
    """
    Given a list of items retrieved according to the limit `limit + 1` and the order/bounds of `page`, trim and rearrange the list as needed for display.

    Args:
        items: The items on the page, sorted by their `key` key. Forward pages (the first page and `NextFilter` pages) are sorted in the opposite order of back pages (`PrevFilter`). Usually, forward pages are in descending key order (i.e. pages in reverse chronological order).
        limit: The maximum number of items on the page. When the page isn't the last page in its direction, `len(items) == limit + 1`.

    Returns:
        The filters for the previous page and the next page.
    """
    # Selected one more result than will be returned to check if there’s a next page in the queried direction.
    has_more = len(items) == limit + 1
    if has_more:
        del items[-1]

    is_back = page.is_back
    if is_back:
        items.reverse()

    # A surrounding page is absent in any of these cases:
    # - there are no results
    # - `has_more` checked in that direction and returned a negative
    # - it’s the back page of the first page
    prev_page = (
        None if page is FIRST_PAGE or ((not has_more) and is_back) or not items
        else PrevFilter(items[0][key])
    )
    next_page = (
        None if ((not has_more) and (not is_back)) or not items
        else NextFilter(items[-1][key])
    )
    return prev_page, next_page


def page_from_compat(backid: int | None, nextid: int | None) -> PageFilter:
    if backid:
        return PrevFilter(backid)
    if nextid:
        return NextFilter(nextid)
    return FIRST_PAGE
