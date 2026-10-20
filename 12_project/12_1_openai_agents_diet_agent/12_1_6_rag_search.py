import asyncio
import chromadb
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool, trace
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv()

# -------------------------------
# Get the collection
# -------------------------------
chroma_client = chromadb.PersistentClient(
    os.path.join(BASE_DIR, "data", "chroma")
)
nutrition_db = chroma_client.get_collection(name="nutrition_db")

# Quick sanity check (optional)
results = nutrition_db.query(query_texts=["banana"], n_results=2)
for i, doc in enumerate(results["documents"][0]):
    print(sorted(results["metadatas"][0][i].items()))
    print(doc)
    print()

# -------------------------------
# Tool: Calorie Lookup
# -------------------------------
@function_tool
def calorie_lookup_tool(query: str, max_results: int = 3) -> str:
    """
    Tool function for a RAG database to look up calorie information
    for individual food items (not meals).
    """
    results = nutrition_db.query(
        query_texts=[query],
        n_results=max_results,
    )

    if not results["documents"][0]:
        return f"No nutrition information found for: {query}"

    formatted_results = []
    for i, doc in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][i]
        food_item = metadata["food_item"].title()
        calories = metadata["calories_per_100g"]
        category = metadata["food_category"].title()

        formatted_results.append(
            f"{food_item} ({category}): {calories} calories per 100g"
        )

    return "Nutrition Information:\n" + "\n".join(formatted_results)


# -------------------------------
# Agent Definition
# -------------------------------
calorie_agent = Agent(
    name="Nutrition Assistant",
    instructions="""
You are a helpful nutrition assistant giving out calorie information.
You give concise answers.
If you need calorie data, use the calorie_lookup_tool.
""",
    tools=[calorie_lookup_tool],
)


# -------------------------------
# Async Runner
# -------------------------------
async def main():
    with trace("Nutrition Assistant with RAG"):
        result = await Runner.run(
            calorie_agent,
            "How many calories are in total in a banana and an apple? "
            "Also give calories per 100g.",
        )
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
