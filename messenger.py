import requests
import os

ACCESS_TOKEN = "EAAR4EKodEE4BPLRQaSlzVMJkEEvdhPuG9NOLjixKHC7gO63yCuBC7ZC2bJNI5V7EMFZAdWCLkZAUn9RJmzcLZAXf51LZAVrJYzd1KCsoDnHUY9EN0ucrGbqU00OFQiwMRhZCfuECdKkgtDZC0NnYKGl4XaWzmAI8BzOhy2SNKHvEZAJqDOhKbwo7sExS1Nyu8y8jzfmjIv5sKThIbGZACuIaVQrHsf01ZCvBXmKnVONy3gS5n0UQZDZD"
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
