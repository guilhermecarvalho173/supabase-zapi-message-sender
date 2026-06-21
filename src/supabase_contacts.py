from dataclasses import dataclass
from datetime import UTC, datetime

from supabase import create_client

from src.config import settings


@dataclass(frozen=True)
class Contact:
    id: int
    name: str
    phone: str


def get_supabase_client():
    return create_client(settings.supabase_url, settings.supabase_key)


def fetch_contacts() -> list[Contact]:
    client = get_supabase_client()
    columns = f"id,{settings.contact_name_column},{settings.contact_phone_column},sent_at"

    response = (
        client.table(settings.contacts_table)
        .select(columns)
        .is_("sent_at", "null")
        .execute()
    )

    contacts: list[Contact] = []
    for row in response.data or []:
        name = str(row.get(settings.contact_name_column, "")).strip()
        phone = str(row.get(settings.contact_phone_column, "")).strip()

        if not name or not phone:
            continue

        contacts.append(Contact(id=int(row["id"]), name=name, phone=phone))

    return contacts


def mark_contact_as_sent(contact_id: int) -> None:
    client = get_supabase_client()
    sent_at = datetime.now(UTC).isoformat()

    (
        client.table(settings.contacts_table)
        .update({"sent_at": sent_at})
        .eq("id", contact_id)
        .execute()
    )
