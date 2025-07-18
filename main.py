from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests, os, json
from supabase import create_client

from auth import (
    get_user_state, set_user_state,
    get_user_email, set_user_email,
    get_user_otp, set_user_otp,
    generate_and_send_otp,
    is_authenticated, mark_authenticated,
    clear_user, set_user_intent,
    get_user_intent
)

from whatsapp import send_message, send_button_message
from ocr import ocr_from_bytes
from openai_utils import ask_openai

app = FastAPI()

ACCESS_TOKEN = "EAAR4EKodEE4BPDSHXiEIjVk1Fq5fR9oXtcGt1LHFswNU2ymrUgrWjnQ8DDowSNaloTjTIkOSgLD7zGDKn4OrShRRjd0iRMFFSOrztMXDMNZAsADg99WScdAAnfPrNcEEhkyz10oYlKsd2A5NRIVJbAaACz5ZAKvNOFSm0uRBKq8jMANHZC1QF7TiuwpM8UjOISQrmH5ZCrD1veyKaDvzeRCqmeJv6bO844XqljDXJX6vQQZDZD"
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
                    mark_authenticated(sender)
                    clear_user(sender)
                    send_message(sender, "✅ OTP verified!")

                    response = supabase.table("users").select("email").eq("email", email).execute()
                    if not response.data:
                        set_user_state(sender, "awaiting_name")
                        send_message(sender, "👤 Please enter your name to register.")
                    else:
                        send_button_message(sender)
                else:
                    send_message(sender, "❌ Incorrect OTP. Try again.")
                return {"status": "ok"}

            elif state == "awaiting_name":
                set_user_state(sender, "awaiting_age")
                set_user_email(sender, {"name": text})
                send_message(sender, "🎂 Please enter your age.")
                return {"status": "ok"}

            elif state == "awaiting_age":
                user_data = get_user_email(sender)
                user_data["age"] = text
                set_user_email(sender, user_data)
                set_user_state(sender, "awaiting_gender")
                send_message(sender, "⚧ Please enter your gender (Male/Female/Other).")
                return {"status": "ok"}

            elif state == "awaiting_gender":
                user_data = get_user_email(sender)
                user_data["gender"] = text
                user_data["email"] = user_data.get("verified_email")
                user_data["whatsapp"] = sender
                supabase.table("users").insert(user_data).execute()

                send_message(sender, "✅ Registration successful!")
                mark_authenticated(sender)
                send_button_message(sender)
                return {"status": "ok"}

            elif text.lower() == "hello":
                send_message(sender, "📧 Please enter your email for verification.")
                set_user_state(sender, "awaiting_email")
                return {"status": "ok"}

            elif state == "awaiting_email":
                set_user_email(sender, {"verified_email": text})
                generate_and_send_otp(sender, text)
                send_message(sender, f"📨 OTP sent to {text}. Please reply with the code.")
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
                print("❌ OCR Error:", e)
                send_message(sender, "❌ OCR failed. Please upload a clear image or PDF.")
                return {"status": "ok"}

            # Prompt selection
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

                    If any field is missing or unclear, write "Not Found".

                    OCR Text:
                    \"\"\"{ocr_text}\"\"\"

                    Return the output in this format:
                    Invoice Number: ...
                    Seller Name: ...
                    Buyer Name: ...
                    Invoice Date: ...
                    Item: ...
                    Quantity: ...
                    Total Amount: ...
                """
            else:
                prompt = f"""
                    You are an intelligent OCR post-processor for Indian bank cheques.

                    Extract these fields:
                    - Receiver Name
                    - Account Holder Name
                    - Cheque Date
                    - Bank Name
                    - Account Number
                    - Amount

                    OCR Text:
                    \"\"\"{ocr_text}\"\"\"

                    Format:
                    Account Holder Name: ...
                    Receiver Name: ...
                    Cheque Date: ...
                    Bank Name: ...
                    Account Number: ...
                    Amount: ...
                """

            try:
                response_text = ask_openai(prompt)
                print(f"🤖 Response:\n{response_text}")

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
                send_message(sender, "✅ Document uploaded successfully.")
                return {"status": "ok"}

            except Exception as e:
                print("❌ OpenAI or Supabase error:", e)
                send_message(sender, "⚠️ Something went wrong while processing the document.")
                return {"status": "ok"}

    except Exception as e:
        print("Unhandled error:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})

    return {"status": "ok"}
