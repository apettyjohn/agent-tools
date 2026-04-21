"""Browser Automation Agent using xAI Grok 4.1 Fast via OpenRouter with Playwright MCP tools.

This agent is designed to run as a persistent service with an A2A interface,
connecting to a Playwright MCP server via stdio (npx subprocess).

Usage:
    uvicorn playwright_agent:app --host 0.0.0.0 --port 8002
"""

import os

from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.os import AgentOS
from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters


# =============================================================================
# Configuration
# =============================================================================

# Agent server config
AGENT_HOST = os.getenv("AGENT_HOST", "0.0.0.0")
AGENT_PORT = int(os.getenv("AGENT_PORT", "8002"))


# =============================================================================
# Agent
# =============================================================================

playwright_agent = Agent(
    name="Playwright Browser Agent",
    id="playwright-browser-agent",
    description="A browser automation agent that uses Playwright to interact with web pages. "
                "Can open browsers, navigate to URLs, click elements, fill forms, "
                "take snapshots, and extract information from web pages.",
    model=OpenRouter(
        id="x-ai/grok-4.1-fast",
        max_tokens=1500000,
    ),
    tools=[
        MCPTools(
            server_params=StdioServerParameters(
                command="npx",
                args=["-y", "@playwright/mcp@latest"],
            ),
        )
    ],
    instructions=[
        "You are a browser automation specialist.",
        "Use Playwright tools to interact with web pages as requested.",
        "Always provide clear descriptions of what you found or accomplished.",
        "Take screenshots when helpful for visual verification.",
        "Use 'snapshot' to get the current state of the page with interactive elements.",
    ],
    markdown=True,
)


# =============================================================================
# AgentOS Setup with A2A Interface
# =============================================================================

agent_os = AgentOS(
    id="playwright-agent-os",
    description="Persistent browser automation agent service with A2A interface",
    agents=[playwright_agent],
    a2a_interface=True,
)

app = agent_os.get_app()


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print(f"Starting Playwright Browser Agent on {AGENT_HOST}:{AGENT_PORT}")
    print("Using @playwright/mcp via stdio transport")
    print("A2A endpoint: /a2a/agents/playwright-browser-agent")
    
    uvicorn.run(
        "playwright_agent:app",
        host=AGENT_HOST,
        port=AGENT_PORT,
        reload=False,
        access_log=True,
    )
