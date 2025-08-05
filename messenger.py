import requests
import os

ACCESS_TOKEN = "EAAR4EKodEE4BPOZAsHKYsd1QzQOZBuGJBJ1fXdHMYvGljwZAp6sVKPRyLOZAMZBPE3Lyiv1chFIGMJOXC8hM0i0UpERxcnbOUOKwjY2H1RA4deBinbBdarXFaadbPDcsBP0nw9bEww7zN7voLbZBMnsM53YMGYuX1S3ZAbry08IZBSnEqASW3Ys7CmUAoWDdJVgQSIUS4L90zmHytMx8452cH8BrkwyVvH3urLA2gYz9coOZCggZDZD"
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

