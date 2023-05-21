from libweasyl import html


def test_inline_json():
    assert html.inline_json('</script>') == r'"<\/script>"'
    assert html.inline_json('</SCRIPT>') == r'"<\/SCRIPT>"'
    assert html.inline_json('<!--<script>') == r'"<\!--<script>"'
