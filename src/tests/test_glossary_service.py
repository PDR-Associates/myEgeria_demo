""" python

   PDX-License-Identifier: Apache-2.0
   Copyright Contributors to the ODPi Egeria project.

   This file is a unit test for my_egeria.


"""

import pytest
from ..services.glossary_service import GlossaryService


def test_glossary_service_env_missing(monkeypatch):
    monkeypatch.delenv("EGERIA_SERVER_URL", raising=False)
    monkeypatch.delenv("EGERIA_SERVER_NAME", raising=False)
    with pytest.raises(ConnectionError):
        GlossaryService()


def test_glossary_service_connection(monkeypatch):
    class MockGlossaryClient:
        def get_glossaries(self):
            return [{"guid": "123", "displayName": "Test Glossary"}]

        def get_terms(self, guid):
            return [{"displayName": "Test Term"}]

    monkeypatch.setenv("EGERIA_SERVER_URL", "http://localhost:8080")
    monkeypatch.setenv("EGERIA_SERVER_NAME", "test")
    monkeypatch.setattr(
        "services.glossary_service.GlossaryAuthorView",
        lambda *a, **k: MockGlossaryClient(),
    )

    service = GlossaryService()
    glossaries = service.list_glossaries()
    assert glossaries[0]["displayName"] == "Test Glossary"

    # terms = service.list_terms("123")
    # assert terms[0]["displayName"] == "Test Term"
