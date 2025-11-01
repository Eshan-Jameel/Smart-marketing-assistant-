# 🚀 CyForge: AI-Powered Smart Marketing Assistant

This project implements a full B2B Marketing Automation pipeline built entirely in Python. It is designed to automate lead generation, personalized outreach, and resource creation using local AI (Ollama) and integrate data using Google Services.

## ✨ Core Features

* **Lead Discovery:** Finds new business leads using targeted search queries via SerpAPI.
* **AI Client Analysis:** Scrapes target websites (with pagination logic) and uses Ollama to extract business summaries and classify the industry.
* **Personalized Outreach:** Generates concise, professional, and custom cold emails tailored to the client's specific industry and pain points.
* **Custom Portfolio Generation:** Creates a professional, multi-page PDF proposal document for each lead, dynamically filled with CyForge's services.
* **Database Integration:** Logs every lead record, email draft, and a link to the uploaded PDF into Google Sheets and uploads the final PDFs to Google Drive.

---

## ⚙️ Project Workflow: The 5-Phase Pipeline

The core logic is managed by a Typer CLI application that orchestrates the entire workflow.

### Phase 1: Analyze Self

The script scrapes your website (`https://cyforge.com`) and uses AI to identify and list your core service offerings.

### Phase 2: Lead Generation

Using your core services, the script generates targeted search queries to find new prospects via the **Discovery Engine**.

### Phase 3: Client Profiling

For each new lead, the **Analysis Engine** scrapes their website, determines their industry, and provides a concise business summary using an LLM (Ollama).

### Phase 4: Content Generation

The **Generation Engine** drafts a unique cold email and creates a custom PDF proposal, personalizing the content based on the client's profile.

### Phase 5: Logging and Storage

The final outreach package (name, URL, summary, email, PDF link) is logged to Google Sheets and the PDF is uploaded to Google Drive.

---

## 💻 CLI Usage

### Full Pipeline Run

Runs lead discovery, analysis, generation, and logging for new leads:

```bash
python main.py run \
    [https://cyforge.com](https://cyforge.com) \
    --desc "We sell AI-powered cybersecurity audits and automated DevSecOps integration for SaaS and FinTech companies."