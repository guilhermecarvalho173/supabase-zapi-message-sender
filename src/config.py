import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_key: str
    contacts_table: str
    contact_name_column: str
    contact_phone_column: str
    zapi_instance_id: str
    zapi_token: str
    zapi_client_token: str | None


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variável de ambiente obrigatória não configurada: {name}")
    return value.strip()


def get_optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if not value:
        return None

    value = value.strip()
    return value or None


def normalize_supabase_url(url: str) -> str:
    return url.removesuffix("/").removesuffix("/rest/v1")


settings = Settings(
    supabase_url=normalize_supabase_url(get_required_env("SUPABASE_URL")),
    supabase_key=get_required_env("SUPABASE_KEY"),
    contacts_table=os.getenv("SUPABASE_CONTACTS_TABLE", "contatos"),
    contact_name_column=os.getenv("SUPABASE_CONTACT_NAME_COLUMN", "nome"),
    contact_phone_column=os.getenv("SUPABASE_CONTACT_PHONE_COLUMN", "telefone"),
    zapi_instance_id=get_required_env("ZAPI_INSTANCE_ID"),
    zapi_token=get_required_env("ZAPI_TOKEN"),
    zapi_client_token=get_optional_env("ZAPI_CLIENT_TOKEN"),
)
