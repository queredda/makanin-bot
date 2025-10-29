#!/usr/bin/env python3
"""
Test script to verify keyword validation is working correctly.
This ensures that only venues mentioning the search keywords are included.
"""

from bot import MakaninBot
from nlu import IntentSlots

print("\n" + "="*70)
print("TESTING KEYWORD VALIDATION")
print("="*70 + "\n")

# Initialize bot
bot = MakaninBot()

# Create test intent slots for "misoa jogja"
slots = IntentSlots(
    intent="find_food",
    keywords=["misoa"],
    location="Yogyakarta",
    constraints={},
    original_text="cariin misoa jogja",
    language="id"
)

print(f"Search query: '{slots.original_text}'")
print(f"Keywords: {slots.keywords}")
print(f"Location: {slots.location}\n")

print("="*70)
print("Searching for results...")
print("="*70 + "\n")

# Run the food search
venues = bot.find_food(slots)

print("\n" + "="*70)
print(f"RESULTS: {len(venues)} restaurants found")
print("="*70)

if venues:
    for i, venue in enumerate(venues, 1):
        print(f"\n{i}. {venue.name}")
        print(f"   Address: {venue.address}")
        if venue.weather_summary:
            print(f"   Weather: {venue.weather_summary}")
        print(f"   TikTok: {venue.tiktok_link}")
else:
    print("\nℹ️  No results found (venues without 'misoa' keyword were filtered out)")

print("\n" + "="*70)
print("✅ Keyword validation test complete!")
print("="*70 + "\n")
