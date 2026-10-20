from fastapi import FastAPI
from openai import AsyncOpenAI
import asyncio
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
client = AsyncOpenAI()

async def ask(prompt):
    r = await client.responses.create(model="gpt-4o-mini", input=prompt)
    return r.output_text

@app.post("/analyze")
async def analyze(text: str):
    summary, keywords, sentiment = await asyncio.gather(
        ask("Summarize: " + text),
        ask("Extract five keywords: " + text),
        ask("Determine sentiment: " + text)
    )

    return {
        "summary": summary,
        "keywords": keywords,
        "sentiment": sentiment
    }