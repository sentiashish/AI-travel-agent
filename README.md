# AI Travel Planning Agent

A Streamlit travel-planning application built with LangChain. It creates
day-by-day travel plans, budget estimates, practical travel notes, and
downloadable Markdown/PDF plans.

The project has two modes:

- **Main agent** (`app.py` / `travel_agent.py`): uses OpenRouter and
  DuckDuckGo search for live AI-assisted responses. If its key is missing or
  unavailable, it automatically returns a clearly labelled local fallback plan.
- **Simple demo** (`alternative_simple_agent.py`): demonstrates the search,
  budget, and itinerary workflow without an LLM API key. It still requires an
  internet connection for DuckDuckGo search.

## Repository files

- `app.py` — Streamlit web interface
- `travel_agent.py` — LangChain agent, tools, fallback planning, and CLI
- `alternative_simple_agent.py` — simple agent demonstration
- `sample_preferences.json` — sample structured trip preferences
- `requirements.txt` — Python dependencies
- `.env.example` — safe environment-variable template
- `DEPLOYMENT.md` — hosting instructions

## Requirements

- Python 3.10 or later (Python 3.11 recommended)
- Internet connection for live search and OpenRouter
- An OpenRouter API key for live AI results

## Local setup on Windows PowerShell

Open PowerShell and run these commands exactly from the project folder:

```powershell
cd "C:\Users\ASHISH KUMAR\Desktop\AI\AI-travel-agent"
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Your prompt should begin with `(.venv)`. Activating the environment does not
change directories, so keep the terminal in `AI-travel-agent` before running
`app.py`, `travel_agent.py`, or `alternative_simple_agent.py`.

## Configure OpenRouter

For the current PowerShell session:

```powershell
$env:OPENROUTER_API_KEY="sk-or-v1-your-real-key"
```

Alternatively, copy `.env.example` to `.env`, replace the placeholder value,
and keep `.env` private. It is ignored by Git.

```powershell
Copy-Item .env.example .env
```

## Run the application

### Streamlit web UI

```powershell
python -m streamlit run app.py
```

Open the URL shown in the terminal, normally `http://localhost:8501`. Stop the
server with `Ctrl+C`.

### One-time CLI query

```powershell
python travel_agent.py --query "Plan a 5-day trip to Goa for 3 people under INR 50000"
```

### Preferences JSON

```powershell
python travel_agent.py --preferences sample_preferences.json
```

### Interactive CLI

```powershell
python travel_agent.py --interactive
```

Useful flags: `--show-steps` prints tool traces; `--no-polish` skips the
final AI editing pass.

### Simple demo agent

```powershell
python alternative_simple_agent.py
```

This demo now configures UTF-8 console output itself, so it works in standard
Windows PowerShell without setting `PYTHONUTF8` manually.

## Troubleshooting

**`can't open file ... travel_agent.py`** — you are in the wrong folder.
Run `cd "C:\Users\ASHISH KUMAR\Desktop\AI\AI-travel-agent"` first.

**`streamlit` or `langchain` is not found** — activate `.venv`, then run
`python -m pip install -r requirements.txt`.

**Missing or invalid `OPENROUTER_API_KEY`** — add a real key to `.env` or the
current PowerShell session. The main application uses its fallback planner if
the key cannot be used.

**Search fails** — check your internet connection or try again later; the
search provider may temporarily rate-limit requests.

## Deployment

Yes, the Streamlit UI can be deployed. See [DEPLOYMENT.md](DEPLOYMENT.md) for
Streamlit Community Cloud, Render, and Railway settings. Add
`OPENROUTER_API_KEY` through the platform's secret manager, never in Git.

## Before pushing to GitHub

```powershell
git status
git add app.py travel_agent.py alternative_simple_agent.py README.md run.txt .gitignore .env.example DEPLOYMENT.md requirements.txt sample_preferences.json
git commit -m "Prepare travel agent for deployment"
git push
```

Check `git status` before committing and do not stage `.env`, virtual
environments, generated logs, or files containing real API keys.
