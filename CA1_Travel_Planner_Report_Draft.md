# CA-1 Report Draft: Agentic AI Travel Planning Agent

## 1. Activity Fit Check (Are we on the correct path?)

Yes. The selected problem statement (Travel Planning Agent) is fully aligned with the activity requirements.

Why this project is valid:
- Uses a modern agent framework: LangChain ReAct-style agent.
- Uses an LLM as reasoning engine (OpenRouter-backed Chat model in main flow).
- Uses multiple tools: web search, budget calculator, file reader, itinerary formatter.
- Shows multi-step agent behavior with tool traces and observations.
- Includes a fallback path so the system still demonstrates orchestration even without API key.

Conclusion:
- The current project direction is correct and submission-worthy for CA-1.

---

## 2. Learning Objectives and How This Project Meets Them

### Objective 1: Understand Agentic AI beyond classical agents
How achieved:
- The system is not a fixed if-else chatbot.
- It performs iterative reasoning, selects tools, and composes a final plan.

### Objective 2: Learn how LLMs act as reasoning agents
How achieved:
- The main agent follows ReAct-style loops:
  Question -> Thought -> Action -> Observation -> Final Answer.
- LLM decides what tool to call next based on intermediate observations.

### Objective 3: Use tool-using, planning, and memory-based agents
How achieved:
- Tool usage: WebSearch, budget calculator, preferences file reader, itinerary generation.
- Planning: day-wise itinerary generation and structured budget split.
- Memory/context: conversation input + tool outputs + intermediate steps influence next actions.

### Objective 4: Compare classical AI agents vs modern agentic systems
How achieved:
- This report includes a direct comparison table in Section 8.

---

## 3. Project Goal and Agent Role

### Agent Goal
Given a user travel goal (destination, duration, budget, interests, travelers), generate a practical, day-by-day travel plan with budget breakdown, transport, food, and safety guidance.

### Agent Role
Act as an autonomous travel planning assistant that:
- Understands user constraints.
- Gathers destination intelligence.
- Calculates feasible cost split.
- Produces actionable itinerary output.

---

## 4. Activity Description Mapping

Required behavior from activity:
- Understand goal.
- Plan steps.
- Use tools.
- Produce output.

Observed in project:
- Understand goal: user query or preferences JSON parsed into trip intent.
- Plan steps: ReAct sequence and staged itinerary composition.
- Use tools: search + calculation + file read + formatting.
- Produce output: markdown itinerary and budget report for UI/CLI.

---

## 5. AI Tools and Frameworks Used

Frameworks and platforms:
- LangChain (agent framework)
- ReAct-style agent pattern
- OpenRouter API for LLM inference
- Streamlit for UI interface

Integrated tools:
- DuckDuckGo web search
- Budget calculator utility
- File/document reader (JSON/CSV)
- Python orchestration utilities

This satisfies the requirement of using at least one modern agent framework/toolset.

---

## 6. Part A - Agent Design (Modern View)

### 6.1 Goal of Agent
Produce a reliable travel itinerary under user constraints.

### 6.2 Agent Role
Autonomous planner and tool orchestrator.

### 6.3 Tools Used
- WebSearch: fetch destination/weather/hotel/food context.
- BudgetCalculator: compute category-level costs and per-person estimate.
- ReadPreferences: load structured user constraints from JSON/CSV.
- GenerateItinerary: convert plan structure to readable itinerary text.

### 6.4 Memory Type
- Short-term/contextual memory:
  - Inputs, intermediate observations, and generated outputs retained during one run.
  - Reasoning steps/log traces retained and exportable.

### 6.5 Planning Strategy
- ReAct and step-by-step planning:
  - Think
  - Choose tool
  - Observe result
  - Update reasoning
  - Repeat until final answer

---

## 7. Part B - Implementation (Modern AI Tools)

Minimum requirement checklist:
- One LLM-based agent: Completed (main travel agent).
- At least two tools: Completed (4 tools integrated).
- Multi-step reasoning: Completed (iterative tool chain).
- Observable behavior/logs: Completed (intermediate steps + reasoning log export).

Example trace format in this project:
- User Goal -> Agent Reasoning -> Tool Call -> Observation -> Next Action -> Final Answer

Implementation note:
- Offline fallback mode is included for robustness when API auth is unavailable.
- This ensures demonstration feasibility in classroom/lab constraints.

---

## 8. Part C - Analysis and Comparison

| Classical Agent (Syllabus) | Modern Agent (This Activity) |
|---|---|
| Rule-based | LLM-driven |
| Static logic | Dynamic planning |
| No memory/context | Contextual short-term memory |
| Single-step behavior | Multi-step reasoning with tool loops |
| Limited adaptability | Adapts to user constraints and observations |

Reflection points:
- Modern agentic systems reduce manual rule writing.
- They improve flexibility, but require guardrails and validation.
- Trace visibility is important for debugging and trust.

---

## 9. Architecture Summary (Use in report)

High-level flow:
1. User input from UI or CLI.
2. Agent interprets travel goal.
3. Agent calls tools iteratively (search, budget, file read as needed).
4. Agent composes structured final plan.
5. UI renders sections and optional trace details.

Suggested architecture diagram blocks:
- User -> Streamlit UI/CLI -> Agent Orchestrator -> Tools Layer -> Final Plan Renderer

Suggested tool flow diagram sequence:
- Input -> Parse constraints -> WebSearch -> BudgetCalculator -> Itinerary synthesis -> Output

---

## 10. Deliverables Checklist (Submission Ready)

### Required deliverables
- PDF report (5-10 pages)
- Architecture diagram
- Tool flow diagram
- Code repository/notebook
- Agent interaction logs
- Prompts and output screenshots

### What to include from this project
- Source files and dependency list.
- Screenshots of:
  - UI input panel
  - Generated itinerary
  - Tool trace section
  - CLI run output
- Reasoning logs JSON export from simple agent run.

---

## 11. Evaluation Rubric Mapping (15 Marks)

### 1) Use of modern tools and frameworks (4/4 target)
Evidence:
- LangChain ReAct, OpenRouter integration, Streamlit UI, integrated toolchain.

### 2) Agent reasoning and tool orchestration (4/4 target)
Evidence:
- Multi-step Thought/Action/Observation behavior, budget and search synthesis.

### 3) Architecture and design clarity (4/4 target)
Evidence:
- Clear modular files, separated tools, UI orchestration, structured output sections.

### 4) Analysis and reflection (3/3 target)
Evidence:
- Classical vs modern comparison and limitations/benefits discussion.

---

## 12. Suggested Report Section Order (Copy as headings)

1. Introduction and Problem Statement
2. Learning Objectives
3. Agent Design (Goal, Role, Tools, Memory, Planning)
4. System Architecture
5. Implementation Details
6. Sample Runs and Logs
7. Analysis and Comparison with Classical Agents
8. Challenges, Limitations, and Future Improvements
9. Conclusion
10. References

---

## 13. Future Improvements (Optional)

- Add calendar integration for itinerary scheduling.
- Add persistent trip history database.
- Add cost estimation with live APIs.
- Add multilingual prompt/output support.
- Add itinerary quality scoring and validation.

---

## 14. Final Statement for Faculty

This Travel Planning Agent demonstrates modern Agentic AI concepts (reasoning, tool use, orchestration, and traceability) while staying feasible for undergraduate implementation. The work directly extends classical intelligent-agent ideas into current LLM-based practice.
