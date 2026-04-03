from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from backend.config import settings


def _runtime_key(runtime_keys: dict[str, str] | None, key: str) -> str:
    return (runtime_keys or {}).get(key, "")


def provider_is_configured(provider: str, runtime_keys: dict[str, str] | None = None) -> bool:
    provider_name = provider.lower()
    if provider_name == "gemini":
        return bool(
            _runtime_key(runtime_keys, "gemini_api_key")
            or settings.google_api_key
            or settings.gemini_api_key
        )
    if provider_name == "openai":
        return bool(_runtime_key(runtime_keys, "openai_api_key") or settings.openai_api_key)
    if provider_name == "anthropic":
        return bool(
            _runtime_key(runtime_keys, "anthropic_api_key") or settings.anthropic_api_key
        )
    if provider_name == "grok":
        return bool(_runtime_key(runtime_keys, "xai_api_key") or settings.xai_api_key)
    return False


def get_provider_capabilities(
    runtime_keys: dict[str, str] | None = None,
) -> list[dict[str, str | bool]]:
    providers = [
        ("gemini", "Gemini"),
        ("openai", "OpenAI"),
        ("anthropic", "Anthropic"),
        ("grok", "Grok"),
    ]
    result: list[dict[str, str | bool]] = []
    for key, label in providers:
        available = provider_is_configured(key, runtime_keys=runtime_keys)
        result.append(
            {
                "key": key,
                "label": label,
                "available": available,
                "reason": "" if available else "API key required in settings or .env",
            }
        )
    return result


def get_llm(
    role: str,
    provider: str | None = None,
    temperature: float = 0,
    runtime_keys: dict[str, str] | None = None,
):
    provider_name = (provider or settings.provider_for_role(role)).lower()
    model_name = settings.model_for_role(role)

    if provider_name == "gemini":
        api_key = (
            _runtime_key(runtime_keys, "gemini_api_key")
            or settings.google_api_key
            or settings.gemini_api_key
        )
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY is required for Gemini.")
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=temperature,
        )

    if provider_name == "openai":
        api_key = _runtime_key(runtime_keys, "openai_api_key") or settings.openai_api_key
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI.")
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            temperature=temperature,
        )

    if provider_name == "anthropic":
        api_key = _runtime_key(runtime_keys, "anthropic_api_key") or settings.anthropic_api_key
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Anthropic.")
        return ChatAnthropic(
            model=model_name,
            api_key=api_key,
            temperature=temperature,
        )

    if provider_name == "grok":
        api_key = _runtime_key(runtime_keys, "xai_api_key") or settings.xai_api_key
        if not api_key:
            raise ValueError("XAI_API_KEY is required for Grok.")
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=settings.xai_base_url,
            temperature=temperature,
        )

    raise ValueError(f"Unsupported provider '{provider_name}'.")
