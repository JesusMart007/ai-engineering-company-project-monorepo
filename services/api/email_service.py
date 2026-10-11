"""Transactional email through Resend. The API key comes from RESEND_API_KEY (.env), never from code.

Sending never raises on a Resend failure: callers run it in the background after
answering the request, so the failure is logged and the user-facing response stays
the same. Logs name the email by subject and the error by Resend type and code;
they never include the recipient, the link or the API key.
"""

from __future__ import annotations

import html
import logging

import resend
from resend.exceptions import ResendError

from config import EMAIL_FROM, RESEND_API_KEY

logger = logging.getLogger(__name__)

# The SDK's default is 30 s; a reset email that has not gone out in 10 s is logged as failed.
RESEND_TIMEOUT_SECONDS = 10
resend.default_http_client = resend.RequestsClient(timeout=RESEND_TIMEOUT_SECONDS)

BRAND = "Nexova Backoffice"


def _send(to: str, subject: str, html_body: str, text_body: str) -> bool:
    if not RESEND_API_KEY:
        logger.error("RESEND_API_KEY is not set; email %r was not sent", subject)
        return False
    resend.api_key = RESEND_API_KEY
    try:
        resend.Emails.send({"from": EMAIL_FROM, "to": [to], "subject": subject, "html": html_body, "text": text_body})
    except ResendError as error:
        # Rejected by Resend (invalid key, validation, rate limit...) or the request itself
        # failed (network, timeout: error_type "HttpClientError").
        logger.error("Resend could not send email %r: %s (code %s)", subject, error.error_type, error.code)
        return False
    except ValueError:
        logger.error("Resend SDK rejected the parameters of email %r", subject)
        return False
    return True


def password_reset_email(link: str, minutes: int) -> tuple[str, str, str]:
    """Subject, HTML and plain-text bodies of the reset email (one column, inline styles, big button)."""
    subject = f"Restablece tu contraseña de {BRAND}"
    safe_link = html.escape(link, quote=True)
    html_body = f"""<!doctype html>
<html lang="es">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{subject}</title></head>
<body style="margin:0;padding:0;background:#f5f7fb;font-family:Arial,Helvetica,sans-serif;color:#172033;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f5f7fb;">
    <tr><td align="center" style="padding:24px 12px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;background:#ffffff;border:1px solid #dce2ed;border-radius:12px;">
        <tr><td style="padding:20px 24px;background:#172033;border-radius:12px 12px 0 0;color:#ffffff;font-size:16px;font-weight:bold;">{BRAND}</td></tr>
        <tr><td style="padding:24px;font-size:16px;line-height:1.5;">
          <h1 style="margin:0 0 16px;font-size:22px;line-height:1.3;">Restablece tu contraseña</h1>
          <p style="margin:0 0 16px;">Hemos recibido una solicitud para cambiar la contraseña de tu cuenta. Pulsa el botón para elegir una nueva:</p>
          <p style="margin:0 0 24px;text-align:center;">
            <a href="{safe_link}" style="display:block;background:#2457d6;color:#ffffff;text-decoration:none;font-weight:bold;font-size:18px;padding:16px 24px;border-radius:8px;">Restablecer contraseña</a>
          </p>
          <p style="margin:0 0 16px;"><strong>El enlace caduca en {minutes} minutos</strong> y solo puede usarse una vez.</p>
          <p style="margin:0 0 8px;">Si el botón no funciona, copia y pega esta dirección en tu navegador:</p>
          <p style="margin:0 0 24px;word-break:break-all;font-size:14px;"><a href="{safe_link}" style="color:#2457d6;">{safe_link}</a></p>
          <p style="margin:0;color:#5b6780;font-size:14px;">Si no has pedido este cambio, ignora este correo: tu contraseña seguirá siendo la misma.</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
    text_body = (
        f"{BRAND}\n\n"
        "Restablece tu contraseña\n\n"
        "Hemos recibido una solicitud para cambiar la contraseña de tu cuenta. "
        "Abre este enlace para elegir una nueva:\n\n"
        f"{link}\n\n"
        f"El enlace caduca en {minutes} minutos y solo puede usarse una vez.\n\n"
        "Si no has pedido este cambio, ignora este correo: tu contraseña seguirá siendo la misma.\n"
    )
    return subject, html_body, text_body


def send_password_reset_email(to: str, link: str, minutes: int) -> bool:
    subject, html_body, text_body = password_reset_email(link, minutes)
    return _send(to, subject, html_body, text_body)
