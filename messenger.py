import requests
import os

ACCESS_TOKEN = "EAAR4EKodEE4BPF9D4cqV3WlD3mwKCrOhv3g3ZB7rlOolwOeifCCXoouHURgHr2CSqiRuZBPbV55GgYlvZAYm4a0h2lj6Hl7Hwzns51R56eTL3Q4aVDl1kXX4qLOtJyzIVfZAo8qdrc2tZCSAdt3ZCCiRO4T9A6tTGdLd04MlryfOdl0nyee4AG0e55A4RgcDAFtHJ4TaERqMKZCXVJnbkijkQOyCUrAQ7NzwomKUmkWnJYCyQZDZD"
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
