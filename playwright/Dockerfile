# ============================================================================
# Playwright Browser Agent Container
# ============================================================================
# This container runs the Playwright Browser Agent as an A2A service.
#
# The @playwright/mcp server is spawned internally by agno's MCPTools
# when the agent starts via `npx @playwright/mcp@latest`.
#
# Port: 8002 - Agent A2A server
# ============================================================================

FROM agnohq/python:3.12

# Install Node.js and npm for MCP server (npx)
RUN apt-get update && \
    apt-get install -y --no-install-recommends nodejs npm curl && \
    rm -rf /var/lib/apt/lists/*

# Install Playwright browsers
RUN npx -y playwright install chrome

# Install uv for fast Python package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

# Application code
WORKDIR /app
COPY . .
RUN uv pip install --system -e . --no-cache
ENV PYTHONPATH=/app

# Expose agent port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Run the agent (it spawns the MCP server internally via MCPTools)
CMD ["uvicorn", "playwright_agent:app", "--host", "0.0.0.0", "--port", "8002"]
