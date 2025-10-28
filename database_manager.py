# database_manager.py (OAuth Version for Free Accounts)
import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request # Needed for token refresh
import os
import os.path

# --- THIS IS THE "CONTRACT" ---
# 1. Sheet Name (Tell your team)
SHEET_NAME = "Smart Marketing Leads"

# 2. Folder ID (Tell your team - This MUST be your ID)
DRIVE_FOLDER_ID = "1UZGR4ORq0RBh9VGUp-jnoAkDFTDF2br7" # PASTE YOUR FOLDER ID HERE

# 3. Client Secret File (Tell team they need this file)
CLIENT_SECRET_FILE = "client_secret.json" 

# 4. Token File (This is created automatically, DO NOT SHARE)
TOKEN_FILE = "token.json" 

# 5. Scopes (Permissions the app asks for)
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
# --- END OF CONTRACT ---


class Database:
    def __init__(self):
        """Initializes the connection to both Sheets and Drive using OAuth."""
        creds = self._get_credentials()
        
        try:
            # Authorize gspread (Sheets)
            self.sheet = gspread.authorize(creds).open(SHEET_NAME).sheet1
            
            # Authorize Google Drive API
            self.drive_service = build('drive', 'v3', credentials=creds)
            
        except gspread.exceptions.SpreadsheetNotFound:
            print(f"FATAL ERROR (Person 2): Spreadsheet '{SHEET_NAME}' not found.")
            print("Please ensure the sheet exists and the name matches exactly.")
            raise
        except Exception as e:
            print(f"FATAL ERROR (Person 2): Could not connect to Google Services. {e}")
            print("Check your internet connection and ensure the Google Cloud setup was correct.")
            raise
            
        self._setup_headers()

    def _get_credentials(self):
        """
        Gets valid user credentials via OAuth 2.0 flow.
        Refreshes token if expired, initiates login if needed.
        """
        creds = None
        # The file token.json stores the user's access and refresh tokens.
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing token: {e}. Need to re-authenticate.")
                    creds = None # Force re-login
            
            # Only initiate flow if creds are still None (needed login)
            if not creds:
                if not os.path.exists(CLIENT_SECRET_FILE):
                    print(f"FATAL ERROR (Person 2): '{CLIENT_SECRET_FILE}' not found.")
                    print("Download the OAuth 'Desktop app' JSON credential from Google Cloud.")
                    raise FileNotFoundError(f"'{CLIENT_SECRET_FILE}' is missing.")
                    
                print("--- GOOGLE AUTHENTICATION REQUIRED (First time or token expired) ---")
                print(f"A browser window will open. Please log in with the Google Account")
                print("you added as a 'Test User' in the Google Cloud Console.")
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
                # port=0 finds a random available port
                creds = flow.run_local_server(port=0) 
            
            # Save the credentials for the next run
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
            print("--- Authentication successful. 'token.json' created/updated. ---")
                
        return creds

    def _setup_headers(self):
        """Checks if the sheet is empty and adds headers if it is."""
        try:
            # Check if A1 is empty, safer than get_all_values() for large sheets
            if not self.sheet.acell('A1').value: 
                headers = ["Client Name", "URL", "Summary", "Industry", "Email Draft", "Drive Link"]
                self.sheet.append_row(headers)
                print("Database Manager: Added headers to empty sheet.")
        except Exception as e:
            print(f"Warning (Person 2): Could not check/add headers. {e}")


    def get_existing_urls(self) -> set:
        """Gets all URLs from column 2 for de-duplication."""
        print("Database Manager: Fetching existing URLs from Sheet...")
        try:
            # Column 2 = URL column
            urls = self.sheet.col_values(2)[1:] # Skip header row
            return set(filter(None, urls)) # Filter out empty strings
        except Exception as e:
            print(f"Warning (Person 2): Could not get URLs. Maybe sheet is empty? {e}")
            return set()

    def get_all_records(self) -> list:
        """Gets all data as a list of dictionaries for the 'analyze' command."""
        print("Database Manager: Fetching all records for analysis...")
        try:
            # get_all_records is convenient for pandas
            return self.sheet.get_all_records() 
        except Exception as e:
            print(f"Warning (Person 2): Could not fetch all records. {e}")
            return []

    def upload_pdf(self, file_path: str, lead_name: str) -> str:
        """Uploads a local file to the specified Google Drive folder."""
        print(f"Database Manager: Uploading '{file_path}' to Google Drive...")
        
        if not os.path.exists(file_path):
             print(f"CRITICAL ERROR (Person 2): File not found for upload: {file_path}")
             return "UPLOAD_FAILED_FILE_MISSING"
             
        try:
            file_metadata = {
                'name': f"{lead_name}_Portfolio.pdf",
                'parents': [DRIVE_FOLDER_ID] 
            }
            media = MediaFileUpload(file_path, mimetype='application/pdf', resumable=True)
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink' 
            ).execute()
            
            file_id = file.get('id')
            
            # Make the file readable by anyone with the link
            self.drive_service.permissions().create(
                fileId=file_id,
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
            
            print("Database Manager: Upload successful.")
            
            # Clean up the local file after successful upload
            try:
                os.remove(file_path)
            except OSError as e:
                print(f"Warning (Person 2): Could not delete local file {file_path}. {e}")
                
            return file.get('webViewLink') # The direct link to view in browser

        except Exception as e:
            print(f"CRITICAL ERROR (Person 2): Failed to upload PDF. {e}")
            # Try to provide more helpful feedback for common issues
            if "invalid_grant" in str(e):
                 print("Hint: Your authentication token might be expired or invalid. Delete 'token.json' and try again.")
            elif "notFound" in str(e):
                 print(f"Hint: Check if DRIVE_FOLDER_ID '{DRIVE_FOLDER_ID}' is correct and exists.")
            return "UPLOAD_FAILED"

    def log_lead(self, name: str, url: str, summary: str, industry: str, email: str, drive_link: str):
        """Appends a single, complete row to the Google Sheet."""
        print(f"Database Manager: Logging '{name}' to Google Sheet...")
        try:
            # Ensure all values are strings to prevent Gspread errors
            row = [
                str(name), str(url), str(summary), str(industry), 
                str(email), str(drive_link)
            ]
            self.sheet.append_row(row)
            print("Database Manager: Log successful.")
        except Exception as e:
            print(f"CRITICAL ERROR (Person 2): Failed to write to sheet. {e}")
            if "RESOURCE_EXHAUSTED" in str(e):
                print("Hint: You might be hitting Google Sheets API rate limits.")