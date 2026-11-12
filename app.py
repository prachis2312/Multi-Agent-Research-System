import re
import time
from datetime import datetime

import streamlit as st

from agents import build_search_agent, build_reader_agent, writer_chain, critic_chain

# ---------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------
st.set_page_config(
    page_title="Research Assistant",
    page_icon=None,
    layout="centered",
)

# Light styling: tighter spacing, calmer typography. Nothing flashy.
st.markdown(
    """
    <style>
        .block-container { padding-top: 2.5rem; max-width: 820px; }
        h1 { font-weight: 600; letter-spacing: -0.5px; }
        .subtle { color: #6b7280; font-size: 0.95rem; margin-top: -0.6rem; }
        .step-time { color: #9ca3af; font-size: 0.8rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------
# Session state
# ---------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []      # list of finished runs
if "current" not in st.session_state:
    st.session_state.current = None    # run currently displayed


# ---------------------------------------------------------------
# Pipeline (same logic as pipeline.py, but with live UI updates)
# ---------------------------------------------------------------
def trim(text: str, limit: int) -> str:
    """Cut text to roughly `limit` characters (about 4 characters per token)."""
    text = str(text)
    return text if len(text) <= limit else text[:limit] + "\n...[truncated]"


def extract_urls(text: str) -> list[str]:
    urls = re.findall(r'https?://[^\s<>"\]\)]+', text)
    seen, clean = set(), []
    for u in urls:
        u = u.rstrip(".,;")
        if u not in seen:
            seen.add(u)
            clean.append(u)
    return clean


def run_pipeline_with_ui(topic: str) -> dict:
    state = {"topic": topic, "timings": {}}

    with st.status("Working on your topic...", expanded=True) as status:

        # Step 1: Search
        st.write("**Step 1 of 4: Searching the web**")
        t = time.time()
        try:
            search_agent = build_search_agent()
            result = search_agent.invoke({
                "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]
            })
            state["search_results"] = result["messages"][-1].content
        except Exception as e:
            status.update(label="Search failed", state="error")
            st.error(f"Search step failed: {e}")
            return None
        state["timings"]["Search"] = time.time() - t
        # Collect URLs from every message (tool outputs included), not just the final summary
        all_text = "\n".join(str(m.content) for m in result["messages"])
        state["urls"] = extract_urls(all_text)
        st.caption(f"Found {len(state['urls'])} links in {state['timings']['Search']:.1f}s")
        with st.expander("View raw search results"):
            st.markdown(state["search_results"])

        # Step 2: Read
        st.write("**Step 2 of 4: Reading the most relevant source**")
        t = time.time()
        try:
            reader_agent = build_reader_agent()
            result = reader_agent.invoke({
                "messages": [(
                    "user",
                    f"Research topic: {topic}\n\n"
                    f"Here are the URLs found during web search:\n{state['urls']}\n\n"
                    "Choose the most relevant URL for this topic "
                    "and use the scrape_url tool to retrieve its content.",
                )]
            })
            state["scraped_content"] = result["messages"][-1].content
        except Exception as e:
            status.update(label="Reading failed", state="error")
            st.error(f"Reader step failed: {e}")
            return None
        state["timings"]["Reading"] = time.time() - t
        st.caption(f"Done in {state['timings']['Reading']:.1f}s")
        with st.expander("View scraped content"):
            st.markdown(state["scraped_content"])

        # Step 3: Write
        st.write("**Step 3 of 4: Drafting the report**")
        t = time.time()
        try:
            combined = (
                f"SEARCH RESULTS: \n {state['search_results']} \n\n"
                f"DETAILED SCRAPED CONTENT: \n {state['scraped_content']}"
            )
            state["report"] = writer_chain.invoke({"topic": topic, "research": combined})
        except Exception as e:
            status.update(label="Writing failed", state="error")
            st.error(f"Writer step failed: {e}")
            return None
        state["timings"]["Writing"] = time.time() - t
        st.caption(f"Done in {state['timings']['Writing']:.1f}s")

        # Step 4: Critique
        st.write("**Step 4 of 4: Reviewing the report**")
        t = time.time()
        try:
            state["feedback"] = critic_chain.invoke({"report": state["report"]})
        except Exception as e:
            status.update(label="Review failed", state="error")
            st.error(f"Critic step failed: {e}")
            return None
        state["timings"]["Review"] = time.time() - t
        st.caption(f"Done in {state['timings']['Review']:.1f}s")

        total = sum(state["timings"].values())
        status.update(label=f"Finished in {total:.0f}s", state="complete", expanded=False)

    state["created"] = datetime.now().strftime("%d %b, %H:%M")
    return state


# ---------------------------------------------------------------
# Sidebar: history
# ---------------------------------------------------------------
with st.sidebar:
    st.subheader("Past research")
    if not st.session_state.history:
        st.caption("Nothing yet. Your finished reports will appear here.")
    for i, item in enumerate(reversed(st.session_state.history)):
        label = item["topic"] if len(item["topic"]) < 32 else item["topic"][:30] + "..."
        if st.button(label, key=f"hist_{i}", use_container_width=True, help=item["created"]):
            st.session_state.current = item
    if st.session_state.history:
        st.divider()
        if st.button("Clear history", use_container_width=True):
            st.session_state.history = []
            st.session_state.current = None
            st.rerun()

# ---------------------------------------------------------------
# Main area
# ---------------------------------------------------------------
st.title("Research Assistant")
st.markdown(
    '<p class="subtle">Enter a topic. Four agents will search, read, write and review a report, '
    "and you can see what each one did.</p>",
    unsafe_allow_html=True,
)

with st.form("topic_form", clear_on_submit=False):
    topic = st.text_input(
        "Research topic",
        placeholder="e.g. Latest developments in solid-state batteries",
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("Start research", type="primary")

if submitted:
    if not topic.strip():
        st.warning("Please enter a topic first.")
    else:
        result = run_pipeline_with_ui(topic.strip())
        if result:
            st.session_state.history.append(result)
            st.session_state.current = result

# ---------------------------------------------------------------
# Results
# ---------------------------------------------------------------
run = st.session_state.current
if run:
    st.divider()
    st.subheader(run["topic"])
    st.caption(f"Generated {run['created']}")

    tab_report, tab_review, tab_sources, tab_process = st.tabs(
        ["Report", "Reviewer feedback", "Sources", "How it was made"]
    )

    with tab_report:
        st.markdown(run["report"])
        st.download_button(
            "Download report (.md)",
            data=run["report"],
            file_name=f"{re.sub(r'[^a-zA-Z0-9]+', '_', run['topic'])[:40]}.md",
            mime="text/markdown",
        )

    with tab_review:
        st.caption("An independent agent critiqued the report above.")
        st.markdown(run["feedback"])

    with tab_sources:
        if run["urls"]:
            st.caption("Links the search agent found. The reader agent picked one to read in full.")
            for u in run["urls"]:
                st.markdown(f"- [{u}]({u})")
        else:
            st.info("No links were found in the search results.")

    with tab_process:
        st.caption("Raw output from each step, in case you want to verify something.")
        cols = st.columns(len(run["timings"]))
        for col, (name, secs) in zip(cols, run["timings"].items()):
            col.metric(name, f"{secs:.1f}s")
        with st.expander("Search agent output"):
            st.markdown(run["search_results"])
        with st.expander("Reader agent output"):
            st.markdown(run["scraped_content"])