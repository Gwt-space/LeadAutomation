from flask import Flask, request
import json
import requests
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()

# ==== CONFIG ====
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
GRAPH_API_VERSION = os.getenv("GRAPH_API_VERSION")
GOOGLE_CREDS_FILE = os.getenv("GOOGLE_CREDS_FILE")
SHEET_NAME = os.getenv("SHEET_NAME")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
TEMPLATE_NAME = os.getenv("TEMPLATE_NAME")
LANGUAGE_CODE = os.getenv("LANGUAGE_CODE")
ADMIN_PHONE = os.getenv("ADMIN_PHONE")

# WhatsApp Recipients
CLIENT_PHONE = os.getenv("CLIENT_PHONE")
MY_PHONE = os.getenv("MY_PHONE")

@app.route('/')
def index():
    return "✅ Webhook service is live!"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if token == VERIFY_TOKEN:
            return challenge, 200
        return "Unauthorized", 403

    if request.method == 'POST':
        data = request.get_json(force=True)
        print("🔔 Received webhook payload:")
        print(json.dumps(data, indent=2))

        if data and data.get("entry"):
            for entry in data["entry"]:
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    lead_id = value.get("leadgen_id")
                    print(f"📌 Lead ID: {lead_id}")

                    if "field_data" in value:
                        answers = value["field_data"]
                        lead_data = {field["name"]: field["values"][0] for field in answers}
                        save_to_google_sheet(lead_data)
                        notify_on_whatsapp(lead_data)
                    else:
                        lead_data = get_lead_data(lead_id)
                        if lead_data:
                            save_to_google_sheet(lead_data)
                            notify_on_whatsapp(lead_data)
        return "EVENT_RECEIVED", 200


def get_lead_data(lead_id):
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{lead_id}"
    params = {"access_token": ACCESS_TOKEN}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        result = response.json()
        print("✅ Fetched Lead Data:", json.dumps(result, indent=2))
        answers = result.get("field_data", [])
        return {field["name"]: field["values"][0] for field in answers}
    else:
        print("❌ Failed to fetch lead data:", response.text)
        return None


def save_to_google_sheet(lead_data):
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(GOOGLE_CREDS_FILE, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open(SHEET_NAME).sheet1

        row = [
            lead_data.get("full_name", ""),
            lead_data.get("email", ""),
            lead_data.get("phone_number", "")
        ]
        sheet.append_row(row)
        print("📤 Lead saved to Google Sheets successfully!")
        print("📄 Lead data going to sheet:", lead_data)
    except Exception as e:
        print("❌ Error saving to Google Sheets:", str(e))


def notify_on_whatsapp(lead_data):
    formatted_data = {
        "name": lead_data.get("full_name", ""),
        "email": lead_data.get("email", ""),
        "phone": lead_data.get("phone_number", "")
    }

    send_whatsapp_message(CLIENT_PHONE, formatted_data)
    send_whatsapp_message(MY_PHONE, formatted_data)


def send_whatsapp_message(to_number, lead_data):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "template",
        "template": {
            "name": TEMPLATE_NAME,
            "language": { "code": LANGUAGE_CODE },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": lead_data.get("full_name", "N/A")},
                        {"type": "text", "text": lead_data.get("email", "N/A")},
                        {"type": "text", "text": lead_data.get("phone_number", "N/A")}
                    ]
                }
            ]
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    print("📲 WhatsApp send response:", response.status_code, response.text)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))


