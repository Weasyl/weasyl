import unittest
import weasyl.pagination as pagination


ID_FIELD = 'id_field'


def fake_result(id):
    return {ID_FIELD: id}


def fake_results(ids):
    return [fake_result(id) for id in ids]


class PaginationTestCase(unittest.TestCase):
    def test_simple_case(self):
        result_size = 10
        check_limit = 20
        extra_value = "hello"

        def select_list(a, b, c, limit, backid=None, nextid=None, extra=None):
            self.assertEqual(extra_value, extra)
            self.assertEqual(check_limit, limit)
            return fake_results(range(result_size))

        def select_count(a, b, c, backid=None, nextid=None, extra=None):
            self.assertEqual(extra_value, extra)
            if backid is not None:
                return backid
            if nextid is not None:
                return nextid
            # should get one or the other
            raise ValueError()

        result = pagination.PaginatedResult(select_list, select_count, ID_FIELD, "%s",
                                            1, 2, 3, check_limit, extra=extra_value)
        self.assertEqual(result_size - 1, result.next_count)
        self.assertEqual(0, result.back_count)
        self.assertEqual(result_size, len(result.query))
        self.assertEqual("nextid=" + str(result_size - 1), result.next_url)
