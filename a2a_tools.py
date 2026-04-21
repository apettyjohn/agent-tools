"""A2A Toolkit for agent-to-agent communication and discovery.

This toolkit provides utilities for:
- Discovering agents by fetching their AgentCards from known URLs
- Sending messages to specific agents via A2A protocol
- Viewing available agents and their capabilities
"""

import asyncio
from typing import Any, Dict, List, Optional

from agno.tools.toolkit import Toolkit
from agno.utils.log import log_error, log_info, log_warning

try:
    from httpx import ConnectError, ConnectTimeout, TimeoutException
except ImportError:
    raise ImportError("`httpx` not installed. Please install using `pip install httpx`")


# Default list of agent URLs - can be overridden in __init__
DEFAULT_AGENT_URLS: List[str] = []


class AgentRegistry:
    """Registry for storing discovered agent cards."""

    def __init__(self):
        self._cards: Dict[str, Dict[str, Any]] = {}
        self._urls: Dict[str, str] = {}  # agent_id -> url mapping

    def add_card(self, agent_id: str, url: str, card_data: Dict[str, Any]) -> None:
        """Add an agent card to the registry."""
        self._cards[agent_id] = card_data
        self._urls[agent_id] = url

    def get_card(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get an agent card by ID."""
        return self._cards.get(agent_id)

    def get_url(self, agent_id: str) -> Optional[str]:
        """Get the URL for an agent by ID."""
        return self._urls.get(agent_id)

    def get_all_cards(self) -> Dict[str, Dict[str, Any]]:
        """Get all agent cards."""
        return self._cards.copy()

    def get_agents_table(self) -> List[Dict[str, Any]]:
        """Get a table-friendly list of all agents with their skills/uses."""
        result = []
        for agent_id, card_data in self._cards.items():
            skills = card_data.get("skills", [])
            skills_str = ", ".join([f"{s.get('name', 'unknown')}: {s.get('description', '')[:100]}" for s in skills]) or "None"
            
            result.append({
                "agent_id": agent_id,
                "name": card_data.get("name", "Unknown"),
                "url": self._urls.get(agent_id, "Unknown"),
                "description": card_data.get("description", "")[:200],
                "skills": skills_str,
                "capabilities": ", ".join(card_data.get("capabilities", [])) or "None",
                "version": card_data.get("version", "Unknown"),
            })
        return result


async def _fetch_agent_card(client, agent_id: str, url: str) -> Optional[Dict[str, Any]]:
    """Fetch an agent card from a single URL."""
    try:
        # Agno A2A endpoint: /a2a/agents/{id}/.well-known/agent-card.json
        response = await client.get(f"{url.rstrip('/')}/a2a/agents/{agent_id}/.well-known/agent-card.json", timeout=10.0)
        if response.status_code == 200:
            return response.json()
        else:
            log_warning(f"Failed to fetch agent card for '{agent_id}' from {url}: {response.status_code}")
            return None
    except (ConnectError, ConnectTimeout, TimeoutException) as e:
        log_error(f"Error fetching agent card for '{agent_id}' from {url}: {e}")
        return None
    except Exception as e:
        log_error(f"Unexpected error fetching agent card for '{agent_id}' from {url}: {e}")
        return None


class A2AToolkit(Toolkit):
    """Toolkit for A2A (Agent-to-Agent) protocol communication.

    This toolkit maintains a registry of known agents and their capabilities,
    allowing you to send messages to specific agents and discover their skills.

    Usage:
        toolkit = A2AToolkit(agent_urls=["http://localhost:7777", "http://localhost:8888"])
        # Agents are discovered automatically on init

        # Send a message to a specific agent
        result = toolkit.send_message_to_agent("agent-1", "Hello, what can you do?")

        # Get a table of all available agents
        agents = toolkit.get_agents_table()
    """

    def __init__(
        self,
        agent_urls: Optional[Dict[str, str]] = None,
        auto_discover: bool = True,
        name: str = "a2a_toolkit",
    ):
        """Initialize the A2A Toolkit.

        Args:
            agent_urls: Dict mapping agent IDs to their base URLs,
                        e.g. {"gcode": "http://localhost:8001", "kit": "http://localhost:8000"}
            auto_discover: Whether to automatically discover agents on init (default: True)
            name: Toolkit name
        """
        super().__init__(name=name)

        self.agent_urls_map: Dict[str, str] = agent_urls or {}  # agent_id -> base_url
        self.agent_urls: List[str] = list(self.agent_urls_map.values())
        self.registry: AgentRegistry = AgentRegistry()
        self._initialized: bool = False

        if auto_discover and self.agent_urls:
            # Run discovery in the event loop if one exists
            try:
                loop = asyncio.get_running_loop()
                # Schedule discovery to run after init completes
                loop.call_soon(self._run_discovery)
            except RuntimeError:
                # No running loop - run synchronously
                asyncio.run(self._discover_agents())

    def _run_discovery(self) -> None:
        """Run discovery in a background task."""
        asyncio.create_task(self._discover_agents())

    async def _discover_agents(self) -> None:
        """Discover agents by fetching their agent cards from all known URLs."""
        if not self.agent_urls:
            log_info("A2AToolkit: No agent URLs configured for discovery")
            return

        log_info(f"A2AToolkit: Discovering agents from {len(self.agent_urls)} URLs...")

        try:
            from httpx import AsyncClient

            async with AsyncClient() as client:
                tasks = [_fetch_agent_card(client, agent_id, url) for agent_id, url in self.agent_urls_map.items()]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for (agent_id, url), result in zip(self.agent_urls_map.items(), results):
                    if isinstance(result, Exception):
                        log_error(f"Error discovering agent '{agent_id}' at {url}: {result}")
                        continue

                    if result is not None:
                        self.registry.add_card(agent_id, url, result)
                        log_info(f"A2AToolkit: Discovered agent '{agent_id}' at {url}")

            self._initialized = True
            log_info(f"A2AToolkit: Discovery complete. Found {len(self.registry._cards)} agents.")

        except Exception as e:
            log_error(f"A2AToolkit: Error during agent discovery: {e}")

    def discover_agents(self) -> None:
        """Synchronously discover agents. Call this after init if no running loop."""
        if not self.agent_urls:
            return
        asyncio.run(self._discover_agents())

    async def adiscover_agents(self) -> None:
        """Async version of discover_agents."""
        await self._discover_agents()

    def send_message_to_agent(
        self,
        agent_id: str,
        message: str,
        context_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a message to a specific agent and return the response.

        Args:
            agent_id: The ID of the agent to send the message to
            message: The message text to send
            context_id: Optional session/context ID for multi-turn conversations
            user_id: Optional user identifier

        Returns:
            Dict containing the response from the agent
        """
        url = self.registry.get_url(agent_id)
        if not url:
            return {
                "success": False,
                "error": f"Agent '{agent_id}' not found in registry. "
                         f"Available agents: {list(self.registry._cards.keys())}",
            }

        try:
            from agno.client.a2a import A2AClient

            client = A2AClient(url)
            result = client.send_message(
                message=message,
                context_id=context_id,
                user_id=user_id,
            )

            return {
                "success": True,
                "agent_id": agent_id,
                "response": result.content if hasattr(result, "content") else str(result),
                "task_id": getattr(result, "task_id", None),
            }

        except Exception as e:
            log_error(f"Error sending message to agent {agent_id}: {e}")
            return {
                "success": False,
                "agent_id": agent_id,
                "error": str(e),
            }

    async def async_send_message_to_agent(
        self,
        agent_id: str,
        message: str,
        context_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Async version of send_message_to_agent.

        Args:
            agent_id: The ID of the agent to send the message to
            message: The message text to send
            context_id: Optional session/context ID for multi-turn conversations
            user_id: Optional user identifier

        Returns:
            Dict containing the response from the agent
        """
        url = self.registry.get_url(agent_id)
        if not url:
            return {
                "success": False,
                "error": f"Agent '{agent_id}' not found in registry. "
                         f"Available agents: {list(self.registry._cards.keys())}",
            }

        try:
            from agno.client.a2a import A2AClient

            client = A2AClient(url)
            result = await client.send_message(
                message=message,
                context_id=context_id,
                user_id=user_id,
            )

            return {
                "success": True,
                "agent_id": agent_id,
                "response": result.content if hasattr(result, "content") else str(result),
                "task_id": getattr(result, "task_id", None),
            }

        except Exception as e:
            log_error(f"Error sending message to agent {agent_id}: {e}")
            return {
                "success": False,
                "agent_id": agent_id,
                "error": str(e),
            }

    def get_agents_table(self) -> List[Dict[str, Any]]:
        """Get a table of all discovered agents with their skills/uses.

        Returns:
            List of dicts with keys: agent_id, name, url, description, skills, capabilities, version
        """
        return self.registry.get_agents_table()

    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific agent.

        Args:
            agent_id: The ID of the agent to get info for

        Returns:
            Dict containing the agent's card data, or None if not found
        """
        card = self.registry.get_card(agent_id)
        if card is None:
            return None

        return {
            "agent_id": agent_id,
            "url": self.registry.get_url(agent_id),
            **card,
        }

    def add_agent_url(self, agent_id: str, url: str) -> None:
        """Add a new agent URL to the registry and discover it.

        Args:
            agent_id: The ID of the agent (e.g., "gcode", "kit")
            url: The base URL of the agent server
        """
        if agent_id not in self.agent_urls_map:
            self.agent_urls_map[agent_id] = url
            self.agent_urls.append(url)

        # Discover the new agent
        asyncio.run(self._discover_agents())
