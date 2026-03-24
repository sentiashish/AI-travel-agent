import argparse
import os
import json
import datetime
import re
from pathlib import Path
from typing import Any, Dict
from dotenv import find_dotenv, load_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain.agents import create_react_agent
from langchain.agents.agent import AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain.tools import Tool, tool
from langchain_community.tools import DuckDuckGoSearchRun

# Resolve project files relative to this script so commands work from any cwd.
BASE_DIR = Path(__file__).resolve().parent
RUN_HISTORY_FILE = BASE_DIR / "agent_run_history.jsonl"

def load_environment() -> None:
    """Load environment variables from common project locations."""
    candidate_files = [
        BASE_DIR / ".env",
        BASE_DIR.parent / ".env",
    ]

    for env_file in candidate_files:
        if env_file.exists():
            load_dotenv(env_file, override=False)

    discovered = find_dotenv(usecwd=True)
    if discovered:
        load_dotenv(discovered, override=False)


# If using OpenRouter (free API)
# Set your API key in .env file or directly in environment variables.
load_environment()

OUTPUT_POLISH_PROMPT = """You are a senior travel consultant editor.
Rewrite the draft travel plan into a polished, human-quality, professional deliverable.

Rules:
- Keep facts from the draft; do not invent prices/events unless clearly labeled as estimate.
- Use clear, concise, high-trust language (not robotic, not overly dramatic).
- Use an executive tone suitable for a premium travel advisory report.
- Keep all currency in INR where possible.
- If details are missing, add practical assumptions as a short bullet list.
- Use compact bullets and short paragraphs. Do not write long prose blocks.
- Under Budget Breakdown, include a markdown table with columns: Category, Estimated Cost (INR), Notes.
- Under Day-by-Day Itinerary, use Day 1/Day 2 style subheadings with Morning/Afternoon/Evening bullets.
- Under Quick Booking Checklist, include exactly 8 checklist items using markdown task list format.
- Ensure this exact output structure with markdown headings:

## Trip Snapshot
## Day-by-Day Itinerary
## Budget Breakdown
## Stay and Transport Options
## Food and Local Experiences
## Safety and Practical Tips
## Quick Booking Checklist

Each section must be present. Keep the output actionable and easy to scan.

User request:
{query}

Draft plan:
{draft}
"""

REQUIRED_OUTPUT_SECTIONS = [
    "## Trip Snapshot",
    "## Day-by-Day Itinerary",
    "## Budget Breakdown",
    "## Stay and Transport Options",
    "## Food and Local Experiences",
    "## Safety and Practical Tips",
    "## Quick Booking Checklist",
]


def _extract_trip_fields(query: str) -> Dict[str, Any]:
    """Best-effort parser for key trip fields from natural language query."""
    text = query or ""

    days_match = re.search(r"(\d+)\s*-?\s*day", text, flags=re.IGNORECASE)
    days = int(days_match.group(1)) if days_match else 5

    travelers_match = re.search(r"for\s+(\d+)\s+(?:travelers?|friends?|people)", text, flags=re.IGNORECASE)
    travelers = int(travelers_match.group(1)) if travelers_match else 2

    budget_match = re.search(r"INR\s*([\d,]+)", text, flags=re.IGNORECASE)
    budget = int(budget_match.group(1).replace(",", "")) if budget_match else 30000

    destination = "Your Destination"
    destination_match = re.search(
        r"trip\s+to\s+(.+?)\s+for\s+\d+\s+(?:travelers?|friends?|people)",
        text,
        flags=re.IGNORECASE,
    )
    if not destination_match:
        destination_match = re.search(r"trip\s+to\s+(.+?)(?:[\.,]|$)", text, flags=re.IGNORECASE)
    if destination_match:
        destination = destination_match.group(1).strip()

    interests_text = "sightseeing, local food, culture"
    interests_match = re.search(r"Interests:\s*(.+?)\.", text, flags=re.IGNORECASE)
    if interests_match:
        interests_text = interests_match.group(1).strip()
    interests = [i.strip() for i in interests_text.split(",") if i.strip()]
    if not interests:
        interests = ["sightseeing", "local food", "culture"]

    return {
        "destination": destination,
        "days": max(days, 1),
        "travelers": max(travelers, 1),
        "budget": max(budget, 1000),
        "interests": interests,
    }


def build_offline_fallback_plan(query: str, reason: str = "") -> str:
    """Generate a useful markdown travel plan without requiring LLM/API access."""
    fields = _extract_trip_fields(query)
    destination = fields["destination"]
    days = fields["days"]
    travelers = fields["travelers"]
    budget = fields["budget"]
    interests = fields["interests"]

    accommodation = int(budget * 0.35)
    food = int(budget * 0.25)
    transport = int(budget * 0.15)
    activities = int(budget * 0.20)
    contingency = max(budget - (accommodation + food + transport + activities), 0)
    per_person = budget / max(travelers, 1)

    day_blocks = []
    for i in range(1, days + 1):
        focus = interests[(i - 1) % len(interests)]
        day_blocks.append(
            f"### Day {i}\n"
            f"- Morning: Visit a top-rated {focus} spot in {destination}; start early to avoid crowds.\n"
            f"- Afternoon: Explore nearby landmarks and local markets; keep 1-2 backup places.\n"
            f"- Evening: Try a well-reviewed local restaurant and a short leisure walk in a safe area."
        )

    assumptions = "\n".join([
        "- This fallback plan is generated without live LLM/API calls.",
        "- Costs are estimates and should be verified during booking.",
        "- Attraction timings and ticket prices may vary by season.",
    ])

    offline_note = ""
    if reason:
        offline_note = f"\n- Runtime note: {reason}\n"

    return f"""
## Trip Snapshot
- Destination: {destination}
- Duration: {days} days
- Travelers: {travelers}
- Budget: INR {budget:,}
- Focus: {", ".join(interests[:5])}
{offline_note}
### Practical Assumptions
{assumptions}

## Day-by-Day Itinerary
{chr(10).join(day_blocks)}

## Budget Breakdown
| Category | Estimated Cost (INR) | Notes |
|---|---:|---|
| Accommodation | {accommodation:,} | Mid-range hotel/hostel split |
| Food & Dining | {food:,} | Local meals + one special meal/day |
| Transport | {transport:,} | Local commute, airport/station transfers |
| Activities | {activities:,} | Tickets, experiences, entry fees |
| Contingency | {contingency:,} | Buffer for surge pricing/emergencies |
| Total | {budget:,} | Approximate total budget |

- Estimated per person: INR {per_person:,.0f}

## Stay and Transport Options
- Stay near central areas with high review counts and good public transport access.
- For budget travel: hostels/guesthouses; for comfort: 3-star hotels with breakfast.
- Use app-based cabs during late hours and keep offline maps downloaded.

## Food and Local Experiences
- Prioritize highly rated local eateries during lunch (less rush than dinner).
- Try region-specific dishes and one guided local food walk if available.
- Keep hydration, hygiene, and dietary preferences in mind.

## Safety and Practical Tips
- Keep digital + physical copies of IDs and booking confirmations.
- Avoid isolated routes late at night; use verified transport apps.
- Carry essential medicines, sunscreen, and a power bank.

## Quick Booking Checklist
- [ ] Book flights/train tickets
- [ ] Reserve accommodation in preferred area
- [ ] Create day-wise map pins for key places
- [ ] Pre-book top activity/experience slots
- [ ] Plan airport/station transfer
- [ ] Set daily spending cap
- [ ] Save emergency contacts and offline maps
- [ ] Keep backup payment method
""".strip()


def _extract_step_trace(result: Dict[str, Any]) -> list[Dict[str, Any]]:
    """Convert LangChain intermediate steps into JSON-serializable records."""
    steps: list[Dict[str, Any]] = []
    for idx, step in enumerate(result.get("intermediate_steps", []), start=1):
        try:
            action, observation = step
            steps.append(
                {
                    "step": idx,
                    "tool": getattr(action, "tool", "unknown"),
                    "tool_input": str(getattr(action, "tool_input", ""))[:1200],
                    "observation": str(observation)[:2000],
                }
            )
        except Exception:
            continue
    return steps


def persist_run_log(
    query: str,
    result: Dict[str, Any],
    show_steps: bool,
    should_polish: bool,
    error: str = "",
) -> None:
    """Append a single run record to local JSONL history for traceability."""
    record = {
        "timestamp": datetime.datetime.now().isoformat(),
        "query": query,
        "show_steps": show_steps,
        "should_polish": should_polish,
        "fallback_mode": bool(result.get("fallback_mode", False)),
        "error": error,
        "output_preview": str(result.get("output", ""))[:1200],
        "raw_output_preview": str(result.get("raw_output", ""))[:1200],
        "steps_count": len(result.get("intermediate_steps", [])),
    }

    if show_steps and "intermediate_steps" in result:
        record["steps"] = _extract_step_trace(result)

    RUN_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RUN_HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

# ============================================================
# SECTION 1: LLM SETUP (Using OpenRouter - Free API)
# ============================================================

def setup_llm() -> ChatOpenAI:
    """
    Setup LLM using OpenRouter's free API.
    OpenRouter provides free access to models like
    meta-llama/llama-3-8b-instruct (free tier).
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing OPENROUTER_API_KEY. Add it to your environment or .env file."
        )

    placeholder_markers = [
        "PASTE_YOUR",
        "YOUR_REAL_KEY",
        "YOUR_REAL_OPENROUTER_KEY",
        "your_openrouter_api_key_here",
    ]
    if any(marker.lower() in api_key.lower() for marker in placeholder_markers):
        raise RuntimeError(
            "Invalid OPENROUTER_API_KEY value (placeholder detected). "
            "Set your real OpenRouter key, e.g. starts with 'sk-or-v1-...'."
        )

    llm = ChatOpenAI(
        model=os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3-8b-instruct"),
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=float(os.getenv("TRAVEL_AGENT_TEMPERATURE", "0.3")),
        max_tokens=int(os.getenv("TRAVEL_AGENT_MAX_TOKENS", "1800")),
        request_timeout=float(os.getenv("TRAVEL_AGENT_REQUEST_TIMEOUT_SEC", "15")),
        max_retries=int(os.getenv("TRAVEL_AGENT_MAX_RETRIES", "1")),
    )
    return llm


def extract_final_answer(raw_output: str) -> str:
    """Extract only the final user-facing answer from agent output."""
    text = (raw_output or "").strip()
    if "Final Answer:" in text:
        text = text.split("Final Answer:", 1)[1].strip()
    return text


def normalize_output_layout(text: str) -> str:
    """Ensure output always includes required headings and clean spacing."""
    cleaned = (text or "").strip()
    if not cleaned:
        cleaned = "Travel plan could not be generated from available details."

    # Normalize heading depth to level-2 for consistency.
    cleaned = re.sub(r"^###\s+", "## ", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^#\s+", "## ", cleaned, flags=re.MULTILINE)

    lower_text = cleaned.lower()
    missing_sections = [
        section for section in REQUIRED_OUTPUT_SECTIONS
        if section.lower() not in lower_text
    ]

    if missing_sections:
        for section in missing_sections:
            cleaned += (
                "\n\n"
                f"{section}\n"
                "- Details not available from current sources; verify during booking."
            )

    # Collapse 3+ newlines into max 2 for cleaner visual density.
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


def polish_output(query: str, draft: str) -> str:
    """Polish draft output into a structured high-quality travel report."""
    try:
        llm = setup_llm()
        prompt = OUTPUT_POLISH_PROMPT.format(query=query, draft=draft)
        response = llm.invoke(prompt)
        content = getattr(response, "content", "")
        polished = content.strip() if content else draft
        return normalize_output_layout(polished)
    except Exception:
        # Never fail user response due to polishing step.
        return normalize_output_layout(draft)


# ============================================================
# SECTION 2: TOOL DEFINITIONS
# ============================================================

# --- Tool 1: Web Search Tool ---
search = DuckDuckGoSearchRun(region="in-en")

search_tool = Tool(
    name="WebSearch",
    func=search.run,
    description=(
        "Useful for searching the internet for travel information, "
        "tourist attractions, hotels, restaurants, weather forecasts, "
        "flight prices, and local tips for any destination. "
        "Input should be a search query string."
    )
)

# --- Tool 2: Budget Calculator Tool ---
def _parse_budget_query(query: str) -> Dict[str, float]:
    """Parse budget tool input from JSON or key=value text."""
    query = query.strip()
    if not query:
        raise ValueError("Empty input")

    # Accept structured JSON input for higher reliability in tool calls.
    if query.startswith("{"):
        raw = json.loads(query)
        return {k: float(v) for k, v in raw.items()}

    params: Dict[str, float] = {}
    for key, value in re.findall(r"([a-zA-Z_]+)\s*=\s*([-+]?[0-9]*\.?[0-9]+)", query):
        params[key.strip()] = float(value)

    if not params:
        raise ValueError("No key=value parameters found")
    return params


@tool
def budget_calculator(query: str) -> str:
    """
    Calculates travel budget based on parameters.
    Input format: 'days=N, hotel_per_day=N, food_per_day=N, transport_per_day=N, activities_per_day=N, num_people=N'
    Example: 'days=5, hotel_per_day=2000, food_per_day=800, transport_per_day=500, activities_per_day=1000, num_people=3'
    Returns detailed budget breakdown.
    """
    try:
        params = _parse_budget_query(query)

        days = int(params.get("days", 1))
        hotel = params.get("hotel_per_day", 0)
        food = params.get("food_per_day", 0)
        transport = params.get("transport_per_day", 0)
        activities = params.get("activities_per_day", 0)
        people = int(params.get("num_people", 1))

        # Calculations
        total_hotel = hotel * days
        total_food = food * days * people
        total_transport = transport * days
        total_activities = activities * days * people
        grand_total = total_hotel + total_food + total_transport + total_activities
        per_person = grand_total / people if people > 0 else grand_total

        result = f"""
💰 BUDGET BREAKDOWN
{'='*40}
📅 Trip Duration: {days} days
👥 Number of People: {people}

🏨 Accommodation: ₹{hotel}/night × {days} nights = ₹{total_hotel:,.0f}
🍽️  Food: ₹{food}/day × {days} days × {people} people = ₹{total_food:,.0f}
🚗 Transport: ₹{transport}/day × {days} days = ₹{total_transport:,.0f}
🎯 Activities: ₹{activities}/day × {days} days × {people} people = ₹{total_activities:,.0f}

{'='*40}
💵 GRAND TOTAL: ₹{grand_total:,.0f}
👤 Per Person: ₹{per_person:,.0f}
{'='*40}
"""
        return result

    except Exception as e:
        return (
            "Error calculating budget. Use JSON or format: "
            "'days=N, hotel_per_day=N, food_per_day=N, transport_per_day=N, "
            f"activities_per_day=N, num_people=N'. Error: {str(e)}"
        )


# --- Tool 3: File Reader Tool (Reads user preferences from JSON) ---
@tool
def read_preferences(file_path: str) -> str:
    """
    Reads travel preferences from a JSON or CSV file.
    Input should be the file path.
    Returns the contents of the preference file.
    """
    try:
        input_path = Path(file_path).expanduser()
        path = input_path if input_path.is_absolute() else (BASE_DIR / input_path)
        path = path.resolve()
        if path.suffix.lower() == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return json.dumps(data, indent=2)
        elif path.suffix.lower() == '.csv':
            import csv
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            return json.dumps(rows, indent=2)
        else:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
    except FileNotFoundError:
        return f"File '{file_path}' not found. Please provide a valid file path."
    except Exception as e:
        return f"Error reading file: {str(e)}"


# --- Tool 4: Itinerary Generator Tool ---
@tool
def generate_itinerary(plan_json: str) -> str:
    """
    Generates a formatted day-by-day itinerary from a JSON plan.
    Input should be a JSON string with format:
    {
        "destination": "City",
        "days": [
            {
                "day": 1,
                "theme": "Arrival & Exploration",
                "morning": "Activity",
                "afternoon": "Activity",
                "evening": "Activity",
                "meals": "Restaurant suggestions",
                "tips": "Any tips"
            }
        ]
    }
    """
    try:
        plan = json.loads(plan_json)
        destination = plan.get("destination", "Unknown")
        days = plan.get("days", [])

        if not isinstance(days, list):
            return "Error: 'days' should be a list in the itinerary JSON."

        itinerary = f"""
🌍 TRAVEL ITINERARY: {destination.upper()}
{'='*50}
📅 Duration: {len(days)} Days
🗓️  Generated on: {datetime.datetime.now().strftime('%B %d, %Y')}
{'='*50}
"""
        for day in days:
            itinerary += f"""
📌 DAY {day.get('day', '?')} - {day.get('theme', 'Exploration')}
{'-'*40}
🌅 Morning   : {day.get('morning', 'Free time')}
☀️  Afternoon : {day.get('afternoon', 'Free time')}
🌙 Evening   : {day.get('evening', 'Free time')}
🍽️  Meals     : {day.get('meals', 'Local restaurants')}
💡 Tips      : {day.get('tips', 'Enjoy!')}
"""
        return itinerary

    except json.JSONDecodeError:
        return "Error: Please provide a valid JSON string for the itinerary plan."
    except Exception as e:
        return f"Error generating itinerary: {str(e)}"


# ============================================================
# SECTION 3: AGENT PROMPT TEMPLATE (ReAct Style)
# ============================================================

TRAVEL_AGENT_PROMPT = """You are an expert Travel Planning Agent. Your job is to create comprehensive travel itineraries based on user requests.

You have access to the following tools:

{tools}

Tool names: {tool_names}

## Your Planning Process (ReAct Strategy):
1. UNDERSTAND the user's travel requirements (destination, dates, budget, interests, group size)
2. SEARCH for relevant information about the destination
3. SEARCH for attractions, hotels, restaurants, and activities
4. CALCULATE the budget using the budget calculator
5. GENERATE a day-by-day itinerary
6. PROVIDE final recommendations and tips

## Response Format:
You must ALWAYS use this exact format:

Question: the input question/request you must answer
Thought: reason about what to do next
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

## Important Rules:
- Always search for UP-TO-DATE information
- Consider weather, local events, and safety
- Provide budget-friendly AND premium options
- Include local food recommendations
- Add practical travel tips
- Be specific with timings and locations
- In Final Answer, use professional markdown headings and actionable bullets
- Include a day-by-day plan and clear budget split
- Avoid generic filler; prioritize concrete recommendations

Begin!

Question: {input}
Thought: {agent_scratchpad}"""


# ============================================================
# SECTION 4: AGENT CREATION AND EXECUTION
# ============================================================

def create_travel_agent(verbose: bool = False, return_steps: bool = False) -> AgentExecutor:
    """Create and configure the Travel Planning Agent executor."""

    # Setup LLM
    llm = setup_llm()

    # Define tools list
    tools = [search_tool, budget_calculator, generate_itinerary, read_preferences]

    # Create prompt
    prompt = PromptTemplate(
        template=TRAVEL_AGENT_PROMPT,
        input_variables=["input", "agent_scratchpad", "tools", "tool_names"]
    )

    # Create ReAct agent
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,
        handle_parsing_errors=True,
        max_iterations=int(os.getenv("TRAVEL_AGENT_MAX_ITERATIONS", "8")),
        max_execution_time=float(os.getenv("TRAVEL_AGENT_MAX_EXECUTION_SEC", "20")),
        return_intermediate_steps=return_steps
    )

    return agent_executor


def execute_query(
    query: str,
    verbose: bool = False,
    show_steps: bool = False,
    should_polish: bool = True
) -> Dict[str, Any]:
    """Execute one planning query and return raw agent response."""
    try:
        agent = create_travel_agent(verbose=verbose, return_steps=show_steps)
        result = agent.invoke({"input": query})

        raw_output = extract_final_answer(str(result.get("output", "")))
        final_output = polish_output(query, raw_output) if should_polish else raw_output
        result["raw_output"] = raw_output
        result["output"] = final_output
        persist_run_log(query, result, show_steps, should_polish)
        return result
    except RuntimeError as exc:
        if "OPENROUTER_API_KEY" in str(exc):
            fallback = normalize_output_layout(build_offline_fallback_plan(query, str(exc)))
            result = {
                "output": fallback,
                "raw_output": fallback,
                "fallback_mode": True,
            }
            persist_run_log(query, result, show_steps, should_polish, error=str(exc))
            return result
        raise
    except Exception as exc:
        error_text = str(exc).lower()
        auth_markers = [
            "authenticationerror",
            "missing authentication header",
            "invalid api key",
            "user not found",
            "401",
            "402",
            "insufficient credits",
            "never purchased credits",
            "payment required",
        ]
        connection_markers = [
            "connection error",
            "apiconnectionerror",
            "timed out",
            "temporarily unavailable",
            "503",
            "502",
            "504",
        ]

        if any(marker in error_text for marker in auth_markers):
            reason = (
                "OpenRouter authorization or billing failed. "
                "Set a valid OPENROUTER_API_KEY and ensure account credits are available."
            )
            fallback = normalize_output_layout(build_offline_fallback_plan(query, reason))
            result = {
                "output": fallback,
                "raw_output": fallback,
                "fallback_mode": True,
            }
            persist_run_log(query, result, show_steps, should_polish, error=str(exc))
            return result

        if any(marker in error_text for marker in connection_markers):
            reason = (
                "OpenRouter connection failed. "
                "Check internet/network and retry; fallback mode used for continuity."
            )
            fallback = normalize_output_layout(build_offline_fallback_plan(query, reason))
            result = {
                "output": fallback,
                "raw_output": fallback,
                "fallback_mode": True,
            }
            persist_run_log(query, result, show_steps, should_polish, error=str(exc))
            return result

        persist_run_log(
            query,
            {"output": "", "raw_output": "", "fallback_mode": False},
            show_steps,
            should_polish,
            error=str(exc),
        )
        raise


def run_travel_agent(user_query: str, show_steps: bool = False, should_polish: bool = True) -> None:
    """Run a single travel planning request from the CLI."""

    print("=" * 60)
    print("🌍  TRAVEL PLANNING AGENT  🌍")
    print("=" * 60)
    print("I'm your AI Travel Planner! I can help you plan")
    print("your perfect trip with detailed itineraries,")
    print("budget calculations, and local recommendations.")
    print("=" * 60)

    print(f"\n📝 User Request: {user_query}")
    print("=" * 60)
    print("🤖 Agent is thinking...\n")

    try:
        result = execute_query(
            user_query,
            verbose=show_steps,
            show_steps=show_steps,
            should_polish=should_polish
        )

        # Print final output
        print("\n" + "=" * 60)
        print("✅ FINAL TRAVEL PLAN")
        print("=" * 60)
        print(result["output"])

        # Print agent reasoning logs
        if show_steps and "intermediate_steps" in result:
            print("\n" + "=" * 60)
            print("📋 AGENT REASONING LOG")
            print("=" * 60)
            for i, step in enumerate(result["intermediate_steps"]):
                action, observation = step
                print(f"\n--- Step {i+1} ---")
                print(f"🔧 Tool: {action.tool}")
                print(f"📥 Input: {action.tool_input}")
                print(f"📤 Output: {str(observation)[:500]}...")

    except Exception as e:
        print(f"Error: {str(e)}")
        print("Tip: Make sure your API key is set correctly.")


def build_query_from_preferences(file_path: str) -> str:
    """Build a deterministic natural language query from a JSON preferences file."""
    input_path = Path(file_path).expanduser()
    resolved = input_path if input_path.is_absolute() else (BASE_DIR / input_path)

    with open(resolved.resolve(), "r", encoding="utf-8") as f:
        data = json.load(f)

    destination = data.get("destination", "Unknown destination")
    days = data.get("trip_duration_days", "unspecified duration")
    num_travelers = data.get("num_travelers", "unspecified group size")
    budget = data.get("budget_total_inr", "unspecified budget")
    budget_category = data.get("budget_category", "unspecified")
    interests = ", ".join(data.get("interests", [])) or "general sightseeing"
    travel_dates = data.get("travel_dates", {})
    start = travel_dates.get("start", "")
    end = travel_dates.get("end", "")
    dates_text = f"from {start} to {end}" if start and end else "dates flexible"

    return (
        f"Plan a {days}-day trip to {destination} for {num_travelers} travelers. "
        f"Total budget is INR {budget} ({budget_category}). "
        f"Interests: {interests}. Travel window: {dates_text}. "
        "Provide a day-by-day itinerary, budget split, food recommendations, "
        "local transport guidance, and safety tips."
    )


# ============================================================
# SECTION 5: INTERACTIVE MODE
# ============================================================

def interactive_mode(show_steps: bool = False, should_polish: bool = True):
    """Run the agent in interactive chat mode."""

    print("=" * 60)
    print("🌍  TRAVEL PLANNING AGENT - Interactive Mode  🌍")
    print("=" * 60)
    print("Type your travel planning request.")
    print("Type 'quit' to exit.\n")

    while True:
        user_input = input("\n🧑 You: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Thank you for using Travel Planning Agent! Bon voyage!")
            break

        if not user_input:
            print("Please enter a travel planning request.")
            continue

        try:
            result = execute_query(
                user_input,
                verbose=show_steps,
                show_steps=show_steps,
                should_polish=should_polish
            )
            print(f"\n🤖 Agent: {result['output']}")
            if show_steps and "intermediate_steps" in result:
                print(f"\n🔎 Steps captured: {len(result['intermediate_steps'])}")
        except Exception as e:
            print(f"Error: {str(e)}")


# ============================================================
# SECTION 6: MAIN EXECUTION
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Industrial-grade AI Travel Planning Agent")
    parser.add_argument("--interactive", action="store_true", help="Run interactive prompt mode")
    parser.add_argument("--query", type=str, help="Single travel planning query")
    parser.add_argument("--preferences", type=str, help="Path to JSON preferences file")
    parser.add_argument("--show-steps", action="store_true", help="Print intermediate tool traces")
    parser.add_argument("--no-polish", action="store_true", help="Disable premium output polishing")
    args = parser.parse_args()

    default_query = (
        "Plan a 5-day trip to Goa, India for 3 friends. "
        "Budget: INR 50,000 total (moderate). "
        "Interests: beaches, water sports, nightlife, local cuisine, historical sites. "
        "Travel dates: December 2025."
    )

    if args.interactive:
        interactive_mode(show_steps=args.show_steps, should_polish=not args.no_polish)
    else:
        query = args.query or default_query
        if args.preferences:
            query = build_query_from_preferences(args.preferences)
        run_travel_agent(query, show_steps=args.show_steps, should_polish=not args.no_polish)
