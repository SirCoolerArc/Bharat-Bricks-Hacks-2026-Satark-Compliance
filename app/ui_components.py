"""
ui_components.py — InsightX Streamlit UI Components
====================================================
Reusable UI building blocks for the InsightX chat interface.
Handles all styling, custom HTML/CSS, and component rendering.

Design direction: Dark, data-terminal aesthetic with amber/gold accents.
Feels like a Bloomberg terminal meets modern AI assistant.
Professional, dense, and trustworthy — not consumer chatbot.
"""

import streamlit as st
import pandas as pd


# ---------------------------------------------------------------------------
# THEME & GLOBAL CSS
# ---------------------------------------------------------------------------

def inject_global_css():
    """Inject all global styles into the Streamlit app."""
    st.markdown("""
    <style>
    /* ── Google Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=DM+Sans:wght@300;400;500;600&family=Bebas+Neue&display=swap');

    /* ── Root Variables ── */
    :root {
        --bg-primary:     #0a0a0f;
        --bg-secondary:   #111118;
        --bg-card:        #16161f;
        --bg-input:       #1c1c28;
        --accent-gold:    #f0a500;
        --accent-amber:   #ff8c00;
        --accent-dim:     #7a5c00;
        --text-primary:   #e8e8f0;
        --text-secondary: #8888aa;
        --text-muted:     #555570;
        --success:        #00d4aa;
        --danger:         #ff4757;
        --border:         #2a2a3a;
        --border-accent:  #f0a50040;
        --glow:           #f0a50020;
    }

    /* ── App Background ── */
    .stApp {
        background-color: var(--bg-primary);
        background-image:
            radial-gradient(ellipse 80% 50% at 50% -10%, #f0a50008 0%, transparent 60%),
            repeating-linear-gradient(0deg, transparent, transparent 40px, #ffffff03 40px, #ffffff03 41px),
            repeating-linear-gradient(90deg, transparent, transparent 40px, #ffffff02 40px, #ffffff02 41px);
        font-family: 'DM Sans', sans-serif;
        color: var(--text-primary);
    }

    /* ── Hide Streamlit chrome ── */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: var(--bg-primary); }
    ::-webkit-scrollbar-thumb { background: var(--accent-dim); border-radius: 2px; }

    /* ── Chat Input ── */
    .stChatInput {
        background: var(--bg-input) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
    }
    .stChatInput textarea {
        color: var(--text-primary) !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 15px !important;
        background: transparent !important;
    }
    .stChatInput textarea::placeholder {
        color: var(--text-muted) !important;
    }

    /* ── Chat Messages ── */
    .stChatMessage {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: transparent !important;
        border: 1px solid var(--border) !important;
        color: var(--text-secondary) !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 13px !important;
        border-radius: 20px !important;
        padding: 6px 14px !important;
        transition: all 0.2s ease !important;
        white-space: nowrap !important;
    }
    .stButton > button:hover {
        border-color: var(--accent-gold) !important;
        color: var(--accent-gold) !important;
        background: var(--glow) !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] .stMarkdown p {
        color: var(--text-secondary) !important;
        font-size: 13px !important;
    }

    /* ── Dataframe / Tables ── */
    .stDataFrame {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
    }

    /* ── Metric Cards ── */
    [data-testid="metric-container"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        padding: 12px !important;
    }
    [data-testid="metric-container"] label {
        color: var(--text-secondary) !important;
        font-size: 12px !important;
        font-family: 'Space Mono', monospace !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: var(--accent-gold) !important;
        font-family: 'Space Mono', monospace !important;
    }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        color: var(--text-secondary) !important;
        font-size: 13px !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
    }
    .streamlit-expanderContent {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
    }

    /* ── Divider ── */
    hr { border-color: var(--border) !important; }

    /* ── Select box ── */
    .stSelectbox select {
        background: var(--bg-input) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------

def render_header():
    """Render the top header bar."""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #111118 0%, #16161f 100%);
        border-bottom: 1px solid #2a2a3a;
        padding: 18px 40px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0;
    ">
        <div style="display:flex; align-items:center; gap:14px;">
            <div style="
                width: 38px; height: 38px;
                background: linear-gradient(135deg, #f0a500, #ff8c00);
                border-radius: 10px;
                display: flex; align-items: center; justify-content: center;
                font-size: 18px;
                box-shadow: 0 0 20px #f0a50030;
            ">⚡</div>
            <div>
                <div style="
                    font-family: 'Bebas Neue', sans-serif;
                    font-size: 26px;
                    letter-spacing: 3px;
                    color: #e8e8f0;
                    line-height: 1;
                ">INSIGHTX</div>
                <div style="
                    font-family: 'Space Mono', monospace;
                    font-size: 10px;
                    color: #f0a500;
                    letter-spacing: 2px;
                    margin-top: 2px;
                ">LEADERSHIP ANALYTICS · TECHFEST IIT BOMBAY</div>
            </div>
        </div>
        <div style="
            font-family: 'Space Mono', monospace;
            font-size: 11px;
            color: #555570;
            text-align: right;
        ">
            <div style="color: #00d4aa;">● LIVE</div>
            <div>250,000 TRANSACTIONS</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# WELCOME SCREEN
# ---------------------------------------------------------------------------

def render_welcome():
    """Render the welcome screen shown before any queries."""
    st.markdown("""
    <div style="
        max-width: 720px;
        margin: 60px auto 0;
        padding: 0 24px;
        text-align: center;
    ">
        <div style="
            font-family: 'Bebas Neue', sans-serif;
            font-size: 52px;
            letter-spacing: 4px;
            color: #e8e8f0;
            line-height: 1;
            margin-bottom: 12px;
        ">ASK YOUR DATA</div>
        <div style="
            font-family: 'DM Sans', sans-serif;
            font-size: 16px;
            color: #8888aa;
            font-weight: 300;
            margin-bottom: 48px;
            line-height: 1.6;
        ">
            Conversational analytics for 250,000 UPI transactions.<br>
            Ask questions in plain English. Get executive-grade insights.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Sample query chips
    st.markdown("""
    <div style="max-width: 720px; margin: 0 auto; padding: 0 24px;">
        <div style="
            font-family: 'Space Mono', monospace;
            font-size: 10px;
            color: #555570;
            letter-spacing: 2px;
            margin-bottom: 16px;
        ">TRY ASKING</div>
    </div>
    """, unsafe_allow_html=True)

    sample_questions = [
        "Which transaction type has the highest failure rate?",
        "Compare failure rates for HDFC vs SBI on weekends",
        "What are the peak transaction hours?",
        "Which age group uses P2P most on weekends?",
        "What % of high-value transactions are flagged?",
        "Is there a relationship between network type and failures?",
    ]

    cols = st.columns(2)
    for i, q in enumerate(sample_questions):
        with cols[i % 2]:
            if st.button(q, key=f"sample_{i}"):
                st.session_state.prefilled_query = q
                st.rerun()


# ---------------------------------------------------------------------------
# USER MESSAGE BUBBLE
# ---------------------------------------------------------------------------

def render_user_message(message: str):
    """Render a user message bubble."""
    st.markdown(f"""
    <div style="
        display: flex;
        justify-content: flex-end;
        margin: 20px 0 8px;
        padding: 0 40px;
    ">
        <div style="
            background: linear-gradient(135deg, #1e1e2e, #252535);
            border: 1px solid #2a2a3a;
            border-radius: 16px 16px 4px 16px;
            padding: 12px 18px;
            max-width: 70%;
            font-family: 'DM Sans', sans-serif;
            font-size: 15px;
            color: #e8e8f0;
            line-height: 1.5;
        ">{message}</div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# ASSISTANT RESPONSE
# ---------------------------------------------------------------------------

def render_assistant_response(response: str, result: dict = None):
    """
    Render the assistant's insight response with optional data table.
    """
    # Main response bubble
    # Convert newlines to <br> for HTML rendering
    formatted = response.replace("\n\n", "</p><p style='margin-top:10px'>").replace("\n", "<br>")

    st.markdown(f"""
    <div style="
        display: flex;
        justify-content: flex-start;
        margin: 8px 0;
        padding: 0 40px;
        gap: 12px;
        align-items: flex-start;
    ">
        <div style="
            width: 32px; height: 32px; flex-shrink: 0;
            background: linear-gradient(135deg, #f0a500, #ff8c00);
            border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
            font-size: 14px;
            box-shadow: 0 0 12px #f0a50025;
            margin-top: 4px;
        ">⚡</div>
        <div style="
            background: linear-gradient(135deg, #13131e, #16161f);
            border: 1px solid #2a2a3a;
            border-left: 3px solid #f0a500;
            border-radius: 4px 16px 16px 16px;
            padding: 16px 20px;
            max-width: 80%;
            font-family: 'DM Sans', sans-serif;
            font-size: 15px;
            color: #d8d8e8;
            line-height: 1.7;
        "><p style='margin:0'>{formatted}</p></div>
    </div>
    """, unsafe_allow_html=True)

    # Data table (if available)
    if result and result.get("data") is not None:
        data = result["data"]
        if isinstance(data, pd.DataFrame) and not data.empty:
            with st.expander("📊 View Data Table", expanded=False):
                st.dataframe(
                    data,
                    use_container_width=True,
                    hide_index=True,
                )


# ---------------------------------------------------------------------------
# METRICS STRIP
# ---------------------------------------------------------------------------

def render_metrics_strip(result: dict):
    """
    Render a horizontal strip of key metric cards from the result summary.
    Only shown when there are clear numerical highlights.
    """
    summary = result.get("summary", {})
    if not summary:
        return

    metrics = []

    if "highest" in summary and isinstance(summary["highest"], dict):
        h = summary["highest"]
        metrics.append((h.get("segment", "Highest"), f"{h.get('value', '')}%", "▲ Max"))

    if "lowest" in summary and isinstance(summary["lowest"], dict):
        l = summary["lowest"]
        metrics.append((l.get("segment", "Lowest"), f"{l.get('value', '')}%", "▼ Min"))

    if "spread" in summary:
        metrics.append(("Spread", f"{summary['spread']}pp", "Range"))

    if "baseline_failure_rate" in summary:
        metrics.append(("Baseline", f"{summary['baseline_failure_rate']}%", "Overall Avg"))

    if "metric_value" in summary:
        unit = summary.get("unit", "")
        val = summary["metric_value"]
        label = summary.get("metric_label", "Value")
        if isinstance(val, float):
            val = f"{val:,.2f}"
        elif isinstance(val, int):
            val = f"{val:,}"
        metrics.append((label[:20], f"{val} {unit}".strip(), ""))

    if not metrics:
        return

    st.markdown("<div style='padding: 0 40px; margin: 4px 0;'>", unsafe_allow_html=True)
    cols = st.columns(min(len(metrics), 4))
    for i, (label, value, delta) in enumerate(metrics[:4]):
        with cols[i]:
            st.metric(label=label, value=value, delta=delta if delta else None)
    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# FOLLOW-UP SUGGESTIONS
# ---------------------------------------------------------------------------

def render_followup_suggestions(suggestions: list[str]):
    """Render clickable follow-up suggestion chips."""
    if not suggestions:
        return

    st.markdown("""
    <div style="padding: 4px 40px 0; margin-top: 4px;">
        <div style="
            font-family: 'Space Mono', monospace;
            font-size: 10px;
            color: #555570;
            letter-spacing: 2px;
            margin-bottom: 8px;
        ">EXPLORE FURTHER</div>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(len(suggestions))
    for i, suggestion in enumerate(suggestions):
        with cols[i]:
            if st.button(f"→ {suggestion}", key=f"followup_{suggestion[:20]}_{i}"):
                st.session_state.prefilled_query = suggestion
                st.rerun()


# ---------------------------------------------------------------------------
# THINKING INDICATOR
# ---------------------------------------------------------------------------

def render_thinking():
    """Show an animated thinking indicator while processing."""
    st.markdown("""
    <div style="
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px 40px;
    ">
        <div style="
            width: 32px; height: 32px;
            background: linear-gradient(135deg, #f0a500, #ff8c00);
            border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
            font-size: 14px;
            animation: pulse 1.5s ease-in-out infinite;
        ">⚡</div>
        <div style="
            font-family: 'Space Mono', monospace;
            font-size: 12px;
            color: #f0a500;
            letter-spacing: 1px;
        ">ANALYSING DATA...</div>
    </div>
    <style>
    @keyframes pulse {
        0%, 100% { opacity: 1; box-shadow: 0 0 12px #f0a50025; }
        50% { opacity: 0.6; box-shadow: 0 0 25px #f0a50060; }
    }
    </style>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------

def render_sidebar(cm):
    """Render the sidebar with session info and controls."""
    with st.sidebar:
        st.markdown("""
        <div style="
            font-family: 'Bebas Neue', sans-serif;
            font-size: 20px;
            letter-spacing: 3px;
            color: #e8e8f0;
            padding: 8px 0 4px;
        ">SESSION</div>
        <div style="
            width: 32px; height: 2px;
            background: linear-gradient(90deg, #f0a500, transparent);
            margin-bottom: 16px;
        "></div>
        """, unsafe_allow_html=True)

        # Turn counter
        turns = cm.get_turn_count()
        st.markdown(f"""
        <div style="
            background: #16161f;
            border: 1px solid #2a2a3a;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 12px;
        ">
            <div style="font-family:'Space Mono',monospace; font-size:10px; color:#555570; letter-spacing:2px;">QUERIES</div>
            <div style="font-family:'Space Mono',monospace; font-size:28px; color:#f0a500; margin-top:4px;">{turns:02d}</div>
        </div>
        """, unsafe_allow_html=True)

        # Active context
        context = cm.get_context()
        active_filters = {k: v for k, v in context.get("active_filters", {}).items() if v is not None}

        if active_filters:
            st.markdown("""
            <div style="font-family:'Space Mono',monospace; font-size:10px; color:#555570; letter-spacing:2px; margin-bottom:8px;">ACTIVE CONTEXT</div>
            """, unsafe_allow_html=True)
            for k, v in active_filters.items():
                st.markdown(f"""
                <div style="
                    background: #f0a50010;
                    border: 1px solid #f0a50030;
                    border-radius: 6px;
                    padding: 6px 10px;
                    margin-bottom: 4px;
                    font-family: 'Space Mono', monospace;
                    font-size: 11px;
                    color: #f0a500;
                ">{k}: {v}</div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Reset button
        if st.button("↺  New Session", use_container_width=True):
            cm.reset()
            st.session_state.messages = []
            st.session_state.prefilled_query = None
            st.rerun()

        st.markdown("---")

        # Dataset info
        st.markdown("""
        <div style="font-family:'Space Mono',monospace; font-size:10px; color:#555570; letter-spacing:1px; line-height:2;">
        DATASET<br>
        <span style="color:#8888aa;">250,000 transactions</span><br>
        <span style="color:#8888aa;">Jan–Dec 2024</span><br>
        <span style="color:#8888aa;">10 states · 8 banks</span><br><br>
        FAILURE BASELINE<br>
        <span style="color:#f0a500;">4.95%</span><br><br>
        HIGH-VALUE (P90)<br>
        <span style="color:#f0a500;">₹3,236+</span><br><br>
        FRAUD FLAG RATE<br>
        <span style="color:#f0a500;">0.19%</span>
        </div>
        """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# ERROR MESSAGE
# ---------------------------------------------------------------------------

def render_error(message: str):
    """Render an error message in the chat."""
    st.markdown(f"""
    <div style="
        padding: 0 40px;
        margin: 8px 0;
    ">
        <div style="
            background: #ff475710;
            border: 1px solid #ff475740;
            border-radius: 8px;
            padding: 12px 16px;
            font-family: 'Space Mono', monospace;
            font-size: 13px;
            color: #ff4757;
        ">⚠ {message}</div>
    </div>
    """, unsafe_allow_html=True)