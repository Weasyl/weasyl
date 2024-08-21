
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
