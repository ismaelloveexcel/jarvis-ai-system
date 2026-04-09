import logging

from typing import Any, Dict, List
from litellm import completion
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_provider_api_key() -> str:
    if settings.LLM_API_KEY:
        return settings.LLM_API_KEY

    if settings.LLM_PROVIDER == "openai":
        return settings.OPENAI_API_KEY
    if settings.LLM_PROVIDER == "anthropic":
        return settings.ANTHROPIC_API_KEY
    if settings.LLM_PROVIDER == "xai":
        return settings.XAI_API_KEY

    return ""


def call_llm(messages: List[Dict[str, str]], temperature: float = 0.4, max_tokens: int = 800) -> str:
    api_key = get_provider_api_key()

    if not api_key:
        return "LLM is not configured yet. Add a valid API key in .env."

    model_name = f"{settings.LLM_PROVIDER}/{settings.LLM_MODEL}"

    response: Any = completion(
        model=model_name,
        messages=messages,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return response["choices"][0]["message"]["content"]


_CLASSIFY_PROMPT = """\
Classify the user's intent into exactly one category. Reply with ONLY the category name.

Categories:
- action: The user wants to perform a specific action (create file, fetch URL, call API, interact with GitHub repo)
- task: The user wants a multi-step plan or build (create app, generate plan, implement feature, design system)
- chat: General conversation, questions, or anything that doesn't fit the above

User message: {text}

Category:"""

# Keyword fallback for when LLM is not configured
_ACTION_KEYWORDS = [
    "create file", "write file", "make file",
    "fetch url", "call api", "http get",
    "github repo", "repo info",
]
_TASK_KEYWORDS = [
    "build", "create app", "generate plan",
    "set up", "implement", "design system",
]


def classify_intent(text: str) -> str:
    api_key = get_provider_api_key()
    if not api_key:
        # Fallback to keyword matching when no LLM key configured
        lower = text.lower()
        if any(k in lower for k in _ACTION_KEYWORDS):
            return "action"
        if any(k in lower for k in _TASK_KEYWORDS):
            return "task"
        return "chat"

    try:
        result = call_llm(
            [{"role": "user", "content": _CLASSIFY_PROMPT.format(text=text)}],
            temperature=0.0,
            max_tokens=10,
        )
        category = result.strip().lower()
        if category in ("action", "task", "chat"):
            return category
        return "chat"
    except Exception:
        logger.warning("LLM classify_intent failed, falling back to keywords")
        lower = text.lower()
        if any(k in lower for k in _ACTION_KEYWORDS):
            return "action"
        if any(k in lower for k in _TASK_KEYWORDS):
            return "task"
        return "chat"
