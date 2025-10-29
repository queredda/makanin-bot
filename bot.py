

import google.generativeai as genai
from typing import List, Optional
from nlu import NLUEngine, IntentSlots
from api_clients import (
    EnsembleDataClient,
    GoogleMapsClient,
    OpenWeatherClient,
    FoodVenue,
)
import config
from concurrent.futures import ThreadPoolExecutor


class MakaninBot:
    """Main bot class that orchestrates all components"""

    def __init__(self):
        # Initialize NLU with Gemini API key
        self.nlu = NLUEngine(api_key=config.GEMINI_API_KEY)

        # NLU caching to speed up repeated searches
        self.nlu_cache = {}

        # Initialize API clients
        self.ensemble = EnsembleDataClient(token=config.ENSEMBLE_DATA_TOKEN)
        self.maps = GoogleMapsClient(api_key=config.GOOGLE_MAPS_API_KEY)
        self.weather = OpenWeatherClient(api_key=config.OPENWEATHER_API_KEY)

        # Initialize Gemini for conversation and place name extraction
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.gemini_model = genai.GenerativeModel(config.GEMINI_MODEL)

        # Conversation history for multi-turn context
        self.conversation_history = []

    def extract_place_name_from_tiktok(self, tiktok_description: str, keywords: Optional[List[str]] = None) -> Optional[str]:
        import re

        if not tiktok_description:
            return None

        # METHOD 1: Try extracting names after @ or 📍 symbols (most reliable)
        print(f"  [Extracting] Trying pattern matching...")

        # Look for @NAME pattern (e.g., @KEDAI QIU QIU 99)
        # This handles both standalone @ and @ after 📍
        at_pattern = r'@([A-Za-z0-9\s\-\.]+?)(?:\s{2,}|📍|#|$)'
        at_matches = re.findall(at_pattern, tiktok_description)

        # Also try more aggressive pattern for @NAME
        at_pattern_aggressive = r'@\s*([A-Za-z0-9\s\-\.]+?)(?:\s+#|$)'
        at_matches_aggressive = re.findall(at_pattern_aggressive, tiktok_description)
        at_matches.extend(at_matches_aggressive)

        # Look for 📍NAME or 📍@NAME pattern (e.g., 📍KEDAI QIU QIU 99 or 📍@KEDAI QIU QIU 99)
        pin_pattern = r'📍\s*@?\s*([A-Za-z0-9\s\-\.\(\)]+?)(?:\s{2,}|#|$)'
        pin_matches = re.findall(pin_pattern, tiktok_description)

        # Extract hashtags that might contain food keywords
        hashtag_pattern = r'#([A-Za-z0-9\u0600-\u06FF]+)'
        hashtags = re.findall(hashtag_pattern, tiktok_description)
        hashtags_lower = [h.lower() for h in hashtags]

        print(f"  [Hashtags found] {hashtags_lower}")

        candidates = []

        # Add @NAME matches
        for match in at_matches:
            name = match.strip()
            if len(name) > 2:
                candidates.append(name)
                print(f"    [@match] {name}")

        # Add 📍NAME matches
        for match in pin_matches:
            name = match.strip() if isinstance(match, str) else match
            if name and len(name) > 2:
                candidates.append(name)
                print(f"    [📍match] {name}")

        print(f"  [Candidates from patterns] {candidates}")

        # Filter candidates using keywords and hashtags
        for candidate in candidates:
            if self._validate_venue_name(candidate, keywords, hashtags_lower, tiktok_description):
                print(f"  ✅ [Pattern match] Found: {candidate}")
                return candidate

        # METHOD 2: Try Gemini extraction if patterns didn't work
        print(f"  [Extracting] Trying Gemini AI...")

        keyword_hint = ""
        if keywords:
            keyword_list = ", ".join(keywords)
            keyword_hint = f"""\nIMPORTANT: The venue MUST be related to these search keywords: {keyword_list}
If NOT about food matching these keywords, return "Not found"."""

        prompt = f"""Extract the ACTUAL RESTAURANT or FOOD VENUE NAME from this TikTok description.

PRIORITY - Look for names in this order:
1. Names directly after 📍 symbol (e.g., 📍@RESTAURANT NAME or 📍RESTAURANT NAME)
2. Names after @ symbol (e.g., @RESTAURANT NAME)
3. Restaurant names in descriptive text mentioning the venue
4. Restaurant names in hashtags (e.g., #restaurantname or #misoaqiuqiu99)
5. If description is very sparse/minimal, extract ANY restaurant-like name from hashtags

Important Rules:
- Look for ALL CAPS or Title Case names which are often restaurant names
- Include numbers in the name (e.g., "QIU QIU 99" not just "QIU QIU")
- Return EXACTLY as it appears (preserve capitalization and spacing)
- DO NOT simplify or shorten names
- DO NOT return creator names, generic hashtags (fyp, viral, etc), or generic words
- If description is minimal (just hashtags or few words), do your best to extract a plausible restaurant name from the text
- If truly impossible to extract any restaurant name, return "Not found"
- If found, return the exact name only - nothing else{keyword_hint}

Description: {tiktok_description}

Return ONLY the restaurant name (or "Not found"):"""

        try:
            response = self.gemini_model.generate_content(prompt)
            place_name = response.text.strip()

            # Filter out low-quality results
            if not place_name or place_name.lower() == "not found":
                print(f"  ❌ [Gemini] No result")
                return None

            # Validate the result
            if self._validate_venue_name(place_name, keywords, hashtags_lower, tiktok_description):
                print(f"  ✅ [Gemini] Found: {place_name}")
                return place_name
            else:
                print(f"  ❌ [Gemini] Validation failed: {place_name}")
                return None

        except Exception as e:
            print(f"  ❌ [Gemini] Error: {e}")

        # METHOD 3: Try extracting from hashtags as last resort
        print(f"  [Extracting] Trying hashtags as fallback...")

        # Look for hashtags that might be restaurant names (longer hashtags, not generic ones)
        generic_hashtags = ["fyp", "fyppppppppppppppppppppppp", "viral", "jogjafood", "kulinerjogja", "baksojogja",
                          "makananjogja", "kulinerviral", "infojogja", "makanananakkos", "jogjaistimewa"]

        candidate_hashtags = [
            tag for tag in hashtags_lower
            if len(tag) > 4 and tag not in generic_hashtags and not tag.startswith("fyp")
        ]

        print(f"  [Hashtag candidates] {candidate_hashtags}")

        for hashtag in candidate_hashtags:
            # Convert hashtag to potential restaurant name
            # e.g., "rmkhasjogja" -> "RM Khas Jogja"
            potential_name = hashtag.replace("jogja", "").replace("resto", "").replace("rm", "").strip()

            if potential_name and len(potential_name) > 2:
                # Capitalize nicely
                formatted_name = " ".join([word.capitalize() for word in potential_name.split()])

                if self._validate_venue_name(formatted_name, keywords, hashtags_lower, tiktok_description):
                    print(f"[Hashtag fallback] Found: {formatted_name}")
                    return formatted_name

        print(f"[All methods] Could not extract restaurant name")
        return None

    def _validate_venue_name(self, name: str, keywords: Optional[List[str]], hashtags: List[str], description: str) -> bool:
        """Validate if a name looks like a real venue name"""
        if not name or len(name) < 2:
            return False

        # Skip if it's obviously a username
        if name.startswith("@") or name.startswith("_"):
            return False

        # Skip if too short
        if len(name) < 3:
            return False

        # Skip known non-food terms
        non_food_keywords = ["disini", "pong", "fashion", "brand", "follow", "like", "share"]
        name_lower = name.lower()
        for keyword in non_food_keywords:
            if keyword in name_lower:
                return False

        # Check if name appears in description (basic sanity check)
        if name not in description and name.lower() not in description.lower():
            pass

        # If keywords provided, MUST validate against them
        if keywords:
            desc_lower = description.lower()
            hashtags_lower = [h.lower() for h in hashtags]

            # Check if any keyword appears in description or hashtags
            has_keywords = any(
                kw.lower() in desc_lower or any(kw.lower() in tag for tag in hashtags_lower)
                for kw in keywords
            )

            if not has_keywords:
                # Keywords provided but NOT found in description/hashtags
                # This venue is not relevant to the search - skip it
                return False

        return True

    def resolve_venue_location(self, venue: FoodVenue, keywords: Optional[List[str]] = None) -> Optional[dict]:
        # Use the venue name (already extracted from TikTok description) for search
        search_query = venue.name

        # Google Maps text search
        results = self.maps.text_search(search_query)
        if not results:
            return None

        # Get the top result
        top_result = results[0]
        place_id = top_result.get("place_id")

        # Get detailed place info
        details = self.maps.get_place_details(place_id)
        if not details or "geometry" not in details:
            return None

        location = details["geometry"]["location"]
        lat = location["lat"]
        lng = location["lng"]

        # Generate share link
        share_link = self.maps.get_share_link(lat, lng, venue.name)

        return {
            "lat": lat,
            "lng": lng,
            "address": details.get("formatted_address"),
            "maps_link": share_link,
        }

    def find_food(self, slots: IntentSlots) -> List[FoodVenue]:
        # Step 1: Search Ensemble Data
        print("\n" + "="*60)
        print("FOOD SEARCH DEBUG")
        print("="*60)
        print(f"Keywords: {slots.keywords}")
        print(f"Location: {slots.location}")
        print(f"Constraints: {slots.constraints}")

        results = self.ensemble.search(
            keywords=slots.keywords,
            location=slots.location,
            constraints=slots.constraints
        )

        print(f"Ensemble Data returned: {len(results) if results else 0} results")

        if not results:
            print("No results from Ensemble Data API")
            return []

        venues = []
        skipped_count = 0

        for idx, result in enumerate(results[:config.MAX_RESULTS]):
            print(f"\n--- Processing result {idx + 1} ---")

            # Step 2: Extract actual restaurant name from TikTok description BEFORE creating venue
            tiktok_description = result.get("tiktok_description", "")
            print(f"TikTok desc: {tiktok_description[:80]}..." if len(tiktok_description) > 80 else f"TikTok desc: {tiktok_description}")

            extracted_place = self.extract_place_name_from_tiktok(
                tiktok_description,
                keywords=slots.keywords
            )

            # Skip if we couldn't extract a valid restaurant name
            if not extracted_place:
                print("Skipped: Could not extract restaurant name")
                skipped_count += 1
                continue

            # Validate that keywords match (if keywords were provided)
            if slots.keywords:
                desc_lower = tiktok_description.lower()
                hashtags = result.get("hashtags", [])
                hashtags_lower = [h.lower() for h in hashtags] if hashtags else []

                has_keywords = any(
                    kw.lower() in desc_lower or any(kw.lower() in tag for tag in hashtags_lower)
                    for kw in slots.keywords
                )

                if not has_keywords:
                    print(f"Skipped: No keywords {slots.keywords} found in description or hashtags")
                    skipped_count += 1
                    continue

            print(f"Extracted: {extracted_place}")

            venue = FoodVenue(
                id=result.get("id", ""),
                name=extracted_place,  # Use extracted restaurant name, not creator name
                description=result.get("description", ""),
                tiktok_link=result.get("tiktok_link"),
                tiktok_description=tiktok_description,
            )

            # Step 3-4: Resolve location via Google Maps (with parallel weather fetch)
            # Use ThreadPoolExecutor to fetch Maps and Weather in parallel
            with ThreadPoolExecutor(max_workers=2) as executor:
                # Submit both tasks concurrently
                maps_future = executor.submit(self.resolve_venue_location, venue, slots.keywords)

                # We need latitude/longitude for weather, so wait for maps first
                location_data = maps_future.result()

            if not location_data:
                print(f"⏭️  Skipped: Google Maps could not find '{extracted_place}'")
                skipped_count += 1
                continue  # Skip if location cannot be resolved

            print(f"📍 Found on Maps: {location_data.get('address', 'Unknown')}")

            venue.latitude = location_data["lat"]
            venue.longitude = location_data["lng"]
            venue.address = location_data["address"]
            venue.maps_link = location_data["maps_link"]

            # Step 5: Fetch weather in parallel with next venue processing
            # For now, fetch sequentially but it's fast
            weather_info = self.weather.get_current_weather(venue.latitude, venue.longitude)
            if weather_info:
                venue.weather_summary = self.weather.format_weather_summary(
                    weather_info,
                    language=slots.language
                )
                print(f"Weather: {venue.weather_summary}")

            venues.append(venue)
            print(f"Added venue: {venue.name}")

        print(f"\nFinal result: {len(venues)} venues found, {skipped_count} skipped")
        print("="*60 + "\n")

        return venues

    def format_response(self, venues: List[FoodVenue], slots: IntentSlots) -> str:
        """Format the venues into a friendly, readable response"""
        if not venues:
            if slots.language == "id":
                return "Hmm... kayaknya belum ada yang cocok nih 🤔 Mau coba cari di area lain? Bisa juga dengan keyword yang berbeda! 😊"
            else:
                return "Hmm... looks like I couldn't find anything matching that! 🤔 Try a different area or keyword? 😊"

        response = ""
        if slots.language == "id":
            response += "🎉 Yay! Aku nemuin beberapa pilihan viral yang kelihatannya enak banget!\n\n"
        else:
            response += "🎉 Found some delicious viral spots for you! Here you go:\n\n"

        for i, venue in enumerate(venues, 1):
            response += f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            response += f"#{i} 🍽️  {venue.name}\n"

            if venue.address:
                response += f"📍 {venue.address}\n"

            if venue.weather_summary:
                if slots.language == "id":
                    response += f"🌤️  Cuaca: {venue.weather_summary}\n"
                else:
                    response += f"🌤️  Weather: {venue.weather_summary}\n"

            if venue.maps_link:
                response += f"🗺️  Maps: {venue.maps_link}\n"

            if venue.tiktok_link:
                response += f"🎥 Viral di TikTok: {venue.tiktok_link}\n"

            response += "\n"

        response += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        if slots.language == "id":
            response += "✨ Selamat menikmati! Jangan lupa share pengalamanmu ya! 😋"
        else:
            response += "✨ Enjoy your meal! Don't forget to share your experience! 😋"

        return response

    def chat(self, user_message: str) -> str:
        """
        Main chat method. Handles both food-finding and general conversation.
        """
        # Parse user input with NLU (with caching for speed)
        if user_message in self.nlu_cache:
            print(f"[NLU Cache] Hit - using cached result for: '{user_message}'")
            slots = self.nlu_cache[user_message]
        else:
            slots = self.nlu.parse_user_input(user_message)
            self.nlu_cache[user_message] = slots

        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Handle food-finding intent
        if slots.intent == "find_food":
            venues = self.find_food(slots)
            response = self.format_response(venues, slots)
        else:
            # General conversation via Gemini
            system_prompt = """You are Makanin, a super friendly and enthusiastic food-finder bot! 🍜✨

Your personality:
- You're warm, engaging, and genuinely excited about food!
- Use emojis naturally and appropriately to make conversations fun
- Be conversational, brief, and always helpful
- Mirror the user's language (Indonesian or English) perfectly
- You're knowledgeable about food culture and viral food trends
- You make food recommendations sound amazing and irresistible!

When users ask about food:
- Share your enthusiasm with lots of encouragement!
- Suggest they search using specific keywords like 'cariin bakso viral' or 'find me good ramen near campus'
- If they mention specific foods or areas, help them discover viral spots
- Use phrases like "Ooh, bagus banget pilihan!" or "That sounds delicious!"

Tone examples:
- Be casual and friendly, like chatting with a food-loving friend
- Use warm greetings and encourage them to explore
- If they have questions, answer helpfully with personality
- Always end conversations on a positive note about food!"""

            try:
                # Build conversation context for Gemini
                conversation_text = ""
                for msg in self.conversation_history[:-1]:  # All messages except the current one
                    if msg["role"] == "user":
                        conversation_text += f"User: {msg['content']}\n"
                    else:
                        conversation_text += f"Makanin: {msg['content']}\n"

                # Build final prompt for Gemini
                final_prompt = f"""{system_prompt}

Previous conversation:
{conversation_text}

User: {user_message}

Makanin:"""

                # Call Gemini with the formatted prompt
                response_obj = self.gemini_model.generate_content(final_prompt)
                response = response_obj.text.strip()
            except Exception as e:
                print(f"Error in Gemini chat: {e}")
                import traceback
                traceback.print_exc()
                if slots.language == "id":
                    response = "Ah sorry! Terjadi kesalahan nih 😅 Bisa coba lagi? Terimakasih! 😊"
                else:
                    response = "Oops! Something went wrong there 😅 Can you try again? Thanks! 😊"

        # Add bot response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })

        return response
