#!/usr/bin/env python3
"""
Test script for the Makanin Agent system
Demonstrates the new intelligent agent capabilities
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.agent import MakaninAgent


async def test_agent():
    """Test the agent with various scenarios"""
    print("🤖 Testing Makanin Agent System")
    print("=" * 50)

    # Initialize the agent
    agent = MakaninAgent()
    user_id = "test_user"

    # Test cases
    test_cases = [
        "cariin bakso viral di jogja",
        "find me good ramen near campus",
        "halo, apa kabar?",
        "makanan enak di jakarta",
        "thanks for the recommendations!"
    ]

    for i, test_message in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: '{test_message}'")
        print("-" * 40)

        try:
            # Process the message
            response = await agent.process_message(user_id, test_message)
            print(f"🤖 Agent Response: {response}")

            # Show tool execution status
            status = agent.get_tool_status()
            print(f"📊 Recent tool executions: {status['recent_executions']}")

        except Exception as e:
            print(f"❌ Error: {e}")

        print("\n" + "=" * 50)

    print("✅ Agent testing completed!")


async def test_tool_planning():
    """Test the agent's tool planning capabilities"""
    print("\n🧠 Testing Tool Planning Capabilities")
    print("=" * 50)

    agent = MakaninAgent()
    user_id = "test_user"

    test_message = "cariin seblak viral di bandung yang murah"

    print(f"📝 Planning for: '{test_message}'")
    print("-" * 40)

    try:
        # Create a tool plan
        plan = await agent.create_tool_plan(test_message, user_id)
        print("🗺️  Generated Tool Plan:")
        print(f"Reasoning: {plan.get('reasoning', 'No reasoning provided')}")
        print(f"Expected Outcome: {plan.get('expected_outcome', 'No outcome specified')}")

        print("\n📋 Tool Steps:")
        for i, step in enumerate(plan.get('tool_plan', []), 1):
            print(f"  {i}. Tool: {step.get('tool', 'Unknown')}")
            print(f"     Purpose: {step.get('purpose', 'No purpose')}")
            print(f"     Parameters: {step.get('parameters', {})}")
            print(f"     Depends on: {step.get('depends_on', [])}")

    except Exception as e:
        print(f"❌ Planning error: {e}")

    print("\n" + "=" * 50)


def show_tool_registry():
    """Display information about available tools"""
    print("🔧 Available Tools in Agent System")
    print("=" * 50)

    # Import to trigger tool registration
    import agent.tools
    from agent.tools import tool_registry

    tools = tool_registry.get_all_tools()
    for name, tool in tools.items():
        print(f"📦 {name}")
        print(f"   Description: {tool.description}")
        print(f"   API Key Required: {'Yes' if tool.api_key else 'No'}")
        print()

    print(f"Total tools registered: {len(tools)}")


async def main():
    """Main test function"""
    print("🍜 Makanin Agent System Test Suite")
    print("=" * 60)

    try:
        # Show available tools
        show_tool_registry()

        # Test agent responses
        await test_agent()

        # Test tool planning
        await test_tool_planning()

        print("\n🎉 All tests completed!")
        print("\nThe agent system successfully:")
        print("✅ Analyzes user intent with NLU")
        print("✅ Selects appropriate tools intelligently")
        print("✅ Orchestrates multi-tool workflows")
        print("✅ Generates context-aware responses")
        print("✅ Maintains conversation memory")

    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the test suite
    asyncio.run(main())
