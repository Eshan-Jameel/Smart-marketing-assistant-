import analysis_engine
import generation_engine
import ollama
import json
import sys

# --- CONFIGURATION ---
# Use a real URL that's simple to scrape. GitHub's main page is perfect.
TEST_URL_CLIENT = "https://github.com" 

# For your own site, a fake URL is fine since we're just testing the prompt
TEST_URL_SELF = "https://cyforge.com" 
TEST_DESC_SELF = "We are CyForge. We sell AI-powered cybersecurity audits and automated code-fixing for SaaS and FinTech companies."
# --- END CONFIGURATION ---

def check_ollama():
    """Checks if the Ollama server is running."""
    print("Checking Ollama connection...")
    try:
        ollama.list()
        print("✅ Ollama is running.\n")
        return True
    except Exception:
        print("❌ FATAL: Ollama server is NOT running.")
        print("Please start the Ollama application, then run this test again.")
        return False

def test_analysis():
    """Tests the analyze_my_business function."""
    print("--- 1. Testing analyze_my_business() ---")
    services = analysis_engine.analyze_my_business(TEST_URL_SELF, TEST_DESC_SELF)
    if not services or not isinstance(services, str):
         print(f"❌ FAILED: analyze_my_business returned: {services}")
         sys.exit(1)
    print(f"✅ Success. Got services: {services}\n")
    return services

def test_client_analysis():
    """Tests the analyze_client function."""
    print(f"--- 2. Testing analyze_client() on {TEST_URL_CLIENT} ---")
    client_info = analysis_engine.analyze_client(TEST_URL_CLIENT)
    
    # This is the check that would have caught your bug
    if not client_info:
        print(f"❌ FAILED: analyze_client returned None.")
        sys.exit(1)
    if not isinstance(client_info, dict):
        print(f"❌ FAILED: analyze_client returned a {type(client_info)}, not a dictionary.")
        print("Did you remember to add 'import json' and 'json.loads()' in analysis_engine.py?")
        sys.exit(1)
        
    assert 'summary' in client_info, "client_info is missing 'summary' key"
    assert 'industry' in client_info, "client_info is missing 'industry' key"
    
    print(f"✅ Success. Got client info (as a dictionary):")
    print(json.dumps(client_info, indent=2))
    print("\n")
    return client_info

def test_email_gen(my_services, client_info):
    """Tests the generate_email function."""
    print("--- 3. Testing generate_email() ---")
    
    # This is where your previous error happened
    email = generation_engine.generate_email(my_services, client_info)
    
    if not email or not isinstance(email, str):
         print(f"❌ FAILED: generate_email returned: {email}")
         sys.exit(1)
         
    assert "Eshan Jameel" in email, "Email signature is missing!"
    
    # Check if it's using the info
    if client_info.get('industry') and client_info['industry'] not in email:
        print("⚠️ Warning: Email doesn't seem to mention the client's industry.")
        
    print("✅ Success. Got email draft:")
    print("--------------------")
    print(email)
    print("--------------------")

# --- RUN THE TESTS ---
if __name__ == "__main__":
    if check_ollama():
        try:
            services = test_analysis()
            client_info = test_client_analysis()
            test_email_gen(services, client_info)
            
            print("\n🎉 All Person 3 tests passed! Your code is solid.")
            print("You are clear to push your code and tell Person 1 you are ready for integration.")
        
        except AssertionError as e:
            print(f"\n❌ TEST FAILED: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ UNEXPECTED CRASH: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)