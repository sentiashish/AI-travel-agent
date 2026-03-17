import os
import json
import datetime
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain.agents import create_react_agent
from langchain.agents.agent import AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain.tools import Tool, tool
from langchain_community.tools import DuckDuckGoSearchRun
search = DuckDuckGoSearchRun(region="in-en")
from langchain.memory import ConversationBufferMemory

# If using OpenRouter (free API)
# Set your API key in .env file or directly here
load_dotenv()

# ============================================================
# SECTION 1: LLM SETUP (Using OpenRouter - Free API)
# ============================================================

def setup_llm():
    """
    Setup LLM using OpenRouter's free API.
    OpenRouter provides free access to models like
    meta-llama/llama-3-8b-instruct (free tier).
    """
    llm = ChatOpenAI(
        model="meta-llama/llama-3-8b-instruct",  # Free model
        openai_api_key=os.getenv("OPENROUTER_API_KEY", "your-key-here"),
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.7,
        max_tokens=2000
    )
    return llm


# ============================================================
# SECTION 2: TOOL DEFINITIONS
# ============================================================

# --- Tool 1: Web Search Tool ---
search = DuckDuckGoSearchRun()

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
@tool
def budget_calculator(query: str) -> str:
    """
    Calculates travel budget based on parameters.
    Input format: 'days=N, hotel_per_day=N, food_per_day=N, transport_per_day=N, activities_per_day=N, num_people=N'
    Example: 'days=5, hotel_per_day=2000, food_per_day=800, transport_per_day=500, activities_per_day=1000, num_people=3'
    Returns detailed budget breakdown.
    """
    try:
        # Parse the input
        params = {}
        for part in query.split(","):
            key, value = part.strip().split("=")
            params[key.strip()] = float(value.strip())

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
        return f"Error calculating budget. Please use format: 'days=N, hotel_per_day=N, food_per_day=N, transport_per_day=N, activities_per_day=N, num_people=N'. Error: {str(e)}"


# --- Tool 3: File Reader Tool (Reads user preferences from JSON) ---
@tool
def read_preferences(file_path: str) -> str:
    """
    Reads travel preferences from a JSON or CSV file.
    Input should be the file path.
    Returns the contents of the preference file.
    """
    try:
        if file_path.endswith('.json'):
            with open(file_path, 'r') as f:
                data = json.load(f)
            return json.dumps(data, indent=2)
        elif file_path.endswith('.csv'):
            import csv
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            return json.dumps(rows, indent=2)
        else:
            with open(file_path, 'r') as f:
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

Begin!

Question: {input}
Thought: {agent_scratchpad}"""


# ============================================================
# SECTION 4: AGENT CREATION AND EXECUTION
# ============================================================

def create_travel_agent():
    """Creates and returns the Travel Planning Agent."""

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

    # Create agent executor with memory
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,           # Shows reasoning traces/logs
        handle_parsing_errors=True,
        max_iterations=10,
        return_intermediate_steps=True  # Returns agent logs
    )

    return agent_executor


def run_travel_agent():
    """Main function to run the Travel Planning Agent."""

    print("=" * 60)
    print("🌍  TRAVEL PLANNING AGENT  🌍")
    print("=" * 60)
    print("I'm your AI Travel Planner! I can help you plan")
    print("your perfect trip with detailed itineraries,")
    print("budget calculations, and local recommendations.")
    print("=" * 60)

    agent = create_travel_agent()

    # Example query - modify as needed
    user_query = """
    Plan a 5-day trip to Goa, India for 3 friends.
    Budget: ₹50,000 total (moderate budget).
    Interests: beaches, water sports, nightlife, 
    local cuisine, historical sites.
    Travel dates: December 2025.
    We want a mix of adventure and relaxation.
    """

    print(f"\n📝 User Request: {user_query}")
    print("=" * 60)
    print("🤖 Agent is thinking...\n")

    try:
        # Run the agent
        result = agent.invoke({"input": user_query})

        # Print final output
        print("\n" + "=" * 60)
        print("✅ FINAL TRAVEL PLAN")
        print("=" * 60)
        print(result["output"])

        # Print agent reasoning logs
        if "intermediate_steps" in result:
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


# ============================================================
# SECTION 5: INTERACTIVE MODE
# ============================================================

def interactive_mode():
    """Run the agent in interactive chat mode."""

    agent = create_travel_agent()

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
            result = agent.invoke({"input": user_input})
            print(f"\n🤖 Agent: {result['output']}")
        except Exception as e:
            print(f"Error: {str(e)}")


# ============================================================
# SECTION 6: MAIN EXECUTION
# ============================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        run_travel_agent()
