from unittest.mock import Mock

import pytest


@pytest.fixture
def response_signature(monkeypatch):
    """
    Fixture that patches response signature verification.

    Yields headers that should be added to the response.
    """
    monkeypatch.setattr('mohawk.Sender.accept_response', Mock())

    yield {
        'server-authorization': 'hawk-sig',
        'content-type': 'application/json',
    }
