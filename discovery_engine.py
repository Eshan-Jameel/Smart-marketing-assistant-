# marketing-automation-using-csi-main/discovery_engine.py

import os
from serpapi import SerpApiClient
import traceback
from dotenv import load_dotenv # <-- ADD THIS IMPORT

# --- Load environment variables from .env file ---
load_dotenv() # <-- ADD THIS LINE AT THE TOP (after imports)

# --- CONFIGURATION ---
# Now, os.getenv will automatically find the key loaded from .env
SERPAPI_API_KEY = os.getenv("SERPAPI_KEY")
# --- END CONFIGURATION ---


def find_leads(services_str: str, location: str = "United States") -> list[dict]:
    """
    Finds potential B2B client leads for given services using SerpAPI Google Search.

    Args:
        services_str: A comma-separated string of the user's B2B services.
        location: The geographical location to target the search (default: "United States").

    Returns:
        A list of dictionaries, where each dictionary contains the 'name'
        and 'url' of a potential lead, or an empty list if an error occurs or no leads found.
    """

    # Check if the API key was loaded successfully
    if not SERPAPI_API_KEY: # Check if it's None or empty
        print("❌ FATAL ERROR (Person 4): SERPAPI_API_KEY is not set.")
        print("   Ensure you have a .env file in the project root with SERPAPI_KEY=YOUR_KEY")
        return []

    # --- Generate a Search Query ---
    try:
        first_service = services_str.split(',')[0].strip()
        if not first_service:
             raise IndexError("Service string was empty or malformed.")
        query = f"companies needing {first_service}"
    except IndexError:
        print("Error (Person 4): Could not parse services string to create query.")
        return []
    except Exception as e:
        print(f"Error (Person 4): Unexpected issue creating query from '{services_str}'. Error: {e}")
        return []

    print(f"🔎 Searching SerpAPI for: '{query}' in '{location}'...")

    # --- Prepare API Parameters ---
    params = {
        "engine": "google",
        "q": query,
        "location": location,
        "google_domain": "google.com",
        "gl": "us",
        "hl": "en",
        "num": 10,
        "api_key": SERPAPI_API_KEY
    }

    # --- Call SerpAPI ---
    try:
        client = SerpApiClient(params_dict=params)
        results = client.get_dict()

        if "error" in results:
            print(f"❌ SerpAPI returned an error: {results['error']}")
            # Provide specific feedback for common API key issues
            if "invalid API key" in results['error'].lower():
                 print("   Hint: Double-check the SERPAPI_KEY value in your .env file.")
            elif "exceeded your credits" in results['error'].lower():
                 print("   Hint: You may have used up your free SerpAPI credits for the month.")
            return []

        organic_results = results.get("organic_results", [])

        leads = []
        for result in organic_results:
            link = result.get("link")
            title = result.get("title")

            if link and title and link.startswith('http'):
                 leads.append({
                    "name": title,
                    "url": link
                 })

        if leads:
            print(f"✅ Found {len(leads)} potential leads via SerpAPI.")
        else:
             print("⚠️ No organic results found for this query in SerpAPI response.")

        return leads

    except Exception as e:
        print(f"❌ CRITICAL ERROR (Person 4) during SerpAPI call/processing: {e}")
        traceback.print_exc()
        return []

# --- Example Usage Block (for testing this file directly) ---
if __name__ == '__main__':
    print("--- Testing discovery_engine.py (using .env) ---")

    if not SERPAPI_API_KEY:
         print("Cannot run test: SERPAPI_KEY not found. Check your .env file.")
    else:
        test_services = "AI Code Vulnerability Audits, Automated DevSecOps Integration, Compliance-as-a-Service"
        test_location = "California, United States"

        found_leads = find_leads(test_services, location=test_location)

        if found_leads:
            print("\n--- Example Leads Found ---")
            for i, lead in enumerate(found_leads[:5]):
                print(f"{i+1}. Name: {lead.get('name')}")
                print(f"   URL:  {lead.get('url')}\n")
        else:
            print("\n--- No leads found in test run (Check API key in .env and SerpAPI credits). ---")