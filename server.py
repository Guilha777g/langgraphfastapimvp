import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from langchain_core.messages import HumanMessage
from tools.whatsapp import send_whatsapp_message

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Agent instance (initialized on startup)
agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa o agente com checkpointer na startup."""
    global agent
    from agent import get_agent
    agent = await get_agent()
    logger.info("Agent inicializado com sucesso")
    yield


app = FastAPI(title="Agent MVP", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "agent_ready": agent is not None}


@app.post("/chat")
async def chat(request: Request):
    """Endpoint REST generico. Body: {"message": "...", "thread_id": "..."}"""
    body = await request.json()
    message = body.get("message", "")
    thread_id = body.get("thread_id", "default")

    if not message:
        return {"error": "message is required"}

    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=message)]},
        config={"configurable": {"thread_id": thread_id}},
    )

    reply = result["messages"][-1].content
    logger.info(f"[{thread_id}] User: {message[:50]}... | Agent: {reply[:50]}...")
    return {"reply": reply, "thread_id": thread_id}


@app.get("/webhook")
async def webhook_verify(request: Request):
    """Verificacao do webhook pelo Meta."""
    params = request.query_params
    verify_token = os.getenv("VERIFY_TOKEN", "")

    if params.get("hub.verify_token") == verify_token:
        return int(params["hub.challenge"])
    return {"error": "token invalido"}


@app.post("/webhook")
async def webhook_receive(request: Request):
    """Recebe mensagens do WhatsApp."""
    body = await request.json()

    try:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": "no_message"}

        msg = messages[0]
        phone = msg["from"]
        text = msg.get("text", {}).get("body", "")

        if not text:
            return {"status": "ignored", "reason": "no text"}

        logger.info(f"WhatsApp de {phone}: {text[:80]}")

        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=text)]},
            config={"configurable": {"thread_id": phone}},
        )

        reply = result["messages"][-1].content
        await send_whatsapp_message(phone, reply)

        logger.info(f"Resposta para {phone}: {reply[:80]}")
        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Erro ao processar webhook: {e}")
        return {"status": "error", "detail": str(e)}
