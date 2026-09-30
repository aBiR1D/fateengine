# Fate Engine — Project Context

## What is this?
AI-powered life path simulator. Users describe their current life situation and a
decision they're facing. The engine runs Monte Carlo-style simulations using LLMs
to generate probability-weighted futures across career, finances, health,
relationships, and personal growth.

## Architecture
```
fateengine/
├── models.py       # Pydantic domain models (LifeState, Decision, LifePath, etc.)
├── config.py       # pydantic-settings config from env / .env
├── ai.py           # LLM abstraction (Anthropic + OpenAI)
├── simulator.py    # Core Monte Carlo simulation engine
├── visualizer.py   # Rich terminal visualisation
├── cli.py          # Typer CLI (simulate, quick, compare, serve)
├── api/app.py      # FastAPI REST API
└── mcp/server.py   # MCP server (FastMCP)
```

## Key commands
```bash
# Install
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'

# CLI
fateengine simulate          # Interactive mode
fateengine quick "Should I quit my job?"
fateengine compare "Stay" "Leave" --context "Senior dev, 5y tenure"
fateengine serve             # Start API server

# Tests
python -m pytest tests/ -v

# API
curl -X POST http://localhost:8420/api/v1/quick \
  -H 'Content-Type: application/json' \
  -d '{"situation": "Software engineer, 30y/o", "decision": "Should I start a startup?"}'
```

## Environment variables
- `FATEENGINE_PROVIDER` — `anthropic` or `openai`
- `FATEENGINE_ANTHROPIC_API_KEY` / `FATEENGINE_OPENAI_API_KEY`
- `FATEENGINE_MODEL` — model identifier
- `FATEENGINE_TEMPERATURE` — generation temperature (default 0.8)

## Design decisions
- Models are all Pydantic v2 with strict validation.
- AI layer uses `generate_json()` with schema hints for structured output.
- Simulation batches LLM calls with asyncio semaphore for concurrency control.
- Visualizer uses Rich exclusively — no external chart libraries needed.
- MCP server uses the official `mcp[cli]` FastMCP SDK.
