from libweasyl import html


def test_inline_json():
    assert html.inline_json('</script>') == r'"\u003c/script>"'
    assert html.inline_json('</SCRIPT>') == r'"\u003c/SCRIPT>"'
    assert html.inline_json('<!--<script>') == r'"\u003c!--\u003cscript>"'
