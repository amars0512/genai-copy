import os
import asyncio
import chromadb
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool, trace
from agents.mcp import MCPServerStreamableHttp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv()

# ChromaDB setup
client = chromadb.PersistentClient(os.path.join(BASE_DIR, "data", "chroma"))
calories_db = client.get_collection("nutrition_db")


@function_tool
def calorie_lookup_tool(query: str, max_results: int = 3) -> str:
    """Look up calorie information for food items."""
    print(f"[LOCAL DB] Looking up: {query}")
    results = calories_db.query(query_texts=[query], n_results=max_results)
    
    if not results["documents"][0]:
        return f"No info found: {query}"
    
    return "Nutrition Info:\n" + "\n".join(
        f"{m['food_item'].title()} ({m['food_category'].title()}): {m['calories_per_100g']} cal/100g"
        for m in results["metadatas"][0]
    )


class LoggingMCPServer(MCPServerStreamableHttp):
    """MCP server wrapper that logs all tool calls."""
    
    async def call_tool(self, name: str, arguments: dict):
        if 'web_search_exa' in name or 'exa' in name.lower():
            print(f"\n[EXA SEARCH CALLED] Tool: {name}")
            print(f"   Arguments: {arguments}\n")
        return await super().call_tool(name, arguments)


async def main():
    # Setup MCP with logging
    exa = LoggingMCPServer(
        name="Exa Search",
        # Go to https://exa.ai/ and get an API key
        params={"url": f"https://mcp.exa.ai/mcp?exaApiKey={os.environ.get('EXA_API_KEY')}", "timeout": 30},
        client_session_timeout_seconds=30,
        cache_tools_list=True,
        max_retry_attempts=1,
    )
    
    try:
        await exa.connect()
        print("[MCP] Exa Search connected\n")
        
        # Create agent
        agent = Agent(
            name="Nutrition Assistant",
            instructions="Use calorie_lookup_tool for foods. If missing ingredients, use Exa to find recipes, then lookup each ingredient. List ingredients with calories per 100g and totals. Max 10 lookups.",
            tools=[calorie_lookup_tool],
            mcp_servers=[exa],
        )
        
        # Run queries
        with trace("Simple Foods"):
            print("\n=== Query 1: Simple Foods ===")
            result = await Runner.run(agent, "How many calories in a banana and apple? Give per 100g and total.")
            print(result.final_output)
        
        with trace("Meal"):
            print("\n=== Query 2: Meal ===")
            result = await Runner.run(agent, "How many calories in an English breakfast?")
            print(result.final_output)
    
    finally:
        await exa.cleanup()


if __name__ == "__main__":
    asyncio.run(main())