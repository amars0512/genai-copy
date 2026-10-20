# 16 - Mock Temperature: the simplest MCP client + server

The smallest possible MCP demo: one workflow and six nodes. The "server" is just a local JavaScript
function that returns a made-up temperature. No API, no key, no database.

```
 LEFT: MCP client (the agent)                    RIGHT: MCP server (the tool)
 ───────────────────────────────                 ─────────────────────────────────
 Chat trigger → AI Agent ← Ollama qwen3:8b       MCP Server Trigger  /mcp/weather-mcp
                   └─ mcp (MCP Client) ── HTTP ─► └─ get_temperature  (Code tool, mock data)
```

File: `16_mock_temperature_MCP.json`

## Setup

1. Import the workflow and check the **Ollama Chat Model** credential.
2. **Activate (publish)** it. The MCP client calls the production URL
   `http://localhost:5678/mcp/weather-mcp`, which only exists while the workflow is active.
3. Click **Open chat**.

## Try

| Ask | Answer |
|---|---|
| How hot is it in Mumbai? | 31°C (fixed mock value) |
| Temperature in Reykjavik? | 11°C (a made-up value, the same every time for that city) |
| What's the weather like? | "Which city?" (no tool call) |
| Tell me a joke | Declines: it only does temperatures |

Open **Executions** to show the MCP round trip: each temperature question creates two runs of this
workflow. The agent's run shows the `mcp` tool call, and the server's run shows `get_temperature`
returning `{"city": "Mumbai", "temperature_c": 31, "source": "mock data (not real weather)"}`.

## The tool

`get_temperature` is a **Code tool** with an input schema of `{ city: string }`:

- known cities (Mumbai 31, Delhi 27, Pune 26, Bengaluru 24, Chennai 32, London 12, New York 15,
  Tokyo 18) return a fixed value
- any other city gets a value from 5–34°C computed from its name, so it's the same on every run

**Next steps in class:**
- **17:** swap the mock function for a real API (NewsAPI).
- **18:** several tools over a real database.

## Notes

- n8n adds the MCP Client node's name in front of each tool name: node `mcp` + tool `get_temperature` gives
  `mcp_get_temperature`, the name in the system prompt. Rename the node without updating the
  prompt and the agent returns an empty reply.
- `qwen3:8b` runs with thinking off and a 512-token cap, so it can't loop and hang the chat.
