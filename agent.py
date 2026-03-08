import os
import yaml
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from tools import ALL_TOOLS

load_dotenv()

# Config
with open("config.yaml") as f:
    CONFIG = yaml.safe_load(f)

# LLM com tools
llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0.3)
llm_with_tools = llm.bind_tools(ALL_TOOLS)

# System prompt from config
_rules = "\n".join(f"- {r}" for r in CONFIG.get("rules", []))
_n8n_flows = "\n".join(
    f"- {name}: {info['description']}"
    for name, info in CONFIG.get("n8n", {}).get("flows", {}).items()
)

SYSTEM_PROMPT = f"""Voce e {CONFIG['name']}.
{CONFIG['persona']}

Regras:
{_rules}

Voce tem acesso aos seguintes fluxos n8n (use trigger_n8n para aciona-los):
{_n8n_flows}

Voce tambem pode consultar e criar agendamentos no Google Calendar.

IMPORTANTE:
- Use trigger_n8n com flow_name e data (JSON string) para buscar informacoes ou executar acoes.
- Sempre busque informacoes antes de responder sobre produtos, precos ou regras.
- Seja concisa e natural nas respostas."""


# Graph nodes
async def assistant(state: MessagesState):
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}


def route(state: MessagesState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


# Build graph
graph = StateGraph(MessagesState)
graph.add_node("assistant", assistant)
graph.add_node("tools", ToolNode(ALL_TOOLS))
graph.add_edge(START, "assistant")
graph.add_conditional_edges("assistant", route)
graph.add_edge("tools", "assistant")


async def get_agent():
    """Retorna o agente compilado com checkpointer."""
    database_url = os.getenv("DATABASE_URL")
    checkpointer = AsyncPostgresSaver.from_conn_string(database_url)
    await checkpointer.setup()
    return graph.compile(checkpointer=checkpointer)
