# Agent Tools

[![Python](https://img.shields.io/badge/Python->=3.12-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/apettyjohn/agent-tools)](LICENSE)

Agent Tools is a collection of utilities and agents for AI agent development, focusing on agent-to-agent (A2A) communication and browser automation.

## Features

- **A2A Toolkit** (`a2a_tools.py`): Discover agents via AgentCards, send A2A protocol messages, and manage agent registries.
- **Playwright Browser Agent** (`playwright/playwright_agent.py`): Persistent FastAPI service using xAI Grok 4.1 Fast (via OpenRouter) with Playwright MCP tools for web automation (navigate, click, fill forms, screenshots, etc.).
- **Modular Design**: Built on [Agno](https://github.com/agno-agi/agno) framework.
- **Testing**: Comprehensive tests in `/tests/`.
- **Docker Support**: Playwright agent includes `Dockerfile` and `compose.yaml`.

## Quick Start

### Prerequisites
- Python &gt;=3.12
- [uv](https://astral.sh/uv) (recommended) or pip
- GitHub CLI (`gh`) for repo management

### Installation

```bash
cd agent-tools
uv sync  # or pip install -e .
```

### Usage

#### A2A Tools
```python
from a2a_tools import AgentRegistry  # Example usage
registry = AgentRegistry()
# Add/discover agents...
```

#### Playwright Agent (Server)
```bash
cd playwright
uvicorn playwright_agent:app --host 0.0.0.0 --port 8002
```

Or with Docker:
```bash
docker compose up
```

#### Main Entry
```bash
uv run main.py  # Prints &quot;Hello from agent-tools!&quot;
```

## Project Structure

```
agent-tools/
├── a2a_tools.py          # A2A communication toolkit
├── main.py               # Main entrypoint
├── pyproject.toml        # Project metadata &amp; deps
├── playwright/           # Browser agent
│   ├── playwright_agent.py
│   ├── Dockerfile
│   ├── compose.yaml
│   └── pyproject.toml
└── tests/                # Unit tests
    ├── a2a-tools-test.py
    └── test_playwright_agent.py
```

## Development

- **Format**: `uv run ruff format . &amp;&amp; uv run ruff check .`
- **Test**: `uv run pytest`
- **Build**: `uv build`

## Contributing

1. Fork &amp; clone
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit (`git commit -m 'Add some AmazingFeature'`)
4. Push &amp; PR

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

[MIT](LICENSE)
