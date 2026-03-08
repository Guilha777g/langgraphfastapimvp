"""
Chat de teste no terminal.

Uso:
    python chat.py

Digite 'sair' para encerrar.
"""
import asyncio
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

load_dotenv()


async def main():
    from agent import get_agent
    agent = await get_agent()

    thread_id = "test-cli"
    print("Chat ativo. Digite 'sair' para encerrar.\n")

    while True:
        user_input = input("Voce: ")
        if user_input.strip().lower() == "sair":
            print("Ate mais!")
            break

        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=user_input)]},
            config={"configurable": {"thread_id": thread_id}},
        )

        reply = result["messages"][-1].content
        print(f"\n{result['messages'][-1].response_metadata.get('model_name', 'Agent')}: {reply}\n")


if __name__ == "__main__":
    asyncio.run(main())
