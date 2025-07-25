import requests
import os

ACCESS_TOKEN = "EAAR4EKodEE4BPELXQPsZBf5nSFQOi1adxQ4MPnflr6DnZAPITxIrEHiZAuUFa5GkIxFBJCN7orA8EcpHH7ZApdgXAKuhSCthgQbQtpZBRmgX8Xa7uUGQ3mUYmsWjMetz0rKvKSVK7KSvUIQBV03izntAyHX2OsmbWFm27qaZAeHjSf1UnpZCMaRVXbogOHNhfkXiZAIrkpewnaPgAUgSd4iyKrPitZA0GnQaSLgQuCPcFJIWZCuxae"
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
