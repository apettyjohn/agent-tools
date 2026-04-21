"""Test script for the Playwright Browser Agent.

This script tests:
1. Agent health check endpoint
2. A2A agent discovery
3. Basic browser automation via Playwright tools

Usage:
    python tests/test_playwright_agent.py
"""

import sys
import json
import httpx
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from a2a_tools import A2AToolkit


# =============================================================================
# Configuration
# =============================================================================

AGENT_URL = "http://localhost:8002"
AGENT_ID = "playwright-browser-agent"


# =============================================================================
# Tests
# =============================================================================

def test_health_check():
    """Test if the agent is up and responding."""
    print("=" * 60)
    print("TEST 1: Health Check")
    print("=" * 60)
    
    try:
        response = httpx.get(f"{AGENT_URL}/health", timeout=10)
        response.raise_for_status()
        print(f"✓ Agent is healthy: {response.status_code}")
        print(f"  Response: {response.json()}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False


def test_agent_discovery():
    """Test A2A agent discovery."""
    print("\n" + "=" * 60)
    print("TEST 2: A2A Agent Discovery")
    print("=" * 60)
    
    toolkit = A2AToolkit(agent_urls={"playwright-browser-agent": AGENT_URL}, auto_discover=False)
    toolkit.discover_agents()
    
    agents = toolkit.get_agents_table()
    if not agents:
        print("✗ No agents discovered")
        return False
    
    print(f"✓ Discovered {len(agents)} agent(s)")
    for agent in agents:
        print(f"  - {agent['agent_id']}: {agent.get('description', 'No description')[:60]}...")
    
    # Get full agent card
    raw_card = toolkit.get_agent_info(AGENT_ID)
    print(f"\n  Agent Card for {AGENT_ID}:")
    print(f"  {json.dumps(raw_card, indent=4)[:500]}...")
    
    return True


def test_browser_task():
    """Test sending a browser automation task to the agent."""
    print("\n" + "=" * 60)
    print("TEST 3: Browser Automation Task")
    print("=" * 60)
    
    toolkit = A2AToolkit(agent_urls={"playwright-browser-agent": AGENT_URL}, auto_discover=False)
    toolkit.discover_agents()

    task_input = {
        "task": "Take a snapshot of the current page to see what's available.",
    }
    
    print(f"  Sending task: {task_input['task']}")
    
    try:
        result = toolkit.send_message_to_agent(
            agent_id=AGENT_ID,
            message=task_input["task"],
        )
        print(f"  Result type: {type(result)}")
        if isinstance(result, dict):
            print(f"  Keys: {result.keys()}")
            if result.get("success"):
                print(f"\n✓ Task completed successfully!")
                if "response" in result:
                    print(f"  Response preview: {str(result['response'])[:300]}...")
                return True
            else:
                print(f"  ✗ FAILED: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"  Result: {str(result)[:300]}...")
        return True
    except Exception as e:
        print(f"✗ Task failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("Playwright Browser Agent Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health_check()))
    results.append(("Agent Discovery", test_agent_discovery()))
    results.append(("Browser Task", test_browser_task()))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    sys.exit(0 if passed == total else 1)
