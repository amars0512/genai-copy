# 17 - News Assistant: MCP client and MCP server in one workflow

Workflow 16 with a real API instead of a mock function: one n8n workflow, two halves. Ask for news in
the chat. The agent calls the MCP server, and the server calls NewsAPI.

```
 LEFT: MCP client (the agent)                       RIGHT: MCP server (the tool)
 ───────────────────────────────                    ──────────────────────────────────
 Chat trigger → AI Agent ← Ollama qwen3:8b          MCP Server Trigger  /mcp/news-mcp
                   ├─ Simple Memory                  └─ get_latest_news  (HTTP Request → newsapi.org)
                   └─ mcp (MCP Client) ─── HTTP ───►
```

File: `17_news_MCP_client_server.json` (7 nodes). The bigger version with a database and several tools
is workflow 18.

## Setup

1. **NewsAPI key:** get a free key at newsapi.org (this repo's `.env` has it as `NEWS_API_KEY`).
2. **Import** the workflow, open the **get_latest_news** node, and create a credential:
   *Header Auth*, name `X-Api-Key`, value = your key. The key lives in n8n's encrypted credential
   store, never in the workflow JSON.
3. Check the **Ollama Chat Model** credential, then **activate (publish)** the workflow. The MCP client
   calls the production URL `http://localhost:5678/mcp/news-mcp`, which only exists while the
   workflow is active.
4. Click **Open chat**.

## Try

| Ask | What happens |
|---|---|
| What is the latest news on electric cars? | Tool call → 5 recent headlines with source and date |
| Any news about India cricket? | Tool call with topic "India cricket" |
| And what about OpenAI? | Memory keeps the context; new tool call |
| What is 2+2? | No tool call; "Sorry, I can only help with news." |

In **Executions**, each question shows **two** runs of this workflow: the agent's run (left half, the
`mcp` tool call) and the server's run (right half, the NewsAPI request). That's the MCP round trip.

## Notes

- **Tool names get a prefix.** n8n adds the MCP Client node's name: node `mcp` + tool `get_latest_news`
  gives `mcp_get_latest_news`, the name used in the system prompt. Rename the node without updating
  the prompt and the agent returns an empty reply.
- **Trimmed response.** The HTTP tool sends the model only the title, description, source, date and URL
  of each article (*Optimize Response*), not the whole NewsAPI payload.
- **Relevant results.** `searchIn=title` matches the topic in headlines only. Without it, NewsAPI
  also matches words buried in article text, and "electric cars" returned stock-market stories.
- **qwen3 settings.** Thinking is turned off and replies are capped at 1,024 tokens, so qwen3 can't loop and hang the chat.
- **Speed depends on the GPU.** The NewsAPI call takes ~0.4 s, and almost all the time is the model
  writing the answer. On a laptop running on **battery**, the GPU throttles (~7 tokens/s → ~50 s per
  answer); plugged in it's ~40 tokens/s → ~10 s.
- NewsAPI's free plan is for development: 100 requests/day, and the newest articles may be a few hours old.
