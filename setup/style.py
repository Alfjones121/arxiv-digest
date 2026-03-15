import streamlit as st

from brand import PINE, CARD_BORDER, WARM_GREY


def inject_css() -> None:
    st.markdown(
        f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=IBM+Plex+Sans:wght@300;400;600&family=DM+Mono:wght@400&display=swap');

    h1, h2, h3 {{ font-family: 'DM Serif Display', Georgia, serif !important; }}
    .stMarkdown p, .stMarkdown li {{ font-family: 'IBM Plex Sans', sans-serif; }}
    code, .stCode {{ font-family: 'DM Mono', monospace !important; }}

    /* Brand card styling */
    .brand-card {{
        background: white;
        border: 1px solid {CARD_BORDER};
        border-radius: 6px;
        padding: 24px;
        margin: 12px 0;
    }}
    .brand-label {{
        font-family: 'DM Mono', monospace;
        font-size: 10px;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: {WARM_GREY};
    }}
    .step-number {{
        display: inline-block;
        background: {PINE};
        color: white;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        text-align: center;
        line-height: 28px;
        font-family: 'DM Mono', monospace;
        font-size: 14px;
        margin-right: 8px;
    }}
</style>
""",
        unsafe_allow_html=True,
    )
