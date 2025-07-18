from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests, os, json
from supabase import create_client, Client
from dotenv import load_dotenv
from auth import (
    get_user_state,
    set_user_state,
    get_user_email,
    set_user_email,
    get_user_otp,
    set_user_otp,
    generate_and_send_otp,
    is_authenticated,
    mark_authenticated,
    clear_user,
    set_user_intent,
    get_user_intent
)
from whatsapp import send_message, send_button_message
from ocr import ocr_from_bytes
from openai_utils import ask_openai

# Initialize FastAPI
app = FastAPI()
load_dotenv()

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

ACCESS_TOKEN = "EAAR4EKodEE4BPExXPRZAu71OT6ut0xZCbyU7yM9Sz5kTkXdYZAvpDHJ1BhUjTZAMAHnZAbzIMS2tuUuwMcCVXav7bGlTWLqIZC6M7L9tDdBiyBi3Y0blA3JCvZCQluM4IGpP5SNlO3mxzBqEt2IaC4PH0x25ES8b1CDpxHLH26c1YwqJ9pxaQNsZC9bfAYxQ4A06PQXrJrLhXXsLYNSotkMG1Q1zHiD5WgMIbtPsV1UdipnmJQZDZD"
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print(json.dumps(data, indent=2))

    try:
        entry = data["entry"][0]["changes"][0]["value"]
        messages = entry.get("messages")
        if not messages:
            return {"status": "ok"}

        msg = messages[0]
        sender = msg["from"]
        msg_type = msg["type"]

        if msg_type == "text":
            text = msg["text"]["body"]
            state = get_user_state(sender)

            if state == "awaiting_otp":
                if text == get_user_otp(sender):
                    email = get_user_email(sender)
                    result = supabase.table("users").select("email").eq("email", email).execute()

                    if result.data:
                        clear_user(sender)
                        mark_authenticated(sender)
                        send_message(sender, "✅ OTP verified and you're logged in!")
                        send_button_message(sender)
                    else:
                        set_user_state(sender, "awaiting_name")
                        send_message(sender, "👋 You're verified! Now please enter your full name to complete registration.")
                    return {"status": "ok"}
                else:
                    send_message(sender, "❌ Incorrect OTP. Try again.")
                    return {"status": "ok"}

            elif text.lower() == "hello":
                send_message(sender, "📧 Please enter your email for verification.")
                set_user_state(sender, "awaiting_email")
                return {"status": "ok"}

            elif state == "awaiting_email":
                set_user_email(sender, text)
                generate_and_send_otp(sender, text)
                send_message(sender, f"📨 OTP sent to {text}. Please reply with the code.")
                return {"status": "ok"}

            elif state == "awaiting_name":
                set_user_intent(sender, text.strip())
                set_user_state(sender, "awaiting_age")
                send_message(sender, "📅 Great. Please enter your age.")
                return {"status": "ok"}

            elif state == "awaiting_age":
                try:
                    age = int(text.strip())
                    set_user_otp(sender, str(age))
                    set_user_state(sender, "awaiting_gender")
                    send_message(sender, "👤 Got it. Lastly, enter your gender (e.g., Male/Female/Other).")
                except ValueError:
                    send_message(sender, "❌ Please enter a valid number for age.")
                return {"status": "ok"}

            elif state == "awaiting_gender":
                name = get_user_intent(sender)
                age = get_user_otp(sender)
                gender = text.strip()
                email = get_user_email(sender)

                supabase.table("users").insert({
                    "name": name,
                    "age": int(age),
                    "gender": gender,
                    "email": email,
                    "whatsapp": sender
                }).execute()

                clear_user(sender)
                mark_authenticated(sender)
                send_message(sender, f"✅ Thanks {name}! You're now registered and logged in.")
                send_button_message(sender)
                return {"status": "ok"}

            elif text.lower() == "status":
                send_message(sender, f"📌 State: {get_user_state(sender)} | Auth: {is_authenticated(sender)}")
                return {"status": "ok"}

            else:
                send_message(sender, "👋 Please type 'hello' to begin chat with FinBot!")
                return {"status": "ok"}

        if not is_authenticated(sender):
            send_message(sender, "🔒 Please verify by saying 'hello' first.")
            return {"status": "ok"}

        if msg_type == "interactive":
            button_id = msg["interactive"]["button_reply"]["id"]
            set_user_intent(sender, button_id)

            if button_id == "upload_invoice":
                send_message(sender, "📤 Please upload your invoice (PDF or image).")
            elif button_id == "upload_cheque":
                send_message(sender, "📤 Please upload a scanned cheque.")
            return {"status": "ok"}

        if msg_type in ["image", "document"]:
            intent = get_user_intent(sender)
            if intent not in ["upload_invoice", "upload_cheque"]:
                send_message(sender, "❗ Please select an option first using the buttons.")
                return {"status": "ok"}

            media_id = msg[msg_type]["id"]
            meta_url = f"https://graph.facebook.com/v19.0/{media_id}"
            meta = requests.get(meta_url, params={"access_token": ACCESS_TOKEN}).json()
            media_url = meta.get("url")

            file_bytes = requests.get(media_url, headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}).content

            try:
                ocr_text = ocr_from_bytes(file_bytes)
            except Exception as e:
                send_message(sender, "❌ OCR failed. Please upload a clear image or PDF.")
                return {"status": "ok"}

            if intent == "upload_invoice":
                prompt = f"""
                    You are an intelligent OCR post-processor for invoices.

                    Extract the following fields clearly from the raw OCR text below:
                    - Invoice Number
                    - Seller Name
                    - Buyer Name
                    - Invoice Date
                    - Item(s)
                    - Quantity
                    - Amount (Total)

                    If any field is missing or unclear, write \"Not Found\".

                    OCR Text:
                    \"\"\"
                    {ocr_text}
                    \"\"\"

                    Return the output in this format:
                    Invoice Number: ...
                    Seller Name: ...
                    Buyer Name: ...
                    Invoice Date: ...
                    Items:
                    - Item: ...
                        Quantity: ...
                        Amount: ...
                    Total Amount: ...
                """
            elif intent == "upload_cheque":
                prompt = f"""
                    You are an intelligent OCR post-processor for Indian bank cheques.
                    
                    Your job is to extract specific fields from the cheque OCR result. Pay special attention to the positions and context of each field.
                    
                    ### Extraction Instructions:
                    - **Receiver Name**: This is the person or entity the cheque is made payable to. It appears directly after "PAY".
                    - **Account Holder Name**: This is the person who signed the cheque. It is usually printed or written at the bottom-right, near the signature line.
                    - **Cheque Date**: Usually in the top-right corner, formatted like DDMMYYYY.
                    - **Bank Name**: Printed in the top-left.
                    - **Account Number**: Written after A/c No. , basicallly below the amount**.
                    - **Amount**: Extract the full amount in numerals.
                    
                    Ignore static texts like "OR BEARER", "Rupees", etc.
                    
                    If any field is missing or unreadable, write "Not Found".
                    
                    OCR Text:
                    \"\"\"
                    {ocr_text}
                    \"\"\"
                    
                    Return the result in this format:
                    
                    Account Holder Name: ...
                    Receiver Name: ...
                    Cheque Date: ...
                    Bank Name: ...
                    Account Number: ...
                    Amount: ...
                    """
            else:
                raise ValueError(f"❌ Unknown intent: {intent}")

            try:
                response_text = ask_openai(prompt)
                print(f"🤖 Response:\n{response_text}")
                send_message(sender, response_text)
                parsed = {}
                for line in response_text.splitlines():
                    if ":" in line:
                        key, value = line.split(":", 1)
                        parsed[key.strip().lower().replace(" ", "_")] = value.strip()

                user_email = get_user_email(sender)
                email = user_email.get("verified_email") if isinstance(user_email, dict) else user_email

                if intent == "upload_invoice":
                    invoice_data = {
                        "email": email,
                        "invoice_number": parsed.get("invoice_number", "Not Found"),
                        "sellers_name": parsed.get("seller_name", "Not Found"),
                        "buyers_name": parsed.get("buyer_name", "Not Found"),
                        "date": parsed.get("invoice_date", "Not Found"),
                        "item": parsed.get("item", "Not Found"),
                        "quantity": parsed.get("quantity", "Not Found"),
                        "amount": parsed.get("total_amount", "Not Found")
                    }
                    supabase.table("upload_invoice").insert(invoice_data).execute()

                elif intent == "upload_cheque":
                    cheque_data = {
                        "email": email,
                        "payee_name": parsed.get("receiver_name", "Not Found"),
                        "senders_name": parsed.get("account_holder_name", "Not Found"),
                        "amount": parsed.get("amount", "Not Found"),
                        "date": parsed.get("cheque_date", "Not Found"),
                        "bank_name": parsed.get("bank_name", "Not Found"),
                        "account_number": parsed.get("account_number", "Not Found")
                    }
                    supabase.table("upload_cheique").insert(cheque_data).execute()
                send_message(sender, response_text)
                send_message(sender, "✅ Document uploaded and stored successfully.")
                return {"status": "ok"}

            except Exception as e:
                print("❌ OpenAI or Supabase error:", e)
                send_message(sender, "⚠️ Something went wrong while processing the document.")
                return {"status": "ok"}

    except Exception as e:
        print("Unhandled error:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})

    return {"status": "ok"}
