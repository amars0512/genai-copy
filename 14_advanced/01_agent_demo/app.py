"""
Birthday Gift Hunt - Streamlit front end (local qwen3:8b via Ollama).

    streamlit run app.py

Shows the agent's behaviour live while it runs:
  * Decision timeline  - every tool the agent chose, with its stated reason
  * Current page       - what the agent just read
  * Evidence log       - every page read so far
  * Explored map       - the part of the website graph the agent has discovered
"""

import asyncio
import json

import streamlit as st

from hunt_agent import MODEL, run_hunt
from hunt_engine import HUNT, MAX_TOOL_CALLS, PAGES, HuntState

st.set_page_config(page_title="Birthday Gift Hunt", page_icon="🎁", layout="wide")


# ---------------------------------------------------------------- rendering
def build_dot(state: HuntState, full_map: bool) -> str:
    """Graphviz DOT for the pages the agent has discovered (or the whole site)."""
    shown = set(PAGES) if full_map else set(state.reachable) | set(state.visited)
    lines = ["digraph G {", 'rankdir=LR; bgcolor="transparent";',
             'node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=10];']
    for pid in shown:
        label = f"{pid}\\n{PAGES[pid]['title'][:28]}"
        if state.status == "solved" and pid in state.final_evidence:
            fill, pen = "#9be79b", 3                     # evidence for the accepted answer
        elif pid == state.current_page:
            fill, pen = "#ffd166", 3                     # where the agent is right now
        elif pid in state.visited:
            fill, pen = "#bde0fe", 1                     # read
        elif pid in state.reachable:
            fill, pen = "#eeeeee", 1                     # discovered but not read
        else:
            fill, pen = "#ffffff", 1                     # hidden (full map only)
        style = '"rounded,filled,dashed"' if pid not in state.reachable else '"rounded,filled"'
        lines.append(f'{pid} [label="{label}", fillcolor="{fill}", penwidth={pen}, style={style}];')
    for pid in shown:
        if full_map or pid in state.visited:
            for target in PAGES[pid]["links"]:
                if target in shown:
                    walked = pid in state.visited and target in state.visited
                    lines.append(f'{pid} -> {target} [color="{"#1d3557" if walked else "#aaaaaa"}"];')
    lines.append("}")
    return "\n".join(lines)


def render(state: HuntState, slots: dict, pending: str | None = None, full_map: bool = False) -> None:
    used = len(state.tool_calls)
    with slots["status"].container():
        c1, c2, c3 = st.columns(3)
        c1.metric("Tool calls used", f"{used} / {state.max_tool_calls}")
        c2.metric("Rooms / spots searched", f"{len(state.visited)} / {len(PAGES)}")
        c3.metric("Status", state.status.replace("_", " "))
        if state.status == "solved":
            st.success(f"🎁 Found it: **{state.final_answer}**. "
                       f"Evidence: {', '.join(state.final_evidence)}")
        elif state.status == "out_of_steps":
            st.error("⏱️ The agent ran out of steps without a confirmed answer.")

    with slots["timeline"].container():
        st.subheader("🧭 Decision timeline")
        if pending:
            st.info(f"🤔 Agent chose **{pending}** ...")
        for call in reversed(state.tool_calls):
            verdict = call["result"].splitlines()[0]
            icon = {"read_page": "📄", "list_links": "🔗", "submit_answer": "📝"}[call["tool"]]
            with st.container(border=True):
                st.markdown(f"**Step {call['step']}** {icon} `{call['tool']}({json.dumps(call['args'])})`")
                st.markdown(f"_Why:_ {call['reason']}")
                if call["tool"] == "submit_answer" or verdict.startswith("ERROR"):
                    (st.success if verdict.startswith("ACCEPTED") else st.warning)(verdict)

    with slots["page"].container():
        st.subheader("📍 Where the agent is now")
        if state.current_page:
            page = PAGES[state.current_page]
            with st.container(border=True):
                st.markdown(f"**{state.current_page} - {page['title']}**")
                st.write(page["content"])
                st.caption("Links: " + ", ".join(f"{p} ({PAGES[p]['title']})" for p in page["links"]))
        else:
            st.caption("Not started yet.")

        st.subheader("🔎 Rooms searched")
        for pid in state.visited:
            with st.expander(f"{pid} - {PAGES[pid]['title']}"):
                st.write(PAGES[pid]["content"])

    with slots["graph"].container():
        st.subheader("🏠 Explored house")
        st.caption("Yellow = current · blue = read · grey = discovered, not read · green = accepted evidence"
                   + (" · dashed = never discovered" if full_map else ""))
        st.graphviz_chart(build_dot(state, full_map), width="stretch")


# ---------------------------------------------------------------- page
st.title("🎁 Birthday Gift Hunt - an autonomous agent at work")

with st.sidebar:
    st.header("Mission")
    st.write(HUNT["mission"])
    st.caption(f"House: {len(PAGES)} connected rooms and hiding spots · start: {HUNT['start_page']}")
    model = st.text_input("Local Ollama model", MODEL)
    start = st.button("▶️ Start the hunt", type="primary", width="stretch")
    if st.button("🔄 Reset", width="stretch"):
        st.session_state.pop("state", None)
        st.session_state.pop("summary", None)
    full_map = st.toggle("Show the whole house (spoiler)", value=False)
    st.caption(f"Tools: read_page · list_links · submit_answer · budget {MAX_TOOL_CALLS} calls")

slots = {"status": st.empty()}
left, right = st.columns([1, 1])
with left:
    slots["timeline"] = st.empty()
with right:
    slots["page"] = st.empty()
slots["graph"] = st.empty()
summary_slot = st.empty()

if start:
    state = HuntState()
    st.session_state["state"] = state

    def on_event(event, state):
        # Redraw when the agent picks a tool (before it runs) and when the tool returns.
        if event.type != "run_item_stream_event":
            return
        if event.item.type == "tool_call_item":
            raw = event.item.raw_item
            args = json.loads(getattr(raw, "arguments", "{}") or "{}")
            args.pop("reason", None)
            render(state, slots, pending=f"{getattr(raw, 'name', 'a tool')}({json.dumps(args)})", full_map=full_map)
        elif event.item.type == "tool_call_output_item":
            render(state, slots, full_map=full_map)

    render(state, slots, full_map=full_map)
    with st.spinner("Agent is searching the house (local model, can take a minute)..."):
        try:
            st.session_state["summary"] = asyncio.run(run_hunt(state, model=model, on_event=on_event))
        except Exception as e:  # surface API/key errors in the UI instead of a stack trace
            st.session_state["summary"] = f"Run failed: {e}"

state = st.session_state.get("state", HuntState())
render(state, slots, full_map=full_map)
if st.session_state.get("summary"):
    with summary_slot.container():
        st.subheader("🧾 Agent's summary")
        st.write(st.session_state["summary"])
