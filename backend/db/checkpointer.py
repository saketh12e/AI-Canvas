from backend.config import settings


def get_postgres_connection_string() -> str:
    """Build psycopg connection string from Supabase config.

    Accepts two forms of SUPABASE_URL:
      1. Direct Postgres URL:  postgresql://postgres:PASSWORD@host:5432/postgres
         → returned as-is
      2. Supabase dashboard URL: https://PROJECT.supabase.co
         → derive the standard Supabase direct connection string
    """
    url = settings.supabase_url
    key = settings.supabase_service_key
    if url.startswith("postgresql://") or url.startswith("postgres://"):
        # Already a valid Postgres connection string — use directly
        return url
    # Supabase dashboard URL: extract project ref
    project_ref = url.replace("https://", "").split(".")[0]
    return f"postgresql://postgres:{key}@db.{project_ref}.supabase.co:5432/postgres"

# NOTE: AsyncPostgresSaver.from_conn_string() in langgraph-checkpoint-postgres ≥3.0
# returns an _AsyncGeneratorContextManager.  Callers must use it as:
#
#   async with AsyncPostgresSaver.from_conn_string(conn_str) as cp:
#       await cp.setup()
#
# This is handled in main.py lifespan so the connection stays open for the
# lifetime of the FastAPI process.
