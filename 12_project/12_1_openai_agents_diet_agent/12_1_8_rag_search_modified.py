import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner, trace, function_tool
import chromadb
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv()

DB_PATH = os.path.join(BASE_DIR, "data", "chroma")
client = chromadb.PersistentClient(path=DB_PATH)

calories_db = client.get_collection("nutrition_db")
qna_db = client.get_collection("nutrition_qna")


@function_tool
def calorie_lookup_tool(query: str, max_results: int = 3) -> str:
    """Look up calorie information for food items."""
    results = calories_db.query(query_texts=[query], n_results=max_results)

    if not results["documents"][0]:
        return f"No nutrition info found for: {query}"

    output = []
    for meta in results["metadatas"][0]:
        output.append(
            f"{meta['food_item'].title()} "
            f"({meta['food_category'].title()}): "
            f"{meta['calories_per_100g']} cal/100g"
        )

    return "Nutrition Info:\n" + "\n".join(output)


@function_tool
def nutrition_qna_tool(query: str, max_results: int = 3) -> str:
    """Ask nutrition questions."""
    results = qna_db.query(query_texts=[query], n_results=max_results)

    if not results["documents"][0]:
        return f"No info found for: {query}"

    return "Related answers:\n" + "\n".join(results["documents"][0])


agent = Agent(
    name="Nutrition Assistant",
    instructions=(
        "You are a nutrition assistant. "
        "Use calorie_lookup_tool for calories, "
        "nutrition_qna_tool for nutrition questions. "
        "Be concise."
    ),
    tools=[calorie_lookup_tool, nutrition_qna_tool],
)


async def main():
    with trace("Nutrition Assistant"):
        result = await Runner.run(
            agent,
            "What are the best meal choices for pregnant women and how many calories do they have?"
        )
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
