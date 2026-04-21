import sys
from pathlib import Path
import json

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from a2a_tools import A2AToolkit

# Create toolkit with agent URLs - discovery runs automatically
toolkit = A2AToolkit(agent_urls={
    "gcode": "http://localhost:8001",
    "navigator": "http://localhost:8000",
}, auto_discover=False)  # disable auto

toolkit.discover_agents()  # run synchronously

# View all discovered agents
agents = toolkit.get_agents_table()
if not agents:
    print("No agents found. Check URLs and try again.")
else:
    for agent in agents:
        # Print raw card data
        raw_card = toolkit.get_agent_info(agent['agent_id'])
        print(f"=== {agent['agent_id']} ===")
        print(json.dumps(raw_card, indent=2))
        print("---")