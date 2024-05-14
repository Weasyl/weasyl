from libweasyl import html


def test_strip_html():
    assert html.strip_html('<div style="text-align: center">**foo**</div> <!-- comment -->') == "**foo** ", "`strip_html` should strip HTML tags"
    assert html.strip_html('1 < 3 > 2 "foo"') == '1 < 3 > 2 "foo"', "the output of `strip_html` should be plain text, not HTML"
    assert html.strip_html("&copy;") == "©", "`strip_html` should decode named character references"
    assert html.strip_html("&#xec;") == "ì", "`strip_html` should decode numeric character references"


def test_inline_json():
    assert html.inline_json('</script>') == r'"<\/script>"'
    assert html.inline_json('</SCRIPT>') == r'"<\/SCRIPT>"'
    assert html.inline_json('<!--<script>') == r'"<\!--<script>"'
