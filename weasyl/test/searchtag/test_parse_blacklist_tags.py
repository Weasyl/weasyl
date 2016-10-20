# encoding: utf-8

from __future__ import absolute_import

import pytest

from weasyl import searchtag


def test_parse_blacklist_tags():
    """
    Ensure that ``searchtag.parse_blacklist_tags() functions as expected.

    Additionally tests ``_SEARCHTAG_BLACKLIST_REGEXP_PATTERN`` as a consequence
      of testing this function.

    Valid patterns include:
        - test*     (Wildcard at the end);
        - *test     (Wildcard at the start);
        - te*st     (Wildcard in the middle);
        - test      (A raw tag with no wildcard); and
        - test_too  (Underscores are also permitted)

    Invalid patterns include:
        - *             (No raw wildcards)
        - a* or *a      (Must have at least two alphanumeric characters with a wildcard)
        - a*a*, *a*a, *aa*, or a**a  (Only one asterisk per tag)
        - Anything that does not meet the same requirements of ``searchtag.parse_tags()``, 
            since this function essentially reimplements and extends that function.
            Example, unicode characters.
    """
    valid_tags = set(['test*', '*test', 'te*st', 'test', 'test_too'])
    invalid_tags = set(['*', 'a*', '*a', 'a*a*', '*a*a', '*aa*', 'a**a', '✔'])
    combined_tags = valid_tags | invalid_tags

    # Function under test
    resultant_tags = searchtag.parse_blacklist_tags(u", ".join(combined_tags))

    # Verify that we have the tags in the valid list
    for valid_result in resultant_tags:
        assert valid_result in valid_tags

    # Verify that no invalid tags were returned
    for result in resultant_tags:
        assert result not in invalid_tags
