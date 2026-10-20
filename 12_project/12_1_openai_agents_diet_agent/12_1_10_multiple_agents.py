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
        params={"url": f"https://mcp.exa.ai/mcp?exaApiKey={os.environ.get('EXA_API_KEY')}", "timeout": 30},
        client_session_timeout_seconds=30,
        cache_tools_list=True,
        max_retry_attempts=1,
    )
    
    try:
        await exa.connect()
        print("[MCP] Exa Search connected\n")
        
        # Create calorie agent with search
        calorie_agent_with_search = Agent(
            name="Nutrition Assistant",
            instructions="Use calorie_lookup_tool for foods. If missing ingredients, use Exa to find recipes, then lookup each ingredient. List ingredients with calories per 100g and totals. Max 10 lookups.",
            tools=[calorie_lookup_tool],
            mcp_servers=[exa],
        )
        
        # Create breakfast planner agent
        healthy_breakfast_planner_agent = Agent(
            name="Breakfast Planner Assistant",
            instructions="""
            * You are a helpful assistant that helps with healthy breakfast choices.
            * You give concise answers.
            Given the user's preferences prompt, come up with different breakfast meals that are healthy and fit for a busy person.
            * Explicitly mention the meal's names in your response along with a sentence of why this is a healthy choice.
            """,
        )
        
        # Convert agents to tools
        calorie_calculator_tool = calorie_agent_with_search.as_tool(
            tool_name="calorie-calculator",
            tool_description="Use this tool to calculate the calories of a meal and it's ingredients",
        )
        
        breakfast_planner_tool = healthy_breakfast_planner_agent.as_tool(
            tool_name="breakfast-planner",
            tool_description="Use this tool to plan a a number of healthy breakfast options",
        )
        
        # Create price checker agent
        breakfast_price_checker_agent = Agent(
            name="Breakfast Price Checker Assistant",
            instructions="""
            * You are a helpful assistant that takes multiple breakfast items (with ingredients and calories) and checks for the price of the ingredients.
            * Use the web search tool to get an approximate price for the ingredients.
            * In your final output prove the meal name, ingredients with calories and price for each meal.
            * Use markdown and be as concise as possible.
            """,
            mcp_servers=[exa],
        )
        
        # Create main breakfast advisor agent
        breakfast_advisor = Agent(
            name="Breakfast Advisor",
            instructions="""
            * You are a breakfast advisor. You come up with meal plans for the user based on their preferences.
            * You also calculate the calories for the meal and its ingredients.
            * Based on the breakfast meals and the calories that you get from upstream agents,
            * Create a meal plan for the user. For each meal, give a name, the ingredients, and the calories

            Follow this workflow carefully:
            1) Use the breakfast_planner_tool to plan a a number of healthy breakfast options.
            2) Use the calorie_calculator_tool to calculate the calories for the meal and its ingredients.
            3) Handoff the breakfast meals and the calories to the Use the Breakfast Price Checker Assistant to add the prices in the last step.
            """,
            tools=[breakfast_planner_tool, calorie_calculator_tool],
            handoff_description="""
            Create a concise breakfast recommendation based on the user's preferences. Use Markdown format.
            """,
            handoffs=[breakfast_price_checker_agent],
        )
        
        # Run simple queries
        with trace("Simple Foods"):
            print("\n=== Query 1: Simple Foods ===")
            result = await Runner.run(calorie_agent_with_search, "How many calories in a banana and apple? Give per 100g and total.")
            print(result.final_output)
        
        with trace("Meal"):
            print("\n=== Query 2: Meal ===")
            result = await Runner.run(calorie_agent_with_search, "How many calories in an English breakfast?")
            print(result.final_output)
        
        # Run multi-agent breakfast advisor
        with trace("Multi Agent: Breakfast Advisor"):
            print("\n=== Query 3: Multi-Agent Breakfast Advisor ===")
            result = await Runner.run(
                breakfast_advisor,
                "I'm a busy person and I want to eat healthy breakfasts. I like to eat oatmeal and eggs. What is a healthy breakfast for me? Give me two options.",
            )
            print(result.final_output)
    
    finally:
        await exa.cleanup()


if __name__ == "__main__":
    asyncio.run(main())