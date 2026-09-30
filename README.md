# 🔮 Fate Engine

**AI-powered life path simulator** — Monte Carlo futures for your biggest decisions.

Should you quit your job to start a startup? Move across the country? Go back to school?
Fate Engine runs hundreds of AI-generated simulations across career, finances, health,
relationships, and personal growth to show you what your possible futures look like.

---

## ✨ Features

- **Monte Carlo life simulation** — run 20–1000 probabilistic paths per option
- **Multi-dimensional scoring** — happiness, finances, career, relationships, health
- **Beautiful terminal UI** — branching trees, comparison tables, score bars, timelines
- **Interactive CLI** — guided life-situation interview or quick one-liner mode
- **REST API** — FastAPI server for web integrations
- **MCP server** — use Fate Engine as a tool in Claude, Cursor, and other AI assistants
- **Dual LLM support** — works with Anthropic Claude and OpenAI GPT

## 🚀 Quick start

```bash
# Clone & install
git clone <repo-url> && cd fateengine
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'

# Configure
cp .env.example .env
# Edit .env with your API key

# Run
fateengine quick "Should I quit my job to start a startup?"
```

## 📖 Usage

### Interactive simulation

```bash
fateengine simulate
```

Walks you through questions about your career, finances, health, relationships, and goals,
then asks about the decision you're facing. Outputs a rich visualisation of possible futures.

### Quick mode

```bash
fateengine quick "Should I move to Berlin for a new job?" --situation "Software engineer, NYC, 28 years old"
```

### Compare two options

```bash
fateengine compare "Stay at BigCo" "Join early-stage startup" \
  --context "Senior engineer, 150k salary, 2 kids" \
  --years 10 --paths 50
```

### API server

```bash
fateengine serve --port 8420
```

Then:

```bash
curl -X POST http://localhost:8420/api/v1/quick \
  -H 'Content-Type: application/json' \
  -d '{"situation": "Product manager, 35", "decision": "Should I switch to engineering?"}'
```

### MCP integration

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "fateengine": {
      "command": ".venv/bin/python",
      "args": ["-m", "fateengine.mcp.server"]
    }
  }
}
```

## 🏗 Architecture

| Module | Purpose |
|--------|---------|
| `models.py` | Pydantic v2 domain models |
| `config.py` | Environment-based configuration |
| `ai.py` | LLM abstraction (Claude + OpenAI) |
| `simulator.py` | Monte Carlo simulation engine |
| `visualizer.py` | Rich terminal visualisation |
| `cli.py` | Typer CLI |
| `api/app.py` | FastAPI REST API |
| `mcp/server.py` | MCP server (FastMCP) |

## 🧪 Tests

```bash
python -m pytest tests/ -v
```

## 📝 License

MIT
