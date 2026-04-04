import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Explicit absolute path relative to this file — works regardless of
# which directory uvicorn is launched from.
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
load_dotenv(dotenv_path=_env_path, override=True)


class Settings(BaseSettings):
    gemini_api_key: str = ""
    google_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    xai_api_key: str = ""
    xai_base_url: str = "https://api.x.ai/v1"
    firecrawl_api_key: str = ""
    firecrawl_base_url: str = "https://api.firecrawl.dev/v2"
    tavily_api_key: str = ""
    tavily_base_url: str = "https://api.tavily.com"
    github_token: str = ""
    github_api_base_url: str = "https://api.github.com"
    langsmith_api_key: str = ""
    langsmith_tracing: str = "true"
    langsmith_project: str = "langcanvas"

    supabase_url: str = ""
    supabase_service_key: str = ""

    default_provider: str = "gemini"
    planner_provider: str = ""
    research_provider: str = ""
    synthesis_provider: str = ""
    canvas_provider: str = ""

    model_planner: str = ""
    model_research: str = ""
    model_synthesis: str = ""
    model_canvas: str = ""

    model_explainer: str = "gemini-3.1-pro-preview"
    model_visualizer: str = "gemini-3-flash-preview"
    model_doc_router: str = "gemini-3.1-flash-lite-preview"

    class Config:
        env_file = _env_path  # absolute path — pydantic-settings can accept this
        env_file_encoding = "utf-8"
        extra = "ignore"

    def provider_for_role(self, role: str) -> str:
        provider = getattr(self, f"{role}_provider", "")
        return (provider or self.default_provider or "gemini").lower()

    def model_for_role(self, role: str) -> str:
        explicit_model = getattr(self, f"model_{role}", "")
        if explicit_model:
            return explicit_model

        legacy_defaults = {
            "planner": self.model_doc_router,
            "research": self.model_doc_router,
            "synthesis": self.model_explainer,
            "canvas": self.model_visualizer,
        }
        return legacy_defaults.get(role, self.model_explainer)


settings = Settings()

_resolved_key = settings.google_api_key or settings.gemini_api_key
if _resolved_key:
    os.environ["GOOGLE_API_KEY"] = _resolved_key

print(f"[config] .env path:   {_env_path}")
print(f"[config] .env exists: {os.path.exists(_env_path)}")
print(f"[config] GEMINI_API_KEY: {'YES' if settings.gemini_api_key else 'NO'}")
print(f"[config] OPENAI_API_KEY: {'YES' if settings.openai_api_key else 'NO'}")
print(f"[config] ANTHROPIC_API_KEY: {'YES' if settings.anthropic_api_key else 'NO'}")
print(f"[config] XAI_API_KEY: {'YES' if settings.xai_api_key else 'NO'}")
print(f"[config] FIRECRAWL_API_KEY: {'YES' if settings.firecrawl_api_key else 'NO'}")
print(f"[config] TAVILY_API_KEY: {'YES' if settings.tavily_api_key else 'NO'}")
print(f"[config] GITHUB_TOKEN: {'YES' if settings.github_token else 'NO'}")
print(f"[config] GOOGLE_API_KEY env: {'YES' if os.environ.get('GOOGLE_API_KEY') else 'NO'}")
print(f"[config] SUPABASE_URL: {settings.supabase_url[:30] if settings.supabase_url else 'EMPTY'}")
