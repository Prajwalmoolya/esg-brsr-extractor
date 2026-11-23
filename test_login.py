import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

async def main():
    async for m in query(prompt="Say hello in 3 words",
                         options=ClaudeAgentOptions(model="haiku", tools=[])):
        if isinstance(m, ResultMessage):
            print(m.result)

asyncio.run(main())