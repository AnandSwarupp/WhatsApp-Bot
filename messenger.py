import requests
import os

ACCESS_TOKEN = "EAAR4EKodEE4BPAZBfdZBsoxlNUy87TN8bEoqKtnucHOxdBde5ZB10sdh7p5LGhRWIqv7Oaao202UXEwZAVhs2UlsZC1pmXJuRFHvIVvZChRxiFOT7VrfaDOZAz0D9ySboQdqDxCKviP14BAHAM5gI1tdOIUUATfswmDuJFS9ygl5ZC1DaX3Ibs8wlZCP1kKguK0GPl4sJQnEFcPZAE4fCIleLjNTzcBcyb1WWM8FZAwYj6vGGpMJWEZD"
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
