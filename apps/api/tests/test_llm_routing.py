"""Tests for LLM routing / classify_intent."""
from app.core.llm import classify_intent


def test_classify_action_keywords():
    assert classify_intent("create file readme.md") == "action"
    assert classify_intent("fetch url from API") == "action"
    assert classify_intent("github repo info") == "action"


def test_classify_task_keywords():
    assert classify_intent("build a web scraper") == "task"
    assert classify_intent("create app for tracking expenses") == "task"
    assert classify_intent("implement user auth") == "task"


def test_classify_chat_fallback():
    assert classify_intent("hello how are you") == "chat"
    assert classify_intent("what time is it") == "chat"


def test_classify_empty_string():
    assert classify_intent("") == "chat"
