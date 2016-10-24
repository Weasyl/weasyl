from __future__ import absolute_import

import pytest

from weasyl import searchtag


def test_parse_blacklist_tags():
    """
    Ensure that ``searchtag.parse_blacklist_tags() functions as expected.

    Examples of valid patterns include:
        - test*     (Wildcard at the end);
        - *test     (Wildcard at the start);
        - te*st     (Wildcard in the middle);
        - test      (A raw tag with no wildcard); and
        - test_too  (Underscores are also permitted)

    Examples of invalid patterns include:
        - *             (No raw wildcards)
        - a* or *a      (Must have at least two alphanumeric characters with a wildcard)
        - a*a*, *a*a, *aa*, or a**a  (Only one asterisk per tag)
        - }     Anything that wouldn't be returned by ``searchtag.parse_tags()``,
            since this function essentially reimplements and extends that function.
    """
    valid_tags = {'test*', '*test', 'te*st', 'test', 'test_too'}
    invalid_tags = {'*', '**', '***', 'a*', '*a', 'a*a*', '*a*a', '*aa*', 'a**a', '}'}
    combined_tags = valid_tags | invalid_tags

    # Function under test
    resultant_tags = searchtag.parse_blacklist_tags(" ".join(combined_tags))

    # Verify that we have the tags in the valid list
    assert len(resultant_tags) == len(valid_tags)
    for valid_result in valid_tags:
        assert valid_result in resultant_tags

    # Verify that no invalid tags were returned
    for invalid_result in invalid_tags:
        assert invalid_result not in resultant_tags
