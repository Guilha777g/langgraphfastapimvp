import os
import datetime
from langchain_core.tools import tool
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
SA_JSON_PATH = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "./credentials/google-sa.json")


def _get_service():
    credentials = service_account.Credentials.from_service_account_file(
        SA_JSON_PATH, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=credentials)


@tool
def check_availability(date: str) -> str:
    """Consulta horarios disponiveis na agenda para uma data especifica.

    Args:
        date: Data no formato YYYY-MM-DD (ex: 2026-03-15)
    """
    try:
        service = _get_service()
        start = f"{date}T00:00:00Z"
        end = f"{date}T23:59:59Z"

        events = (
            service.events()
            .list(
                calendarId=CALENDAR_ID,
                timeMin=start,
                timeMax=end,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        items = events.get("items", [])
        if not items:
            return f"Agenda livre o dia todo em {date}."

        busy = []
        for event in items:
            start_time = event["start"].get("dateTime", event["start"].get("date"))
            end_time = event["end"].get("dateTime", event["end"].get("date"))
            summary = event.get("summary", "Ocupado")
            busy.append(f"  - {start_time} ate {end_time}: {summary}")

        return f"Horarios ocupados em {date}:\n" + "\n".join(busy)

    except FileNotFoundError:
        return "ERRO: Credenciais do Google Calendar nao encontradas. Verifique GOOGLE_SERVICE_ACCOUNT_JSON."
    except Exception as e:
        return f"ERRO: Falha ao consultar agenda: {e}"


@tool
def book_appointment(date: str, time: str, name: str, description: str = "") -> str:
    """Cria um agendamento no Google Calendar.

    Args:
        date: Data no formato YYYY-MM-DD (ex: 2026-03-15)
        time: Horario no formato HH:MM (ex: 14:00)
        name: Nome do cliente ou titulo do agendamento
        description: Descricao ou detalhes adicionais
    """
    try:
        service = _get_service()

        start_dt = datetime.datetime.fromisoformat(f"{date}T{time}:00")
        end_dt = start_dt + datetime.timedelta(hours=1)

        event = {
            "summary": name,
            "description": description,
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": "America/Sao_Paulo",
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": "America/Sao_Paulo",
            },
        }

        created = (
            service.events()
            .insert(calendarId=CALENDAR_ID, body=event)
            .execute()
        )

        return f"Agendamento criado com sucesso! {name} em {date} as {time}. ID: {created['id']}"

    except FileNotFoundError:
        return "ERRO: Credenciais do Google Calendar nao encontradas."
    except Exception as e:
        return f"ERRO: Falha ao criar agendamento: {e}"
