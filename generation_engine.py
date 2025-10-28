import ollama
def generate_email(my_services: str, client_info: dict) -> str:
    """
    Generates a personalized B2B outreach email.

    my_services: A comma-separated string of our services (from analyze_my_business).
    client_info: The dict from analyze_client ({"summary": "...", "industry": "..."}).
    """
    print(f"Drafting email for industry: {client_info.get('industry')}...")

    system_prompt = """
    You are "CyForge", a senior B2B cybersecurity expert. 
    You are writing a *short*, concise, and professional cold outreach email.
    Your tone is confident, expert, and helpful, not "salesy".
    DO NOT use buzzwords like "revolutionize" or "unlock".
    Your goal is to get a reply.
    """

    user_prompt = f"""
    I need to write a cold email to a potential client.

    **My Company's Services:**
    {my_services}

    **Client Information:**
    - **Business Summary:** {client_info.get('summary')}
    - **Industry:** {client_info.get('industry')}

    **Instructions:**
    1.  Start with a *brief* observation about their company/industry (e.g., "As a leader in the FinTech space...").
    2.  Identify a *specific, implied pain point* for their industry (e.g., FinTech needs compliance; SaaS needs speed).
    3.  Connect ONE of my services directly to that *exact* pain point.
    4.  Keep the email to 3-4 short paragraphs.
    5.  End with a single, clear call to action (e.g., "Are you free for a 15-minute call next week?").
    6.  Sign off as "Eshan Jameel, Co-founder, CyForge".

    Draft the email.
    """

    response = ollama.chat(
        model='llama3:8b',
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]
    )
    return response['message']['content']