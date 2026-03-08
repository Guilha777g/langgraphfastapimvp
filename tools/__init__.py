from tools.n8n import trigger_n8n
from tools.calendar import check_availability, book_appointment
from tools.whatsapp import send_whatsapp_message

ALL_TOOLS = [trigger_n8n, check_availability, book_appointment]
