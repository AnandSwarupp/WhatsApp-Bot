import requests
import os

ACCESS_TOKEN = "EAAR4EKodEE4BPKZB9f0dKZB4b8xHnFY7JSUNnJqHbTMF9vNAfOd9ZCMYmzpzZCGxaT6aW6dptSbPgzps69ugpIOnn7lP6oJnPmOZCNFpin1UemUZAmLbEzAUYKWonYtiv4vZBwIkl5FKivC5DZCB4OmK7RbMuntGm77whW4WqEf13A27we9ZAZAfbFD90wOiy9BSZBAYZCJKFGZCsa4mBkEz1jIzr9pQLwLtlZCdcctwxGdLPGfdErkfAZD"
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
GRAPH_API_URL = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

def send_message(to: str, message: str):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(GRAPH_API_URL, headers=headers, json=payload)
    print(response.json())
