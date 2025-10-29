"""
Test script for Gemini-based NLU module.
Tests the new NLU that uses Gemini API for intelligent parsing.
"""

from nlu import NLUEngine
import config


def test_nlu():
    """Test NLU intent and slot extraction with Gemini API"""
    nlu = NLUEngine(api_key=config.GEMINI_API_KEY)

    test_cases = [
        # Food finding intent - Indonesian
        {
            "input": "Cariin bakso viral deket UGM dong",
            "expected_intent": "find_food",
            "expected_location": "UGM",
        },
        {
            "input": "Carin soto murah di Malioboro",
            "expected_intent": "find_food",
            "expected_location": "Malioboro",
        },
        {
            "input": "hunting makanan halal deket kampus",
            "expected_intent": "find_food",
        },
        # Food finding intent - English
        {
            "input": "Find me good ramen near campus",
            "expected_intent": "find_food",
        },
        {
            "input": "recommend budget-friendly restaurants",
            "expected_intent": "find_food",
        },
        # General chat
        {
            "input": "Halo, apa kabar?",
            "expected_intent": "chat",
        },
        {
            "input": "What's your favorite food?",
            "expected_intent": "chat",
        },
    ]

    print("Testing NLU Module")
    print("=" * 60)

    for i, test_case in enumerate(test_cases, 1):
        user_input = test_case["input"]
        slots = nlu.parse_user_input(user_input)

        print(f"\nTest {i}: {user_input}")
        print(f"  Intent: {slots.intent} {'✓' if slots.intent == test_case['expected_intent'] else '✗'}")
        print(f"  Keywords: {slots.keywords}")
        print(f"  Location: {slots.location}")
        if "expected_location" in test_case:
            match = slots.location and test_case["expected_location"].lower() in slots.location.lower()
            print(f"    {'✓' if match else '✗'} (expected: {test_case['expected_location']})")
        print(f"  Constraints: {slots.constraints}")
        print(f"  Language: {slots.language}")


def test_constraint_extraction():
    """Test constraint extraction specifically with Gemini"""
    nlu = NLUEngine(api_key=config.GEMINI_API_KEY)

    constraint_tests = [
        ("bakso murah", {"price": "cheap"}),
        ("restaurant mahal", {"price": "expensive"}),
        ("makanan halal", {"halal": True}),
        ("tempat makan buka sekarang", {"open_now": True}),
        ("detek yang bagus", {"nearby": True}),
        ("makanan murah dan halal", {"price": "cheap", "halal": True}),
    ]

    print("\n\nTesting Constraint Extraction")
    print("=" * 60)

    for text, expected_constraints in constraint_tests:
        slots = nlu.parse_user_input(text)
        print(f"\nInput: {text}")
        print(f"  Expected: {expected_constraints}")
        print(f"  Got:      {slots.constraints}")

        # Check if all expected constraints are present
        all_match = all(
            slots.constraints.get(k) == v
            for k, v in expected_constraints.items()
        )
        print(f"  {'✓' if all_match else '✗'} Match")


def test_keyword_extraction():
    """Test food keyword extraction with Gemini"""
    nlu = NLUEngine(api_key=config.GEMINI_API_KEY)

    keyword_tests = [
        "bakso enak",
        "ramen viral",
        "soto ayam murah",
        "makanan jepang halal",
        "restoran fusion bagus",
    ]

    print("\n\nTesting Keyword Extraction")
    print("=" * 60)

    for text in keyword_tests:
        slots = nlu.parse_user_input(text)
        print(f"\nInput: {text}")
        print(f"  Keywords: {slots.keywords}")


def test_language_detection():
    """Test language detection with Gemini"""
    nlu = NLUEngine(api_key=config.GEMINI_API_KEY)

    language_tests = [
        ("Cariin makanan enak dong", "id"),
        ("Cari restoran halal", "id"),
        ("Find me food", "en"),
        ("I want some ramen", "en"),
        ("What's the best place to eat?", "en"),
    ]

    print("\n\nTesting Language Detection")
    print("=" * 60)

    for text, expected_lang in language_tests:
        slots = nlu.parse_user_input(text)
        match = slots.language == expected_lang
        print(f"\nInput: {text}")
        print(f"  Expected: {expected_lang}")
        print(f"  Got:      {slots.language}")
        print(f"  {'✓' if match else '✗'}")


if __name__ == "__main__":
    test_nlu()
    test_constraint_extraction()
    test_keyword_extraction()
    test_language_detection()

    print("\n" + "=" * 60)
    print("NLU Testing Complete!")
    print("=" * 60 + "\n")
