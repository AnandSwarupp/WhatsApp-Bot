import requests
import os

ACCESS_TOKEN = "EAAR4EKodEE4BPJyofg2OyclOghSAbOWz1MQMDaOohedVeQgqOfSO7vjO6AGmPNZAFUD3yOjZAHl2yEyBeEcqXFkrdBLQUhkoadOKETZA41NMCWg8OCrxltZAjZCLzePkBAvYaHRbuc8p5fYVmWifPx1vu6FoWDKDfehTR1q2ZC1qbxF6hYNuUAYIZCNTBdhmMgKZC1ixIc96ZCiFrksZCsAhGxDbGFxpvQZAFxim7hdNmfFfDNH1gZDZD"
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
