import requests
import os

ACCESS_TOKEN = "EAAR4EKodEE4BPIdSgcjOsMlpHiAwKD23VZBzTD6fdyDThvWY74I8ufoo7pZCIU6aCUInSliJLROhUd9fVzMFTZASPEP2ruATwZBDJbn2cy3XO9ku7i55pwrSGMxyAsdLmJkvok6fnfwyrTyhTkaGZCZAvTnS5ncMB60dwuzS5vmAUxjZAg5vxkyulOfnzqXnnoVcHyvBQF3bPAk9XsOMy1S8IaqvexCjXZBZACRbxlLAT1czOhwZDZD"
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
