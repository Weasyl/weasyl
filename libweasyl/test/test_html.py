from libweasyl import html


def test_html_to_text():
    assert html.html_to_text('<div style="text-align: center">**foo**</div><!-- comment -->') == "**foo**", "`html_to_text` should strip HTML tags"
    assert html.html_to_text('1 < 3 > 2 "foo"') == '1 < 3 > 2 "foo"', "the output of `html_to_text` should be plain text, not HTML"
    assert html.html_to_text("&copy;") == "©", "`html_to_text` should decode named character references"
    assert html.html_to_text("&#xec;") == "ì", "`html_to_text` should decode numeric character references"
    assert html.html_to_text('foo <img alt="bar"> baz') == "foo [bar] baz", "`html_to_text` should replace images with their alt text"
    assert html.html_to_text(" foo\nbar  baz\t") == "foo bar baz", "`html_to_text` should normalize whitespace"


def test_inline_json():
    assert html.inline_json('</script>') == r'"<\/script>"'
    assert html.inline_json('</SCRIPT>') == r'"<\/SCRIPT>"'
    assert html.inline_json('<!--<script>') == r'"<\!--<script>"'
