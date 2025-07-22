import requests
import os

ACCESS_TOKEN = "EAAR4EKodEE4BPNwy8eCP67ZC08StsuBVnGoGVFZCm7VceY1OEoYLTHP5blMsZCaBpwaPzLXIqz6XrulhACCQ2M3RfTqloeK1rYRANnFcyoPOpTpCnQuBr0LfwfZAMCVDxTcH7wZAL7j3WrdDvuMDZB4FkcNdDlEZBZA6OMQxPRHZAQVDoPRQZChp7FB97rEH48O1iRAYKkBmbAixfqqQROMdzNbckArVXpYWQK2HUMQP33v1JNU0YZD"
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
