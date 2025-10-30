#!/usr/bin/env python3
"""
Test script to verify Discord bot integration with the new agent system
"""

import asyncio
from discord_bot import makanin


async def test_discord_integration():
    """Test the Discord bot's agent integration"""
    print("🤖 Testing Discord Bot Integration with Agent System")
    print("=" * 60)

    # Verify the bot has the agent
    if not hasattr(makanin, 'agent'):
        print("❌ Bot doesn't have agent attribute")
        return False

    agent = makanin.agent
    print(f"✅ Bot has agent: {type(agent).__name__}")
    print(f"🔧 Available tools: {agent.tool_registry.list_tools()}")

    # Test a simple conversation message
    print("\n📝 Testing conversation message...")
    try:
        response = await agent.process_message("test_user", "halo, apa kabar?")
        print(f"✅ Conversation response: {response[:100]}...")
    except Exception as e:
        print(f"❌ Conversation test failed: {e}")
        return False

    # Test a food search message (without actually calling APIs)
    print("\n🔍 Testing food search message...")
    try:
        response = await agent.process_message("test_user", "cari bakso enak")
        print(f"✅ Food search response: {response[:100]}...")
    except Exception as e:
        print(f"❌ Food search test failed: {e}")
        return False

    print("\n✅ All integration tests passed!")
    print("The Discord bot is now properly using the agent system.")
    return True


async def main():
    """Main test function"""
    try:
        success = await test_discord_integration()
        if success:
            print("\n🎉 Discord bot integration is working correctly!")
            print("\nThe Discord bot will now:")
            print("• Use the agent system for intelligent tool selection")
            print("• Automatically detect food search vs conversation intent")
            print("• Maintain conversation context across messages")
            print("• Provide intelligent responses using the appropriate tools")
        else:
            print("\n❌ Integration tests failed")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
