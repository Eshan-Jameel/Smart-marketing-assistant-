import database_manager
import os

print("--- STARTING PERSON 2 (DATABASE) TEST ---")

# 1. Create a dummy file to upload
DUMMY_FILE = "dummy_test_portfolio.pdf"
try:
    # We use a simple text file and give it a .pdf name
    # The content doesn't matter for an upload test
    with open(DUMMY_FILE, "w") as f:
        f.write("This is a test PDF.")
    print("Created dummy file.")
except Exception as e:
    print(f"Failed to create dummy file: {e}")
    exit()

try:
    # 2. Initialize the database (This tests __init__)
    print("\nInitializing Database...")
    db = database_manager.Database()
    print("✅ __init__ test passed.")
    
    # 3. Test PDF Upload (This tests upload_pdf)
    print("\nTesting PDF Upload...")
    link = db.upload_pdf(DUMMY_FILE, "Test Lead Inc.")
    assert "drive.google.com" in link, "Did not get a valid drive link!"
    print(f"✅ upload_pdf test passed. Link: {link}")
    
    # 4. Test Logging (This tests log_lead)
    print("\nTesting Sheet Logging...")
    db.log_lead(
        name="Test Lead Inc.",
        url="https://test.com",
        summary="They test things.",
        industry="Testing",
        email="This is a test email.",
        drive_link=link
    )
    print("✅ log_lead test passed.")

    # 5. Test Reading (This tests get_existing_urls)
    print("\nTesting Sheet Reading...")
    urls = db.get_existing_urls()
    assert "https://test.com" in urls, "Logged URL was not found in sheet!"
    print("✅ get_existing_urls test passed.")

    print("\n🎉 ALL PERSON 2 TESTS PASSED! Your code is solid.")
    print("Go to your Google Sheet and Drive folder to verify the new row and file.")

except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()