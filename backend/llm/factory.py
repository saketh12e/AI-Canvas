from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from backend.config import settings


def get_llm(role: str, provider: str | None = None, temperature: float = 0):
    provider_name = (provider or settings.provider_for_role(role)).lower()
    model_name = settings.model_for_role(role)

    if provider_name == "gemini":
        api_key = settings.google_api_key or settings.gemini_api_key
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY is required for Gemini.")
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=temperature,
        )

    if provider_name == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI.")
        return ChatOpenAI(
            model=model_name,
            api_key=settings.openai_api_key,
            temperature=temperature,
        )

    if provider_name == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Anthropic.")
        return ChatAnthropic(
            model=model_name,
            api_key=settings.anthropic_api_key,
            temperature=temperature,
        )

    if provider_name == "grok":
        if not settings.xai_api_key:
            raise ValueError("XAI_API_KEY is required for Grok.")
        return ChatOpenAI(
            model=model_name,
            api_key=settings.xai_api_key,
            base_url=settings.xai_base_url,
            temperature=temperature,
        )

    raise ValueError(f"Unsupported provider '{provider_name}'.")
