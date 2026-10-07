from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root's .env, found regardless of the process's working directory
# (Makefile targets run from server/, where no .env exists; Docker
# containers don't need this since env_file: in compose sets real
# process env vars instead of relying on this dotenv lookup).
_ROOT_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ROOT_ENV_FILE, extra="ignore")

    app_env: Literal["local", "gcp", "test"] = "local"

    site_name: str = "Default site"
    web_base_url: str = ""

    wp_base_url: str = ""
    wp_username: str = ""
    wp_app_password: str = ""

    credential_encryption_key: str = ""
