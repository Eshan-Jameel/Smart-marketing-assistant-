import requests
from bs4 import BeautifulSoup
import ollama
import json  # <-- This is the new, critical import

def _get_text_from_url(url: str) -> str | None:
    """
    Fetches a URL and returns all visible, stripped text.
    Returns None if the request fails.
    """
    try:
        # Set a user-agent to look like a real browser, not a script
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        
        # This will raise an error for 4xx or 5xx responses
        response.raise_for_status() 
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Kill all script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        
        # Get all text, strip whitespace from each piece, and join with a space
        text = " ".join(t.strip() for t in soup.stripped_strings)
        return text

    except requests.exceptions.RequestException as e:
        print(f"Error (Person 3): Failed to scrape {url}. Error: {e}")
        return None

def analyze_my_business(url: str, description: str) -> str:
    """
    Analyzes the user's own site to extract key B2B services.
    """
    print(f"Analyzing our business at {url}...")
    text = _get_text_from_url(url)
    
    if not text:
        print("Warning (Person 3): Scraping our URL failed. Falling back to user description.")
        # Fallback to the user's description if scraping fails
        return description 
    
    # Combine scraped text with the user's description for more context
    # Limit text to avoid exceeding model context
    full_context = f"User Description: {description}\n\nWebsite Text: {text[:4000]}"
    
    prompt = f"""
    Given the following context about a B2B company, identify and list 
    its 3-5 most important, client-facing services.
    Return ONLY a comma-separated list (e.g., AI Audits, Compliance-as-a-Service, DevSecOps).

    Context:
    {full_context}
    """
    
    try:
        response = ollama.chat(
            model='llama3:8b', 
            messages=[{'role': 'user', 'content': prompt}]
        )
        return response['message']['content']
    except Exception as e:
        print(f"Error (Person 3): Ollama call failed in analyze_my_business. {e}")
        # If AI fails, just return the basic description
        return description

def analyze_client(url: str) -> dict | None:
    """
    Analyzes a potential client's website.
    Returns a dictionary with their summary and industry, or None.
    """
    print(f"Analyzing client: {url}...")
    text = _get_text_from_url(url)
    if not text:
        return None # If scraping fails, we can't analyze.
    
    # A "system prompt" tells the AI what its job is
    system_prompt = "You are a concise B2B market analyst. Your job is to extract key information from a company's website text. You must only output a valid JSON object."
    
    # We'll ask for two things at once for efficiency
    user_prompt = f"""
    Analyze the following website text and provide two pieces of information:
    1.  **summary**: A one-sentence summary of what this company does.
    2.  **industry**: The company's primary industry (e.g., "FinTech", "SaaS", "Healthcare", "E-commerce", "Manufacturing").

    Return your answer *only* as a single, valid JSON object, like this:
    {{"summary": "...", "industry": "..."}}

    Website Text:
    {text[:4000]}
    """
    
    try:
        response = ollama.chat(
            model='llama3:8b', 
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            format='json' # This tells Ollama to *force* JSON output
        )
        
        # --- THIS IS THE FIX ---
        # 1. Get the raw JSON string from the AI
        json_string = response['message']['content']
        
        # 2. Convert (parse) the JSON string into a real Python dictionary
        return json.loads(json_string) 
        # --- END OF FIX ---
        
    except json.JSONDecodeError:
        print(f"Error (Person 3): AI did not return valid JSON for {url}")
        return None
    except Exception as e:
        print(f"Error (Person 3): Ollama call failed in analyze_client. {e}")
        return None