"""
Unit tests for reasoning/authority_agent.py using a mocked OpenAI client
— no live API key or network call required.
Run with: pytest test_authority_agent.py -v
"""
from unittest.mock import MagicMock, patch

import pytest

from reasoning.authority_agent import generate_complaint, AuthorityAgentError, _load_authority_mapping


def test_authority_mapping_loads_and_covers_all_categories():
    mapping = _load_authority_mapping()
    expected_categories = {
        "flooding", "waterlogging", "road_damage", "construction",
        "safety", "environmental", "traffic", "other",
    }
    assert expected_categories.issubset(mapping.keys())


def test_missing_api_key_raises_error(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(AuthorityAgentError):
        generate_complaint(category="flooding", assessment={}, context={})


@patch("reasoning.authority_agent.OpenAI")
def test_successful_generation_returns_expected_fields(mock_openai_cls, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key-for-test")

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='''
        {
            "title": "Recurring waterlogging on Main Street",
            "description": "Multiple citizen reports and terrain data confirm...",
            "severity": "High",
            "recommended_action": "Clear storm drain and inspect within 48 hours.",
            "responsible_authority": "Municipal Drainage & Flood Control Department"
        }
    '''))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai_cls.return_value = mock_client

    result = generate_complaint(
        category="flooding",
        assessment={"severity": "High", "explanation": "x", "recommended_action": "y"},
        context={"verigrid": {}, "mireye": None, "noaa": None},
    )

    assert result["severity"] == "High"
    assert "Drainage" in result["responsible_authority"]
    assert result["title"]
    assert result["description"]


@patch("reasoning.authority_agent.OpenAI")
def test_invalid_severity_raises_error(mock_openai_cls, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key-for-test")

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='''
        {
            "title": "x", "description": "x", "severity": "Extreme",
            "recommended_action": "x", "responsible_authority": "x"
        }
    '''))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai_cls.return_value = mock_client

    with pytest.raises(AuthorityAgentError):
        generate_complaint(category="flooding", assessment={}, context={})


@patch("reasoning.authority_agent.OpenAI")
def test_missing_required_field_raises_error(mock_openai_cls, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key-for-test")

    mock_client = MagicMock()
    mock_response = MagicMock()
    # Missing "responsible_authority"
    mock_response.choices = [MagicMock(message=MagicMock(content='''
        {"title": "x", "description": "x", "severity": "Low", "recommended_action": "x"}
    '''))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai_cls.return_value = mock_client

    with pytest.raises(AuthorityAgentError):
        generate_complaint(category="flooding", assessment={}, context={})  