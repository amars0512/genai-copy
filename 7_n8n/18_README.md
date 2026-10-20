# 18 - Product Order Support: MCP client and MCP server in one workflow

One n8n workflow, two halves:

```
 LEFT: MCP client (the agent)                        RIGHT: MCP server (the tools)
 ───────────────────────────────                     ──────────────────────────────────
 Chat trigger → AI Agent ← Ollama qwen3:8b           MCP Server Trigger  /mcp/shop-support
                   ├─ Simple Memory                   ├─ get_order_status      (MySQL)
                   └─ shop (MCP Client) ──── HTTP ───►├─ get_customer_details  (MySQL)
                                                      └─ check_refund_status   (MySQL)
```

The agent doesn't call the database directly. It discovers the tools over the MCP protocol, so the
right half could just as well run on another server.

## Files

| File | What it is |
|---|---|
| `18_product_order_MCP_RAG.json` | The workflow (9 nodes) |
| `18_shop_support_seed.sql` | Demo data: `n8n.shop_customers`, `shop_orders`, `shop_refunds` (dates relative to today) |

## Setup

1. Load the demo data (it only creates and replaces the `shop_*` tables):
   ```bash
   docker exec -i mysql sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' < 7_n8n/18_shop_support_seed.sql
   ```
2. Import the workflow. Check the credentials on the 3 MySQL nodes (**MySQL account**) and the Ollama node.
3. **Activate (publish) the workflow.** The MCP client calls the *production* URL
   `http://localhost:5678/mcp/shop-support`, which only exists while the workflow is active.
4. Click **Open chat** and ask away.

## Questions to ask

| Ask | Expected |
|---|---|
| What is the status of order ORD1024? | Delivered 12 days ago, BlueDart tracking |
| Is ORD1024 eligible for a refund? | Checks → **ELIGIBLE** |
| And what about ORD1025? | Uses memory → **NOT ELIGIBLE** (45 days) |
| Can I get a refund for ORD1028? | **NOT ELIGIBLE** (opened electronics) |
| Is ORD1031 still refundable? | **ELIGIBLE** (day 29 of 30) |
| What's happening with the refund for ORD1027? | Refund REF501 approved |
| Who is the customer for ORD1029? | Farhan Sheikh, Bengaluru, Silver |
| Where is order ORD9999? | Not found, nothing invented |
| Who won yesterday's cricket match? | Politely declined |

Open **Executions** to show the MCP round trip. Each question creates **two** executions of this
workflow: the agent's run (left half, with the `shop` tool call) and the server's run (right half,
with the MySQL query).

## Gotchas (worth showing in class)

- **Tool names get a prefix.** n8n adds the MCP Client node's name in front of each tool name. The
  client node is called `shop`, so the agent sees `shop_get_order_status` etc., and the system prompt
  uses those names. If you rename the node and don't update the prompt, the agent replies with an
  **empty message** and no error.
- **The URL path must be unique.** Only one active workflow can own `/mcp/shop-support`.
- **`qwen3:8b` settings:** thinking is turned off and replies are capped at 1,024 tokens. With thinking
  on, qwen3 occasionally loops for tens of thousands of tokens and the chat hangs.
- **Checks first, verdict last.** The prompt makes the model list the eligibility checks before the
  verdict. Asked for the verdict first, it sometimes said "Not eligible" and then listed reasons that
  proved the opposite.
- **The database does the date maths:** `days_since_delivery` is calculated in SQL. Small models are
  bad at date arithmetic.
- **Safe SQL:** the model only supplies the ID, which is passed as a query parameter (`$1`). The
  queries are fixed, read-only `SELECT`s.
