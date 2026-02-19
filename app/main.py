"""
main.py — InsightX Streamlit Application
=========================================
Entry point for the InsightX conversational analytics system.

Run from project root:
    streamlit run app/main.py

Architecture:
    User Input
        → query_parser.parse_query()       [NL → structured intent]
        → analytics_engine.run_query()     [intent → computed results]
        → insight_generator.generate_insight() [results → narrative]
        → conversation_manager.add_turn()  [update state]
        → ui_components.*                  [render to screen]
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st

# ── Page config — must be first Streamlit call ──
st.set_page_config(
    page_title="InsightX — Leadership Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.query_parser import parse_query
from src.analytics_engine import run_query
from src.insight_generator import generate_insight, suggest_followups
from src.conversation_manager import ConversationManager
from app.ui_components import (
    inject_global_css,
    render_header,
    render_welcome,
    render_user_message,
    render_assistant_response,
    render_metrics_strip,
    render_followup_suggestions,
    render_thinking,
    render_sidebar,
    render_error,
)


# ---------------------------------------------------------------------------
# SESSION STATE INITIALISATION
# ---------------------------------------------------------------------------

def init_session():
    """Initialise all session state variables on first load."""
    if "cm" not in st.session_state:
        st.session_state.cm = ConversationManager()
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # messages format: list of dicts with keys:
        # role: "user" | "assistant"
        # content: str
        # result: dict (analytics result, assistant only)
        # followups: list[str] (assistant only)
    if "prefilled_query" not in st.session_state:
        st.session_state.prefilled_query = None


# ---------------------------------------------------------------------------
# CORE PROCESSING PIPELINE
# ---------------------------------------------------------------------------

def process_query(user_input: str) -> tuple[str, dict, list[str]]:
    """
    Run the full pipeline for a user query.

    Returns
    -------
    tuple of (insight_response, analytics_result, followup_suggestions)
    """
    cm = st.session_state.cm

    # Step 1: Parse the natural language query
    context = cm.get_context()
    parsed = parse_query(user_input, conversation_context=context)

    # Step 2: Run analytics computation
    result = run_query(parsed)

    # Step 3: Generate narrative insight
    response = generate_insight(result)

    # Step 4: Generate follow-up suggestions
    followups = suggest_followups(result)

    # Step 5: Update conversation state
    cm.add_turn(user_input, parsed, result, response)

    return response, result, followups


# ---------------------------------------------------------------------------
# RENDER CONVERSATION HISTORY
# ---------------------------------------------------------------------------

def render_history():
    """Render all previous messages in the conversation."""
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            render_user_message(msg["content"])
        else:
            render_assistant_response(
                msg["content"],
                result=msg.get("result"),
            )
            # Show metrics strip for assistant messages
            if msg.get("result") and msg["result"].get("success"):
                render_metrics_strip(msg["result"])
            # Show follow-ups only for the last assistant message
            if msg == st.session_state.messages[-1] and msg.get("followups"):
                render_followup_suggestions(msg["followups"])


# ---------------------------------------------------------------------------
# MAIN APP
# ---------------------------------------------------------------------------

def main():
    init_session()

    # ── Global styles ──
    inject_global_css()

    # ── Header ──
    render_header()

    # ── Sidebar ──
    render_sidebar(st.session_state.cm)

    # ── Main content area ──
    st.markdown("""
    <div style="
        max-width: 900px;
        margin: 0 auto;
        padding: 24px 0 120px;
        min-height: 80vh;
    ">
    """, unsafe_allow_html=True)

    # Show welcome screen or conversation history
    if not st.session_state.messages:
        render_welcome()
    else:
        render_history()

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Chat Input ──
    # Handle prefilled queries from sample chips and follow-up buttons
    prefilled = st.session_state.get("prefilled_query")
    if prefilled:
        st.session_state.prefilled_query = None
        user_input = prefilled
    else:
        user_input = None

    # Streamlit chat input
    chat_input = st.chat_input(
        placeholder="Ask anything about the transaction data...",
        key="chat_input",
    )

    # Determine final input (chat box takes precedence over prefilled)
    final_input = chat_input or user_input

    if final_input and final_input.strip():
        query = final_input.strip()

        # Add user message to history immediately
        st.session_state.messages.append({
            "role": "user",
            "content": query,
        })

        # Show thinking indicator while processing
        with st.spinner(""):
            render_thinking()
            try:
                response, result, followups = process_query(query)

                # Add assistant response to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "result": result,
                    "followups": followups,
                })

            except Exception as e:
                error_msg = f"Something went wrong: {str(e)}"
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "result": None,
                    "followups": [],
                })

        st.rerun()


if __name__ == "__main__":
    main()