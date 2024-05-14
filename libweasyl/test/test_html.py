from libweasyl import html


def test_strip_html():
    assert html.strip_html('<div style="text-align: center">**foo**</div> <!-- comment -->') == "**foo** ", "`strip_html` should strip HTML tags"


def test_inline_json():
    assert html.inline_json('</script>') == r'"<\/script>"'
    assert html.inline_json('</SCRIPT>') == r'"<\/SCRIPT>"'
    assert html.inline_json('<!--<script>') == r'"<\!--<script>"'
