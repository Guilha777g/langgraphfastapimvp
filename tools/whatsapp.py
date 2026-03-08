import os
import logging
import httpx

logger = logging.getLogger(__name__)

WA_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
WA_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "")
WA_API_URL = f"https://graph.facebook.com/v21.0/{WA_PHONE_ID}/messages"


async def send_whatsapp_message(phone: str, text: str) -> bool:
    """Envia mensagem de texto via WhatsApp Business API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                WA_API_URL,
                headers={
                    "Authorization": f"Bearer {WA_TOKEN}",
                    "Content-Type": "application/json",
                },
                json={
                    "messaging_product": "whatsapp",
                    "to": phone,
                    "type": "text",
                    "text": {"body": text},
                },
                timeout=15,
            )
            response.raise_for_status()
            logger.info(f"Mensagem enviada para {phone}")
            return True
    except Exception as e:
        logger.error(f"Falha ao enviar WhatsApp para {phone}: {e}")
        return False
