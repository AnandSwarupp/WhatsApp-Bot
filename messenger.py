import requests
import os

ACCESS_TOKEN = "EAAR4EKodEE4BPPQerlGnT7UilOSzAlo3cdwZAXu31JQxZCl2OtUXuoUmqE0mHTsCoSKKWlXd9RhEO2ccYZAosVZAZCZBAgrTQIalTtZCAL98KnFje4dHmYlB6UwSONabPHb6XhPjKx6bKI4ce61paUuJWrZB2E7jxRCxw1u6KMlI1JmKGCTT3AmSnRjIaswTlEVRkBftlk5B2tciouzgsAsh23HNZB9LfH5zsgUD8jLtSe7XZAvQQZD"
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
