#!/usr/bin/env python3
"""
Script to clear Redis chat history for Makanin bot
Usage:
  python clear_redis.py                    # Clear all user data
  python clear_redis.py --user-id 12345    # Clear specific user data
  python clear_redis.py --list-users       # List all users
"""

import argparse
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.redis_memory import RedisMemoryBackend
from agent.memory import ContextManager


def clear_all_users():
    """Clear all user data from Redis"""
    print("🧹 Clearing ALL user data from Redis...")

    redis_backend = RedisMemoryBackend()
    if not redis_backend.is_connected():
        print("❌ Failed to connect to Redis")
        return False

    # Get all user IDs
    user_ids = redis_backend.get_all_user_ids()
    print(f"Found {len(user_ids)} users: {user_ids}")

    success_count = 0
    for user_id in user_ids:
        if redis_backend.clear_all_user_data(user_id):
            print(f"✅ Cleared data for user {user_id}")
            success_count += 1
        else:
            print(f"❌ Failed to clear data for user {user_id}")

    print(f"\n🎉 Cleared data for {success_count}/{len(user_ids)} users")
    return success_count == len(user_ids)


def clear_specific_user(user_id: str):
    """Clear data for a specific user"""
    print(f"🧹 Clearing data for user {user_id}...")

    redis_backend = RedisMemoryBackend()
    if not redis_backend.is_connected():
        print("❌ Failed to connect to Redis")
        return False

    if redis_backend.clear_all_user_data(user_id):
        print(f"✅ Cleared all data for user {user_id}")
        return True
    else:
        print(f"❌ Failed to clear data for user {user_id}")
        return False


def clear_conversation_only(user_id: str):
    """Clear only conversation history for a specific user"""
    print(f"🧹 Clearing conversation history for user {user_id}...")

    redis_backend = RedisMemoryBackend()
    if not redis_backend.is_connected():
        print("❌ Failed to connect to Redis")
        return False

    if redis_backend.clear_conversation(user_id):
        print(f"✅ Cleared conversation history for user {user_id}")
        return True
    else:
        print(f"❌ Failed to clear conversation for user {user_id}")
        return False


def list_users():
    """List all users in Redis"""
    print("📋 Listing all users in Redis...")

    redis_backend = RedisMemoryBackend()
    if not redis_backend.is_connected():
        print("❌ Failed to connect to Redis")
        return

    user_ids = redis_backend.get_all_user_ids()

    if not user_ids:
        print("📭 No users found in Redis")
        return

    print(f"Found {len(user_ids)} users:")
    for i, user_id in enumerate(user_ids, 1):
        # Get session info
        session = redis_backend.get_user_session(user_id)
        if session:
            print(f"  {i}. User {user_id}")
            print(f"     Language: {session.language}")
            print(f"     Last Intent: {session.last_intent}")
            print(f"     Created: {session.created_at}")
        else:
            print(f"  {i}. User {user_id} (no session data)")
        print()


def main():
    parser = argparse.ArgumentParser(description="Clear Redis chat history for Makanin bot")
    parser.add_argument("--user-id", help="Clear data for specific user ID")
    parser.add_argument("--conversation-only", action="store_true",
                        help="Clear only conversation history (keep session data)")
    parser.add_argument("--list-users", action="store_true",
                        help="List all users in Redis")
    parser.add_argument("--all", action="store_true",
                        help="Clear all user data (default behavior)")

    args = parser.parse_args()

    print("=" * 60)
    print("🍽️  Makanin Bot - Redis Chat History Cleaner")
    print("=" * 60)

    try:
        if args.list_users:
            list_users()
        elif args.user_id:
            if args.conversation_only:
                clear_conversation_only(args.user_id)
            else:
                clear_specific_user(args.user_id)
        else:
            # Default: clear all users
            confirm = input("⚠️  This will delete ALL user data from Redis. Continue? (y/N): ")
            if confirm.lower() in ['y', 'yes']:
                clear_all_users()
            else:
                print("❌ Cancelled")

    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
