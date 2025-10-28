import typer
import pandas as pd
import sys
import os
import ollama

# --- Import all modules from your teammates ---
try:
    import database_manager  # Person 2
    import analysis_engine   # Person 3
    import generation_engine # Person 3 & 4
    import discovery_engine  # Person 4
except ModuleNotFoundError as e:
    print(f"FATAL ERROR: A required file is missing: {e.name}")
    print("Please ensure all .py files (database_manager.py, analysis_engine.py, etc.) exist in this directory.")
    sys.exit(1)


# --- Initialize the Typer App ---
app = typer.Typer(
    name="cyforge",
    help="CyForge: The AI Smart Marketing Assistant. Finds leads, analyzes them, and generates outreach."
)


def _check_ollama_running():
    """A helper function to check if the Ollama server is running."""
    try:
        ollama.list()
        return True
    except Exception:
        return False

@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context):
    """
    This callback runs before any command.
    We use it to check for the Ollama server.
    """
    # This check ensures that if someone just types "python main.py", they see the help menu
    if ctx.invoked_subcommand is None:
        typer.echo("Welcome to CyForge! Please use a command like 'run' or 'analyze'.")
        typer.echo("Try 'python main.py --help' for options.")
    
    # Check for Ollama *only if* the 'run' command is being used
    elif ctx.invoked_subcommand == "run" and not _check_ollama_running():
        typer.secho("Fatal Error: Ollama server is not running.", fg=typer.colors.RED, bold=True)
        typer.echo("Please start the Ollama application and try again.")
        raise typer.Exit(code=1)


# --- The Main "run" Command ---
@app.command()
def run(
    url: str = typer.Argument(
        ..., 
        help="Your company's website URL (e.g., https://cyforge.com)"
    ),
    desc: str = typer.Option(
        ..., 
        "--desc", 
        "-d",
        help="A 1-sentence description of your B2B services (e.g., 'We sell AI-powered cybersecurity audits.')"
    ),
    dev: bool = typer.Option(
        False,
        "--dev",
        help="Run in Development Mode (skips database connection and logging)"
    )
):
    """
    Run the full lead generation and outreach pipeline.
    """
    typer.secho("🚀 Starting CyForge: The AI Smart Marketing Assistant...", fg=typer.colors.CYAN, bold=True)
    if dev:
        typer.secho("    -- DEV MODE ACTIVE (Database will be skipped) --", fg=typer.colors.YELLOW)


    # --- Phase 1: Analyze Self [Person 3's Code] ---
    typer.echo("\n--- Phase 1: Analyzing Your Business ---")
    try:
        services_list_str = analysis_engine.analyze_my_business(url, desc)
        typer.secho(f"✅ Found Services: {services_list_str}", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"CRASH in analysis_engine.py (Person 3): {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # --- Phase 2: Discover Leads [Person 4's Code] ---
    typer.echo("\n--- Phase 2: Discovering New Leads ---")
    try:
        leads = discovery_engine.find_leads(services_list_str)
        if not leads:
            typer.secho("No new leads found. Check SerpAPI key or queries. Exiting.", fg=typer.colors.YELLOW)
            raise typer.Exit()
        typer.secho(f"✅ Found {len(leads)} potential leads via SerpAPI.", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"CRASH in discovery_engine.py (Person 4): {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # --- Phase 3: Connect to Database [Person 2's Code] ---
    typer.echo("\n--- Phase 3: Connecting to Database ---")
    db = None
    existing_urls = set()
    if dev:
        typer.secho("Skipping database connection in --dev mode.", fg=typer.colors.YELLOW)
    else:
        try:
            db = database_manager.Database()
            existing_urls = db.get_existing_urls()
            typer.secho(f"✅ Connected to Google Sheets. Found {len(existing_urls)} existing leads.", fg=typer.colors.GREEN)
        except Exception as e:
            typer.secho(f"CRASH in database_manager.py (Person 2): {e}", fg=typer.colors.RED)
            typer.secho("Continuing in --dev mode. No data will be logged.", fg=typer.colors.YELLOW)
            dev = True # Force dev mode if the database fails

    # --- Phase 4: Main Processing Loop ---
    typer.echo("\n--- Phase 4: Processing New Leads ---")
    new_leads_processed = 0
    for lead in leads:
        lead_name = lead.get('name', 'Unknown Company')
        lead_url = lead.get('url')

        if not lead_url:
            typer.secho(f"Skipping lead with no URL.", fg=typer.colors.YELLOW)
            continue
        
        if lead_url in existing_urls:
            typer.echo(f"Skipping duplicate: {lead_name}")
            continue

        try:
            typer.secho(f"\nProcessing new lead: {lead_name} ({lead_url})", bold=True)
            
            # --- 4a: Analyze Client [Person 3] ---
            client_info = analysis_engine.analyze_client(lead_url)
            if not client_info:
                typer.secho(f"  -> Failed to analyze {lead_url}. Skipping.", fg=typer.colors.YELLOW)
                continue
            typer.echo(f"  -> Analyzed. Industry: {client_info.get('industry', 'N/A')}")
            
            # --- 4b: Generate Email [Person 3] ---
            email_draft = generation_engine.generate_email(services_list_str, client_info)
            typer.echo("  -> Email draft generated.")
            
            # --- 4c: Generate PDF [Person 4] ---
            pdf_path = generation_engine.create_portfolio_pdf(services_list_str, client_info, lead_name)
            typer.echo(f"  -> PDF portfolio created at {pdf_path}")
            
            # --- 4d: Upload & Log [Person 2] ---
            if dev:
                typer.secho("  -> Skipping database logging (--dev mode).", fg=typer.colors.YELLOW)
            else:
                typer.echo("  -> Uploading PDF to Google Drive...")
                drive_link = db.upload_pdf(pdf_path, lead_name)
                typer.echo("  -> Logging to Google Sheets...")
                db.log_lead(
                    name=lead_name,
                    url=lead_url,
                    summary=client_info.get('summary', 'N/A'),
                    industry=client_info.get('industry', 'N/A'),
                    email=email_draft,
                    drive_link=drive_link
                )
            
            new_leads_processed += 1
            typer.secho(f"✅ Successfully processed {lead_name}", fg=typer.colors.GREEN)

        except Exception as e:
            typer.secho(f"CRASH: Failed to process {lead_name}. Error: {e}", fg=typer.colors.RED)
            import traceback
            traceback.print_exc() # Print full error trace for debugging
            continue # Skip to the next lead

    typer.secho(f"\n--- Pipeline Complete ---", fg=typer.colors.CYAN, bold=True)
    typer.secho(f"Processed {new_leads_processed} new leads.", fg=typer.colors.GREEN)


# --- The Bonus "analyze" Command ---
@app.command()
def analyze():
    """
    Analyzes the leads in the Google Sheet and prints a report.
    """
    typer.secho("📊 Analyzing Lead Database...", fg=typer.colors.CYAN, bold=True)
    try:
        db = database_manager.Database()
        records = db.get_all_records()
    except Exception as e:
        typer.secho(f"CRASH in database_manager.py (Person 2): {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if len(records) < 2: # Only 1 row (headers) or 0
        typer.secho("No data to analyze. Run the 'run' command first.", fg=typer.colors.YELLOW)
        return

    # Convert to Pandas DataFrame
    try:
        headers = records[0]
        data = records[1:]
        df = pd.DataFrame(data, columns=headers)
    except Exception as e:
        typer.secho(f"Error creating DataFrame. Is the sheet empty or malformed? {e}", fg=typer.colors.RED)
        return

    typer.echo(f"\n--- Analytics Report ---")
    typer.secho(f"Total Leads Logged: {len(df)}", bold=True)
    
    if "Industry" in df.columns:
        typer.secho("\nLeads by Industry:", bold=True)
        # Use to_string() for clean printing in the terminal
        industry_counts = df["Industry"].value_counts().to_string()
        typer.echo(industry_counts)
    else:
        typer.secho("\n'Industry' column not found. Run the pipeline to populate it.", fg=typer.colors.YELLOW)
    
    typer.secho("------------------------", bold=True)


# --- This makes the script runnable ---
if __name__ == "__main__":
    app()