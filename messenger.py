import requests
import os

ACCESS_TOKEN = "EAAR4EKodEE4BPDoie4g4fYZA6IEP6hUJD0QJ3ZBlZAp7E5VtwyUO3jsk4Nk0ZCNn96DCXI5T8dbYmd4iFcZCZCVnxz8l4xrPGBmCMZAZAxvZBlIrZBnBNoeLzMm7xE0Q1ZAe9aeeEbHilR9BGjYZB3I48joEA2Vg5GnM5SmvcWV5zTZBHVuRrIHDNEn1k4S53HBfOi8dGd0npxmCPoy9UnDvggbjMQxECLIuuOXVEt2HdZCinzZBn1AmQZDZD"
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
