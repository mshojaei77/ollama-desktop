"""
Test script for debugging agent initialization
"""

import asyncio
import logging
import sys

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Import the agent registry
from agents.registry import agent_registry

async def main():
    """Main test function"""
    print("Starting agent initialization test...")
    
    # Initialize the agent registry
    print("Initializing agent registry...")
    await agent_registry.initialize()
    
    # Get all registered agents
    agents = agent_registry.get_all_agents()
    print(f"Found {len(agents)} registered agents:")
    
    for agent in agents:
        print(f"  - {agent['name']} ({agent['id']})")
        print(f"    Description: {agent['description']}")
        print(f"    Tags: {', '.join(agent['tags'])}")
        print("")

if __name__ == "__main__":
    asyncio.run(main()) 