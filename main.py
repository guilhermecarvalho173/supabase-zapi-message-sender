from dataclasses import dataclass
import re

import requests
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from src.config import settings
from src.logger import configure_logger
from src.supabase_contacts import fetch_contacts, mark_contact_as_sent
from src.zapi_client import ZApiClient


logger = configure_logger()


@dataclass
class SendResult:
    total: int
    success: int = 0
    failure: int = 0

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0

        return self.success / self.total * 100


def build_message(contact_name: str) -> str:
    if not isinstance(contact_name, str) or not contact_name.strip():
        raise ValueError("Nome do contato inválido.")

    return f"Olá, {contact_name.strip()} tudo bem com você?"


def normalize_phone(phone: str) -> str:
    normalized_phone = re.sub(r"\D", "", phone or "")

    if not normalized_phone:
        raise ValueError("Telefone do contato inválido.")

    return normalized_phone


def should_retry_zapi_error(exception: BaseException) -> bool:
    if isinstance(exception, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
        return True

    if isinstance(exception, requests.exceptions.HTTPError):
        status_code = exception.response.status_code if exception.response is not None else None
        return status_code == 429 or (status_code is not None and status_code >= 500)

    return False


@retry(
    retry=retry_if_exception(should_retry_zapi_error),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def send_message_with_retry(zapi: ZApiClient, phone: str, message: str) -> dict:
    return zapi.send_text(phone, message)


def send_to_contacts(contacts: list) -> SendResult:
    zapi = ZApiClient(settings.zapi_instance_id, settings.zapi_token, settings.zapi_client_token)
    result = SendResult(total=len(contacts))

    logger.info("Iniciando envio para %s contato(s).", result.total)

    for contact in contacts:
        try:
            if not contact.phone or not contact.name:
                result.failure += 1
                logger.warning("Contato %s com dados incompletos. Envio ignorado.", contact.id)
                continue

            phone = normalize_phone(contact.phone)
            message = build_message(contact.name)
            zapi_response = send_message_with_retry(zapi, phone, message)
            mark_contact_as_sent(contact.id)
            result.success += 1
            logger.info(
                "Mensagem enviada para %s (%s). Resposta Z-API: %s",
                contact.name,
                phone,
                zapi_response,
            )
        except requests.exceptions.Timeout:
            result.failure += 1
            logger.exception("Timeout ao enviar mensagem para %s (%s).", contact.name, contact.phone)
        except requests.exceptions.ConnectionError:
            result.failure += 1
            logger.exception("Erro de conexão ao enviar mensagem para %s (%s).", contact.name, contact.phone)
        except requests.exceptions.HTTPError as error:
            result.failure += 1
            status_code = error.response.status_code if error.response is not None else "sem status"
            logger.exception(
                "Erro HTTP ao enviar mensagem para %s (%s). Status: %s. Resposta: %s",
                contact.name,
                contact.phone,
                status_code,
                error,
            )
        except ValueError:
            result.failure += 1
            logger.exception("Dados inválidos para contato %s.", contact.id)
        except Exception:
            result.failure += 1
            logger.exception("Falha ao enviar mensagem para %s (%s).", contact.name, contact.phone)

    return result


def main() -> None:
    contacts = fetch_contacts()

    if not contacts:
        logger.warning("Nenhum contato pendente para enviar.")
        return

    result = send_to_contacts(contacts)

    logger.info(
        "Processo finalizado. Sucessos: %s. Falhas: %s. Total: %s. Taxa: %.2f%%.",
        result.success,
        result.failure,
        result.total,
        result.success_rate,
    )


if __name__ == "__main__":
    main()
