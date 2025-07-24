import requests
import os
from auth import set_user_intent
from messenger import send_message

ACCESS_TOKEN = "EAAR4EKodEE4BPPwpX7zt2jdrpJoZCSLfRdSjVAzdZBTuGPoYp3mTScXJWFn7CpLZCvGT4Pk8sNNlDBkKFCyZCmTOZBnFPqCVZAENwsb7Ms0eJx8zWFNRCjOD7quPy6ZBqrhP171EDwrxtiBZB7J9N8uR9ZB04zg6lcGrs2VPdl5u6KvTEwNvuSZC5GY8gIwqoltZBdkxXUnYOxgkNmWZCFZAQ3BbDuUoDT0XtbVpEmIyqe5FydPtyeQZDZD"
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
GRAPH_API_URL = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

def send_button_message(to: str):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": "Welcome to FinBot! What would you like to do?"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "upload_cheque",
                            "title": "📓 Upload Cheque"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "upload_invoice",
                            "title": "💼 Upload Invoice"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "chat_finance",
                            "title": "💬 Chat"
                        }
                    }
                ]
            }
        }
    }
    response = requests.post(GRAPH_API_URL, headers=headers, json=payload)
    print(response.json())     

