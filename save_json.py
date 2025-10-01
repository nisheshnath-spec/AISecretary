# save_json.py
import json
import os

def save_emails_to_json(email_list, filename="emails.json"):
    """
    Save parsed emails into a JSON file.
    Args:
        email_list (list of dicts): your structured email data
        filename (str): file name to save JSON
    """
    try:
        # Ensure a folder exists
        os.makedirs("data", exist_ok=True)
        filepath = os.path.join("data", filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(email_list, f, indent=4, ensure_ascii=False)

        print(f"✅ Saved {len(email_list)} emails to {filepath}")
        return True
    except Exception as e:
        print(f"❌ Error saving JSON: {e}")
        return False
