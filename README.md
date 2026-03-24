# AI Travel Planning Agent (SEM 6)

This project includes:
- A Streamlit web app UI
- A LangChain ReAct travel agent with tools (search, budget, itinerary, file reader)
- A simple fallback agent implementation for demonstration

## Project Files

- `app.py`: Streamlit frontend
- `travel_agent.py`: Main LangChain + OpenRouter agent (CLI + logic)
- `alternative_simple_agent.py`: Simpler non-LLM orchestration demo
- `sample_preferences.json`: Example structured input file
- `requirements.txt`: Python dependencies
- `agent_run_history.jsonl`: Persistent run history (auto-created)
- `architecture_diagram.md`: Mermaid architecture diagram
- `tool_flow_diagram.md`: Mermaid tool flow diagram
- `experiments_template.md`: Report analysis template
- `PRODUCTION_CHECKLIST.md`: Production readiness checklist

## Prerequisites

- Windows PowerShell
- Python 3.10+ (recommended 3.11)
- Internet connection
- OpenRouter API key (required for `travel_agent.py` and `app.py`)

## Step-by-Step Setup (Windows)

1. Open PowerShell and go to this folder:

```powershell
cd "c:\Users\ASHISH KUMAR\OneDrive\Documents\Desktop\KJSCE\kj stuff\TY Full Syllabus\AI Lab CA-1\ai-ia-sem6"
```

2. Create a virtual environment:

```powershell
python -m venv .venv
```

3. Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

4. Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

5. Set OpenRouter API key (current terminal session):

```powershell
$env:OPENROUTER_API_KEY="your_openrouter_api_key_here"
```

Optional model override:

```powershell
$env:OPENROUTER_MODEL="meta-llama/llama-3-8b-instruct"
```

## Run Options

### 1) Streamlit UI (Recommended)

```powershell
python -m streamlit run app.py
```

Then open the local URL shown in terminal.

### 2) One-shot CLI Query

```powershell
python travel_agent.py --query "Plan a 5-day trip to Goa for 3 friends under INR 50000"
```

### 3) CLI with JSON Preferences

```powershell
python travel_agent.py --preferences sample_preferences.json
```

### 4) Interactive CLI Mode

```powershell
python travel_agent.py --interactive
```

### 5) Simple Agent Demo (No OpenRouter Key Needed)

```powershell
python alternative_simple_agent.py
```

## Useful Flags (Main Agent)

- `--show-steps`: print intermediate tool trace
- `--no-polish`: disable final polishing step

Example:

```powershell
python travel_agent.py --query "Plan a 3-day Jaipur trip" --show-steps --no-polish
```

## Observability and Logs

- Every run is appended to `agent_run_history.jsonl` with:
	- timestamp
	- query
	- fallback mode status
	- output preview
	- optional tool traces (when `--show-steps` is enabled)

- Simple agent traces are exported to:
	- `agent_reasoning_log.json`

## Troubleshooting

### Missing OPENROUTER_API_KEY

If you see:
`Missing OPENROUTER_API_KEY. Add it to your environment or .env file.`

Set the key in PowerShell:

```powershell
$env:OPENROUTER_API_KEY="your_openrouter_api_key_here"
```

### Import errors (langchain/streamlit not found)

Make sure the venv is active and reinstall:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Preferences file not found

Use path relative to this repo or full absolute path:

```powershell
python travel_agent.py --preferences sample_preferences.json
```
