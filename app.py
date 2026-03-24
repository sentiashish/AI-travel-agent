import json
from datetime import date
from typing import Dict, List, Tuple

import streamlit as st

from travel_agent import execute_query


SECTION_ORDER = [
    "Trip Snapshot",
    "Day-by-Day Itinerary",
    "Budget Breakdown",
    "Stay and Transport Options",
    "Food and Local Experiences",
    "Safety and Practical Tips",
    "Quick Booking Checklist",
]

SECTION_META: Dict[str, Tuple[str, str]] = {
    "Trip Snapshot": ("TRIP SNAPSHOT", "section-hero"),
    "Day-by-Day Itinerary": ("DAY-WISE ITINERARY", "section-default"),
    "Budget Breakdown": ("BUDGET BREAKDOWN", "section-budget"),
    "Stay and Transport Options": ("STAY AND TRANSPORT", "section-default"),
    "Food and Local Experiences": ("FOOD AND LOCAL EXPERIENCES", "section-default"),
    "Safety and Practical Tips": ("SAFETY AND PRACTICAL TIPS", "section-default"),
    "Quick Booking Checklist": ("BOOKING CHECKLIST", "section-checklist"),
}


def split_markdown_sections(text: str) -> List[Tuple[str, str]]:
    """Split markdown by level-2 headings and preserve body content."""
    sections: List[Tuple[str, str]] = []
    current_title = "Travel Plan"
    current_lines: List[str] = []

    for line in text.splitlines():
        if line.startswith("## "):
            if current_lines:
                sections.append((current_title, "\n".join(current_lines).strip()))
                current_lines = []
            current_title = line.replace("## ", "").strip()
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_title, "\n".join(current_lines).strip()))

    return sections


def ordered_sections(sections: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """Return sections in preferred display order, then append unknown sections."""
    by_name = {name: body for name, body in sections}
    out: List[Tuple[str, str]] = []

    for name in SECTION_ORDER:
        if name in by_name and by_name[name].strip():
            out.append((name, by_name.pop(name)))

    for name, body in by_name.items():
        if body.strip():
            out.append((name, body))
    return out


st.set_page_config(
    page_title="Atlas Travel Planner",
    page_icon="AT",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Manrope:wght@400;600;700&display=swap');

    :root {
        --bg: #eaf7fb;
        --surface: #f8fdff;
        --ink: #0f1f2e;
        --muted: #35556a;
        --brand: #0f9bb3;
        --brand-deep: #0a6f9b;
        --accent: #35c4da;
        --border: #b7deea;
        --sidebar-bg: #d7f2fa;
        --sidebar-ink: #0d2738;
    }

    .stApp {
        background:
            radial-gradient(circle at 12% 0%, #c9f2ff 0%, transparent 42%),
            radial-gradient(circle at 88% 0%, #b7ebff 0%, transparent 45%),
            linear-gradient(180deg, #f1fbff 0%, #e5f5fb 55%, #f6fcff 100%),
            var(--bg);
        color: var(--ink);
        font-family: 'Manrope', sans-serif;
    }

    /* Remove Streamlit's default dark top bar for a cleaner app canvas. */
    [data-testid="stHeader"] {
        background: transparent !important;
        box-shadow: none !important;
        border: 0 !important;
    }

    [data-testid="stDecoration"] {
        display: none !important;
    }

    [data-testid="stToolbar"],
    [data-testid="stAppDeployButton"],
    [data-testid="stStatusWidget"] {
        display: none !important;
    }

    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif;
        color: var(--ink);
        letter-spacing: -0.01em;
    }

    .hero {
        background: linear-gradient(120deg, #f8fdff 0%, #e7f8ff 44%, #dbf3ff 100%);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 1.1rem 1.1rem 1.2rem 1.1rem;
        box-shadow: 0 10px 24px rgba(15, 77, 107, 0.10);
        margin-bottom: 1rem;
    }

    .hero-title {
        font-size: 2rem;
        font-weight: 700;
        margin: 0 0 0.2rem 0;
    }

    .hero-sub {
        color: var(--muted);
        margin: 0;
    }

    .kpi {
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 0.6rem 0.75rem;
        background: linear-gradient(145deg, #fafdff 0%, #ecf8fd 100%);
    }

    .kpi-label {
        color: var(--muted);
        font-size: 0.82rem;
        margin-bottom: 0.15rem;
    }

    .kpi-value {
        font-size: 1rem;
        font-weight: 700;
        color: var(--ink);
    }

    .plan-card {
        border: 1px solid var(--border);
        border-radius: 16px;
        background: var(--surface);
        padding: 1rem;
        box-shadow: 0 8px 20px rgba(14, 91, 126, 0.08);
        margin-bottom: 0.8rem;
    }

    .section-tag {
        margin: 0 0 0.45rem 0;
        display: inline-block;
        font-size: 0.74rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        color: #17536d;
        padding: 0.2rem 0.55rem;
        border-radius: 999px;
        border: 1px solid #96d8ea;
        background: #ecf9ff;
    }

    .section-hero {
        background: linear-gradient(120deg, #ebfbff 0%, #dcf5ff 100%);
        border-color: #98d9eb;
    }

    .section-budget {
        background: linear-gradient(120deg, #eefbff 0%, #d6f2fb 100%);
        border-color: #8fd2e5;
    }

    .section-checklist {
        background: linear-gradient(120deg, #f0fbff 0%, #e2f7ff 100%);
        border-color: #9ad9eb;
    }

    .stButton button {
        border-radius: 999px;
        border: 1px solid #0a6085;
        background: linear-gradient(135deg, var(--brand) 0%, var(--brand-deep) 100%);
        color: #ffffff;
        font-weight: 700;
        letter-spacing: 0.01em;
        padding: 0.6rem 1.2rem;
        box-shadow: 0 8px 18px rgba(15, 119, 156, 0.24);
    }

    .stDownloadButton button {
        border-radius: 999px;
        border: 1px solid #0d7f99;
        background: linear-gradient(135deg, #2db7cf 0%, #1384b4 100%);
        color: #ffffff;
        font-weight: 700;
    }

    [data-testid="stAlert"] {
        border-radius: 12px !important;
        border: 1px solid #9fcfe0 !important;
    }

    [data-testid="stAlert"] p,
    [data-testid="stAlert"] div,
    [data-testid="stAlert"] span {
        color: #12354b !important;
        font-weight: 600;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #dcf4fb 0%, #cef0fa 55%, #e5f7fc 100%);
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] * {
        color: var(--sidebar-ink) !important;
    }

    [data-testid="stSidebar"] .stTextInput input,
    [data-testid="stSidebar"] .stNumberInput input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] .stDateInput input,
    [data-testid="stSidebar"] [data-baseweb="input"] input,
    [data-testid="stSidebar"] [data-baseweb="select"] > div,
    [data-testid="stSidebar"] [data-baseweb="select"] div[role="button"] {
        background: #f7fcff !important;
        color: var(--sidebar-ink) !important;
        border: 1px solid #8dd0e3 !important;
    }

    [data-testid="stSidebar"] [data-baseweb="input"] {
        background: #f7fcff !important;
        border-radius: 10px !important;
        border: 1px solid #8dd0e3 !important;
    }

    [data-testid="stSidebar"] [data-baseweb="input"] button,
    [data-testid="stSidebar"] [data-baseweb="input"] svg,
    [data-testid="stSidebar"] [data-baseweb="select"] svg {
        color: #0f6e93 !important;
        fill: #0f6e93 !important;
        background: transparent !important;
    }

    [data-testid="stSidebar"] .stNumberInput button {
        background: #eef9ff !important;
        border: 1px solid #8dd0e3 !important;
    }

    [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] div {
        color: var(--brand-deep) !important;
    }

    [data-testid="stSidebar"] .stSlider [role="slider"] {
        background: var(--brand) !important;
    }

    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stCaption {
        color: #17384f !important;
        font-weight: 600;
    }

    @media (max-width: 768px) {
        .hero-title {
            font-size: 1.5rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <p class="hero-title">Atlas AI Travel Planner</p>
      <p class="hero-sub">Build polished, day-wise travel plans with budget clarity and local recommendations.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Trip Inputs")

    destination = st.text_input("Destination", value="Goa, India")
    days = st.slider("Trip duration (days)", min_value=1, max_value=14, value=5)
    travelers = st.number_input("Travelers", min_value=1, max_value=20, value=3, step=1)
    budget = st.number_input("Total budget (INR)", min_value=1000, value=50000, step=1000)

    col_date_1, col_date_2 = st.columns(2)
    with col_date_1:
        start_date = st.date_input("Start", value=date.today())
    with col_date_2:
        end_date = st.date_input("End", value=date.today())

    interests = st.text_area(
        "Interests",
        value="beaches, water sports, nightlife, local cuisine, historical sites, photography",
        height=90,
    )

    style = st.selectbox(
        "Travel style",
        ["moderate", "budget", "premium"],
        index=0,
    )

    show_steps = st.toggle("Show tool steps", value=False)
    disable_polish = st.toggle("Disable premium polish", value=False)

    st.caption("Note: OPENROUTER_API_KEY must be set in .env or environment.")


query = (
    f"Plan a {days}-day trip to {destination} for {travelers} travelers. "
    f"Total budget is INR {int(budget)} ({style}). "
    f"Interests: {interests}. "
    f"Travel window: from {start_date.isoformat()} to {end_date.isoformat()}. "
    "Provide a day-by-day itinerary, budget split, food recommendations, "
    "local transport guidance, and safety tips."
)

kpi_cols = st.columns(4)
with kpi_cols[0]:
    st.markdown(
        f"<div class='kpi'><div class='kpi-label'>Destination</div><div class='kpi-value'>{destination}</div></div>",
        unsafe_allow_html=True,
    )
with kpi_cols[1]:
    st.markdown(
        f"<div class='kpi'><div class='kpi-label'>Duration</div><div class='kpi-value'>{days} days</div></div>",
        unsafe_allow_html=True,
    )
with kpi_cols[2]:
    st.markdown(
        f"<div class='kpi'><div class='kpi-label'>Travelers</div><div class='kpi-value'>{travelers}</div></div>",
        unsafe_allow_html=True,
    )
with kpi_cols[3]:
    st.markdown(
        f"<div class='kpi'><div class='kpi-label'>Budget</div><div class='kpi-value'>INR {int(budget):,}</div></div>",
        unsafe_allow_html=True,
    )

with st.expander("Preview generated prompt", expanded=False):
    st.code(query, language="text")

if st.button("Generate Travel Plan"):
    with st.spinner("Running research and building your itinerary..."):
        try:
            result = execute_query(
                query=query,
                verbose=show_steps,
                show_steps=show_steps,
                should_polish=not disable_polish,
            )

            output = result.get("output", "No output generated.")
            if result.get("fallback_mode"):
                st.warning(
                    "Running in fallback mode (no OpenRouter key). "
                    "Plan is generated from local heuristics and should be verified before booking."
                )
            sections = ordered_sections(split_markdown_sections(output))

            if len(sections) <= 1:
                st.markdown("<div class='plan-card section-default'>", unsafe_allow_html=True)
                st.markdown(output)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                for title, body in sections:
                    tag, cls = SECTION_META.get(title, (title.upper(), "section-default"))
                    st.markdown(f"<div class='plan-card {cls}'>", unsafe_allow_html=True)
                    st.markdown(f"<p class='section-tag'>{tag}</p>", unsafe_allow_html=True)
                    st.markdown(f"### {title}")
                    st.markdown(body)
                    st.markdown("</div>", unsafe_allow_html=True)

            st.download_button(
                label="Download Plan (.md)",
                data=output,
                file_name="travel_plan.md",
                mime="text/markdown",
            )

            if show_steps and "intermediate_steps" in result:
                with st.expander("Tool trace", expanded=False):
                    for idx, step in enumerate(result["intermediate_steps"], start=1):
                        action, observation = step
                        st.markdown(f"### Step {idx}")
                        st.write(f"Tool: {action.tool}")
                        st.write(f"Input: {action.tool_input}")
                        st.write(str(observation)[:1200])

            with st.expander("Raw response payload", expanded=False):
                safe = {
                    "output": result.get("output", ""),
                    "raw_output": result.get("raw_output", ""),
                }
                st.code(json.dumps(safe, indent=2), language="json")

        except Exception as exc:
            st.error(f"Error: {exc}")
            st.info("Set OPENROUTER_API_KEY in .env or environment before running.")
