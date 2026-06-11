import os
import tomllib
from pathlib import Path
from urllib.parse import quote_plus

ROOT_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv # type: ignore
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv(ROOT_DIR / ".env")


def _database_url_from_streamlit_secrets():
    secrets_path = ROOT_DIR / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        return None

    with secrets_path.open("rb") as secrets_file:
        secrets = tomllib.load(secrets_file)

    direct_url = secrets.get("DATABASE_URL") or secrets.get("database_url")
    if direct_url:
        return direct_url

    postgresql = secrets.get("connections", {}).get("postgresql")
    if not postgresql:
        return None

    dialect = postgresql.get("dialect", "postgresql")
    username = quote_plus(str(postgresql["username"]))
    password = quote_plus(str(postgresql["password"]))
    host = postgresql["host"]
    port = postgresql.get("port", 5432)
    database = postgresql["database"]

    return f"{dialect}://{username}:{password}@{host}:{port}/{database}"


DATABASE_URL = os.getenv("DATABASE_URL") or _database_url_from_streamlit_secrets()
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL nao definida. Configure .env ou .streamlit/secrets.toml com a conexao do Supabase."
    )

RAW_DATA_DIR = ROOT_DIR / "data" / "01_raw"
