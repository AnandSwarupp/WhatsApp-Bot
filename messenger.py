import requests
import os

ACCESS_TOKEN = "EAAR4EKodEE4BPBlxtFOKwdHDOpSU0v3g58ZCvzjIXzDAUE2GjAtuuUeVkUZAN9HnGf6DYv05a4mRQyEGURYg1dbqUgGdrwQJbdrW2k59gfNLchf4Qnifepgcm9dsDjb6fg12Mo2p9qGcOjF2mHZAWY6ssxcXPCkPohWcnpBdPUZCAfzLBLgsvCgMkx3stHiZCcRVvzG8sUwP0DmXYLIRjy8oG2G2anyBixqU4IPFhYN0lb3AZD"
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
