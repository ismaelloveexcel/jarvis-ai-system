from typing import Any, Dict, List
from litellm import completion
from app.core.config import settings


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
