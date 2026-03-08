import os
import yaml
import httpx
from langchain_core.tools import tool

N8N_BASE_URL = os.getenv("N8N_BASE_URL", "")

with open("config.yaml") as f:
    _config = yaml.safe_load(f)

_flows = _config.get("n8n", {}).get("flows", {})

_flow_descriptions = "\n".join(
    f"  - {name}: {info['description']}"
    for name, info in _flows.items()
)

_docstring = (
    "Dispara um fluxo n8n via webhook. Envie os dados necessarios como JSON string.\n\n"
    "Fluxos disponiveis:\n"
    f"{_flow_descriptions}\n\n"
    "Args:\n"
    "    flow_name: Nome do fluxo (ex: buscar_documentos, criar_lead, consultar_pedido)\n"
    '    data: JSON string com os dados para o fluxo (ex: \'{"query": "preco do pao"}\')'
)


@tool(description=_docstring)
def trigger_n8n(flow_name: str, data: str = "{}") -> str:
    """Dispara um fluxo n8n via webhook."""
    flow = _flows.get(flow_name)
    if not flow:
        available = ", ".join(_flows.keys())
        return f"ERRO: Fluxo '{flow_name}' nao encontrado. Disponiveis: {available}"

    url = f"{N8N_BASE_URL}{flow['path']}"

    try:
        import json
        payload = json.loads(data) if isinstance(data, str) else data
    except json.JSONDecodeError:
        payload = {"input": data}

    try:
        response = httpx.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.text
    except httpx.TimeoutException:
        return f"ERRO: Fluxo '{flow_name}' nao respondeu em 30s. Peca ao usuario tentar novamente."
    except httpx.HTTPError as e:
        return f"ERRO: Fluxo '{flow_name}' falhou: {e}"
