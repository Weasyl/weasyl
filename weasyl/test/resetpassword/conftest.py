import re

import pytest

from weasyl import emailer


@pytest.fixture
def captured_tokens(monkeypatch):
    result = {}

    def capture_token(mailto, subject, content):
        token = re.search(r"\?token=(.*)", content).group(1)
        result[mailto] = token

    monkeypatch.setattr(emailer, "send", capture_token)

    return result
