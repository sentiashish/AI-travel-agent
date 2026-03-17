"""
ALTERNATIVE: Simple Travel Agent without paid API
Uses a simpler approach with DuckDuckGo search
and manual orchestration to demonstrate agent concepts.
"""

from langchain_community.tools import DuckDuckGoSearchRun
import json
import datetime


class SimpleTravelAgent:
    """
    A simple Travel Planning Agent that demonstrates
    agentic behavior: Goal → Plan → Tool Use → Output
    """

    def __init__(self):
        self.search_tool = DuckDuckGoSearchRun()
        self.memory = []  # Short-term memory
        self.reasoning_log = []  # Agent traces

    def log_step(self, thought, action, observation):
        """Log each reasoning step (for traces)."""
        step = {
            "step": len(self.reasoning_log) + 1,
            "timestamp": datetime.datetime.now().isoformat(),
            "thought": thought,
            "action": action,
            "observation": observation[:300]
        }
        self.reasoning_log.append(step)
        print(f"\n{'='*50}")
        print(f"📍 STEP {step['step']}")
        print(f"💭 Thought: {thought}")
        print(f"🔧 Action: {action}")
        print(f"👁️  Observation: {observation[:300]}...")
        print(f"{'='*50}")

    def search(self, query):
        """Tool 1: Web Search."""
        try:
            result = self.search_tool.run(query)
            return result
        except Exception as e:
            return f"Search error: {str(e)}"

    def calculate_budget(self, days, hotel_per_day, food_per_day,
                         transport_per_day, activities_per_day, num_people):
        """Tool 2: Budget Calculator."""
        total_hotel = hotel_per_day * days
        total_food = food_per_day * days * num_people
        total_transport = transport_per_day * days
        total_activities = activities_per_day * days * num_people
        grand_total = (total_hotel + total_food +
                       total_transport + total_activities)
        per_person = grand_total / num_people

        return {
            "accommodation": total_hotel,
            "food": total_food,
            "transport": total_transport,
            "activities": total_activities,
            "grand_total": grand_total,
            "per_person": per_person
        }

    def read_preferences(self, file_path):
        """Tool 3: File Reader."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"error": "File not found"}

    def plan_trip(self, destination, days, budget, interests,
                  num_people, travel_month):
        """
        Main agent orchestration method.
        Implements ReAct-style: Thought → Action → Observation loop
        """

        print("\n" + "🌍" * 30)
        print("  TRAVEL PLANNING AGENT ACTIVATED")
        print("🌍" * 30)

        self.memory.append({
            "role": "user",
            "request": f"Plan {days}-day trip to {destination}"
        })

        # ===== STEP 1: Search for destination info =====
        thought1 = (f"I need to find information about {destination} "
                     f"as a travel destination, including top attractions "
                     f"and things to do.")
        search_q1 = f"Top tourist attractions in {destination} 2025"
        result1 = self.search(search_q1)
        self.log_step(thought1, f"WebSearch('{search_q1}')", result1)

        # ===== STEP 2: Search for weather =====
        thought2 = (f"I should check the weather in {destination} "
                     f"during {travel_month} to plan appropriate activities.")
        search_q2 = f"Weather in {destination} in {travel_month}"
        result2 = self.search(search_q2)
        self.log_step(thought2, f"WebSearch('{search_q2}')", result2)

        # ===== STEP 3: Search for hotels =====
        thought3 = (f"Now I need to find accommodation options "
                     f"in {destination} within the budget range.")
        search_q3 = (f"Best budget hotels in {destination} "
                      f"price per night 2025")
        result3 = self.search(search_q3)
        self.log_step(thought3, f"WebSearch('{search_q3}')", result3)

        # ===== STEP 4: Search for food =====
        thought4 = (f"I should find popular local food and restaurants "
                     f"in {destination} for the travelers.")
        search_q4 = f"Best local food restaurants in {destination}"
        result4 = self.search(search_q4)
        self.log_step(thought4, f"WebSearch('{search_q4}')", result4)

        # ===== STEP 5: Calculate budget =====
        thought5 = ("Now I'll calculate the budget breakdown for the trip.")
        budget_result = self.calculate_budget(
            days=days,
            hotel_per_day=budget // (days * 3),  # ~1/3 of daily for hotel
            food_per_day=int(budget / (days * num_people * 4)),
            transport_per_day=int(budget / (days * 8)),
            activities_per_day=int(budget / (days * num_people * 5)),
            num_people=num_people
        )
        self.log_step(
            thought5,
            f"BudgetCalculator(days={days}, people={num_people})",
            json.dumps(budget_result, indent=2)
        )

        # ===== STEP 6: Generate Itinerary =====
        thought6 = ("I now have enough information to create a "
                     "comprehensive day-by-day itinerary.")

        itinerary = self._create_itinerary(
            destination, days, interests,
            result1, result2, result3, result4, budget_result
        )
        self.log_step(thought6, "GenerateItinerary()", "Itinerary created")

        # Store in memory
        self.memory.append({
            "role": "agent",
            "output": "Trip planned successfully",
            "budget": budget_result
        })

        return itinerary, budget_result

    def _create_itinerary(self, destination, days, interests,
                          attractions_info, weather_info,
                          hotel_info, food_info, budget):
        """Generate a formatted itinerary."""

        # Sample itinerary structure (in real case, LLM would generate this)
        sample_plans = {
            "Goa": [
                {
                    "day": 1,
                    "theme": "Arrival & North Goa Beaches",
                    "morning": "Arrive in Goa, check into hotel, freshen up",
                    "afternoon": "Visit Baga Beach - sunbathe, swim, try water sports",
                    "evening": "Explore Tito's Lane for nightlife, dinner at Britto's",
                    "meals": "Breakfast at hotel | Lunch at beach shack | Dinner at Britto's",
                    "tips": "Book hotel near Calangute/Baga for easy beach access"
                },
                {
                    "day": 2,
                    "theme": "Water Sports & Adventure Day",
                    "morning": "Scuba diving or snorkeling at Grande Island",
                    "afternoon": "Parasailing and jet skiing at Calangute Beach",
                    "evening": "Sunset at Anjuna Beach, visit flea market if Wednesday",
                    "meals": "Early breakfast | Packed lunch on boat | Seafood dinner at Curlies",
                    "tips": "Book water sports in advance, carry waterproof phone pouch"
                },
                {
                    "day": 3,
                    "theme": "Heritage & Culture Day",
                    "morning": "Visit Basilica of Bom Jesus (UNESCO site) & Se Cathedral",
                    "afternoon": "Explore Fort Aguada, lunch at Panjim old town",
                    "evening": "Cruise on Mandovi River with live music",
                    "meals": "Breakfast at hotel | Lunch at Viva Panjim | Dinner on cruise",
                    "tips": "Dress modestly for churches, carry water bottle"
                },
                {
                    "day": 4,
                    "theme": "South Goa Exploration",
                    "morning": "Drive to Dudhsagar Waterfalls (jeep safari)",
                    "afternoon": "Visit Palolem Beach - kayaking & dolphin spotting",
                    "evening": "Silent noise party at Palolem or beach bonfire",
                    "meals": "Early breakfast | Lunch near Dudhsagar | Dinner at Magic Italy Palolem",
                    "tips": "Start early for Dudhsagar, wear trekking shoes"
                },
                {
                    "day": 5,
                    "theme": "Relaxation & Departure",
                    "morning": "Yoga session at Ashwem Beach, souvenir shopping at Mapusa Market",
                    "afternoon": "Relax at Morjim Beach, final swim",
                    "evening": "Departure - head to airport/station",
                    "meals": "Breakfast at beach cafe | Farewell lunch at Fisherman's Wharf",
                    "tips": "Pack spices and cashews as souvenirs from Mapusa"
                }
            ]
        }

        # Use sample or generate generic
        if destination.lower() in [k.lower() for k in sample_plans]:
            plan_days = sample_plans.get(destination, sample_plans["Goa"])
        else:
            plan_days = []
            for d in range(1, days + 1):
                plan_days.append({
                    "day": d,
                    "theme": f"Day {d} Exploration",
                    "morning": f"Explore popular morning attractions in {destination}",
                    "afternoon": f"Visit local markets and landmarks",
                    "evening": f"Enjoy local cuisine and nightlife",
                    "meals": "Local restaurants",
                    "tips": "Ask locals for hidden gems!"
                })

        # Format output
        output = f"""
{'🌴'*25}
    ✈️  TRAVEL ITINERARY: {destination.upper()} ✈️
{'🌴'*25}

📅 Duration: {days} Days
👥 Travelers: Group trip
📍 Destination: {destination}
🗓️  Generated: {datetime.datetime.now().strftime('%B %d, %Y')}

{'='*60}
"""
        for day in plan_days[:days]:
            output += f"""
┌{'─'*58}┐
│  📌 DAY {day['day']} - {day['theme']}
├{'─'*58}┤
│  🌅 Morning   : {day['morning']}
│  ☀️  Afternoon : {day['afternoon']}
│  🌙 Evening   : {day['evening']}
│  🍽️  Meals     : {day['meals']}
│  💡 Tips      : {day['tips']}
└{'─'*58}┘
"""

        output += f"""
{'='*60}
💰 BUDGET SUMMARY
{'='*60}
🏨 Accommodation : ₹{budget['accommodation']:,.0f}
🍽️  Food & Dining : ₹{budget['food']:,.0f}
🚗 Transport     : ₹{budget['transport']:,.0f}
🎯 Activities    : ₹{budget['activities']:,.0f}
{'─'*40}
💵 GRAND TOTAL   : ₹{budget['grand_total']:,.0f}
👤 Per Person    : ₹{budget['per_person']:,.0f}
{'='*60}

📋 PACKING SUGGESTIONS:
  ☑️  Sunscreen SPF 50+
  ☑️  Swimwear & beach towel
  ☑️  Comfortable walking shoes
  ☑️  Light cotton clothes
  ☑️  Waterproof phone pouch
  ☑️  First aid kit
  ☑️  Power bank
  ☑️  Sunglasses & hat

🔑 GENERAL TIPS:
  • Book accommodation in advance during peak season
  • Carry cash for small vendors
  • Stay hydrated and use sunscreen
  • Respect local customs and environment
  • Keep emergency numbers saved
  • Download offline maps
"""
        return output

    def get_reasoning_log(self):
        """Return the complete reasoning log for analysis."""
        return self.reasoning_log

    def export_log(self, filename="agent_log.json"):
        """Export reasoning logs to a JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.reasoning_log, f, indent=2)
        print(f"✅ Agent logs exported to {filename}")


# ============================================================
# MAIN EXECUTION
# ============================================================

if __name__ == "__main__":
    # Create agent
    agent = SimpleTravelAgent()

    # Run the travel planning
    itinerary, budget = agent.plan_trip(
        destination="Goa",
        days=5,
        budget=50000,
        interests=["beaches", "water sports", "nightlife",
                    "local cuisine", "historical sites"],
        num_people=3,
        travel_month="December"
    )

    # Print the itinerary
    print(itinerary)

    # Export reasoning logs
    agent.export_log("agent_reasoning_log.json")

    # Print reasoning summary
    print("\n" + "=" * 60)
    print("📋 AGENT REASONING TRACE SUMMARY")
    print("=" * 60)
    for step in agent.get_reasoning_log():
        print(f"\nStep {step['step']} [{step['timestamp']}]")
        print(f"  💭 {step['thought']}")
        print(f"  🔧 {step['action']}")
