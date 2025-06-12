import requests
import pandas as pd
import json
import csv


def json_to_csv(json_filepath, csv_filepath):
    with open(json_filepath, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

        if not isinstance(data, list):
            raise ValueError("Expected a list of JSON objects.")
        if not data:
            raise ValueError("JSON file is empty.")

        with open(csv_filepath, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)

            # ✅ Explicit column headers based on your screenshot
            headers = [
                "Object Type", "Object Name", "Object Description", "Event Category", "Tags",
                "is_active", "Object Owner", 
                "is_hidden_from_dropdowns", "is_hidden_from_persona_results",
                "is_hidden_from_pathfinder", "is_hidden_from_timeline"
            ]
            writer.writerow(headers)

            for e in data:
                raw_tags = e.get("tags", [])
                if isinstance(raw_tags, list):
                    tags_str = ", ".join(str(tag) for tag in raw_tags)
                else:
                    tags_str = str(raw_tags)

                writer.writerow([
                    "Event",
                    e.get("event_type", ""),
                    e.get("description", ""),
                    (e.get("category") or {}).get("name", ""),
                    tags_str,
                    e.get("is_active", ""),
                    e.get("owner", ""),
                    e.get("is_hidden_from_dropdowns", False),
                    e.get("is_hidden_from_persona_results", False),
                    e.get("is_hidden_from_pathfinder", False),
                    e.get("is_hidden_from_timeline", False),
                ])
def api_pull(): 

    # 🔐 UPDATE THESE:
    API_KEY = "0eb42ca51c84f5bfe35ee635860b2fc4"
    SECRET_KEY = "8f781b8898b96f609cb7ec3ca1f0056e"
    # Set domain based on your region:
    DOMAIN = "https://amplitude.com" 

    # Prepare auth header
    auth = (API_KEY, SECRET_KEY)

    # Endpoint to fetch all event types
    url = f"{DOMAIN}/api/2/taxonomy/event"

    resp = requests.get(url, auth=auth)
    print("HTTP Status:", resp.status_code)
    print(resp.text[:200])  # preview

    if resp.status_code != 200:
        raise Exception(f"Error {resp.status_code}: {resp.text}")
    else:
        full_response = resp.json()
        events = full_response.get("data", [])
        with open("events.json", "w", encoding='utf-8') as f:
            json.dump(events, f, indent=2)

        # Convert to CSV
        json_to_csv("events.json", "events.csv")
        print("✅ CSV export complete.")
    
if __name__ == "__main__":
    api_pull()
    print("🚀 Amplitude event definitions successfully pulled and saved.")