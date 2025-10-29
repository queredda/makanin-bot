"""
Main entry point for Makanin bot.
Starts an interactive chat session.
"""

from bot import MakaninBot
import config


def main():
    """Run the Makanin bot in interactive mode"""
    print("\n" + "="*60)
    print("Welcome to Makanin - Your Viral Food Finder Bot!")
    print("="*60)
    print("\nTalk naturally to find viral food spots:")
    print("  - Bahasa Indonesia: 'Cariin bakso viral deket UGM dong'")
    print("  - English: 'Find me good ramen near campus'")
    print("\nType 'exit' to quit.\n")

    # Initialize bot
    bot = MakaninBot()

    # Interactive chat loop
    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "keluar", "bye"]:
                print("\nTerima kasih! Sampai jumpa! (Thanks for using Makanin!)\n")
                break

            # Get bot response
            response = bot.chat(user_input)
            print(f"\nMakanin: {response}\n")

        except KeyboardInterrupt:
            print("\n\nTerima kasih! Sampai jumpa!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please check your API keys and try again.\n")


if __name__ == "__main__":
    main()
