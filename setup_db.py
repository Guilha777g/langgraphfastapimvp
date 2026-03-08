"""
Rodar UMA VEZ para criar as tabelas do LangGraph checkpointer no Supabase.

Uso:
    python setup_db.py

Apos rodar com sucesso, pode deletar este arquivo.
"""
import asyncio
import os
from dotenv import load_dotenv
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

load_dotenv()


async def setup():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERRO: DATABASE_URL nao definida no .env")
        return

    print(f"Conectando ao Supabase...")
    checkpointer = AsyncPostgresSaver.from_conn_string(database_url)
    await checkpointer.setup()
    print("Tabelas do checkpointer criadas com sucesso!")
    print("Pode deletar este arquivo agora.")


if __name__ == "__main__":
    asyncio.run(setup())
