import json

from libweasyl import html


def test_inline_json(monkeypatch):
    monkeypatch.setattr(html, 'json', json)
    assert html.inline_json('</script>') == r'"<\/script>"'
    assert html.inline_json('</SCRIPT>') == r'"<\/SCRIPT>"'
    assert html.inline_json('<!--<script>') == r'"<\!--<script>"'
