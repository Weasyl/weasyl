from weasyl import searchtag


valid_tags = {'test*', '*test', 'te*st', 'test', 'test_too'}


def test_parse_restricted_tags():
    """
    Ensure that ``searchtag.parse_restricted_tags()`` functions as expected.

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
    invalid_tags = {'*', '**', '***', 'a*', '*a', 'a*a*', '*a*a', '*aa*', 'a**a', '}'}
    combined_tags = valid_tags | invalid_tags

    # Function under test
    resultant_tags = searchtag.parse_restricted_tags(" ".join(combined_tags))

    # Verify that we have the tags in the valid list
    assert resultant_tags == valid_tags


def test_uppercase_tags_are_converted_to_lowercase():
    uppercase_tags = {'OMEGA_RUBY', 'ALPHA_SAPPHIRE', 'DIAMOND', 'PEARL', 'DIGI_*'}
    lowercase_tags = {'omega_ruby', 'alpha_sapphire', 'diamond', 'pearl', 'digi_*'}

    assert lowercase_tags == searchtag.parse_restricted_tags(" ".join(uppercase_tags))


def test_overlong_tags_are_dropped():
    lengthy_tags = {"a" * 161, "a" * 162, "a" * 163}
    valid_with_lengthy = valid_tags | {"a" * 161, "a" * 162}

    assert valid_with_lengthy == searchtag.parse_restricted_tags(" ".join(valid_tags | lengthy_tags))
