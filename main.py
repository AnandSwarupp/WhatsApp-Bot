from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests, os, json
from supabase import create_client, Client
from auth import *
from whatsapp import send_button_message
from messenger import send_message
from ocr import ocr_from_bytes
from openai_utils import ask_openai
from datetime import datetime
import re

app = FastAPI()

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

ACCESS_TOKEN = "EAAR4EKodEE4BPPQerlGnT7UilOSzAlo3cdwZAXu31JQxZCl2OtUXuoUmqE0mHTsCoSKKWlXd9RhEO2ccYZAosVZAZCZBAgrTQIalTtZCAL98KnFje4dHmYlB6UwSONabPHb6XhPjKx6bKI4ce61paUuJWrZB2E7jxRCxw1u6KMlI1JmKGCTT3AmSnRjIaswTlEVRkBftlk5B2tciouzgsAsh23HNZB9LfH5zsgUD8jLtSe7XZAvQQZD"
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

def format_date(raw_date: str) -> str | None:
    for fmt in ("%d%m%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw_date, fmt).date().isoformat()
        except ValueError:
            continue
    return None

def run_sql_on_supabase(sql_query: str):
    result = supabase.rpc("execute_sql", {"sql": sql_query}).execute()
    return result

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
        state = get_user_state(sender)

        if msg_type == "text":
            text = msg["text"]["body"].strip().lower()
            state = get_user_state(sender)

            if text == "hello":
                send_message(sender, "📧 Please enter your email to begin.")
                set_user_state(sender, "awaiting_email")
                return {"status": "ok"}

            if state == "awaiting_email":
                set_user_email(sender, text.lower())
                email = text
                email_text = text

                # Check if user is registered
                result = supabase.table("users").select("email").eq("email", email).execute()
                if result.data:
                    # Registered → ask for OTP
                    generate_and_send_otp(sender, email)
                    set_user_state(sender, "awaiting_otp")
                    send_message(sender, f"📨 OTP sent to {email}. Please reply with the code.")
                else:
                    # Not registered → ask for name
                    set_user_state(sender, "awaiting_name")
                    send_message(sender, "👋 Welcome! Please enter your full name to register.")
                return {"status": "ok"}

            if state == "awaiting_name":
                set_user_intent(sender, text)
                set_user_state(sender, "awaiting_age")
                send_message(sender, "🎂 Great. Please enter your age.")
                return {"status": "ok"}

            if state == "awaiting_age":
                try:
                    age = int(text)
                    set_user_otp(sender, str(age))
                    set_user_state(sender, "awaiting_gender")
                    send_message(sender, "👤 Almost done. Enter your gender (e.g., Male/Female/Other).")
                except ValueError:
                    send_message(sender, "❌ Please enter a valid number for age.")
                return {"status": "ok"}

            if state == "awaiting_gender":
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

                # Now send OTP after registration
                generate_and_send_otp(sender, email)
                set_user_state(sender, "awaiting_otp")
                send_message(sender, f"✅ You're almost done! OTP sent to {email}. Please reply with the code.")
                return {"status": "ok"}

            if state == "awaiting_otp":
                if text == get_user_otp(sender):
                    mark_authenticated(sender)
                    clear_user(sender)
                    send_message(sender, "✅ OTP verified! You're now logged in.")
                    send_button_message(sender)
                else:
                    send_message(sender, "❌ Incorrect OTP. Try again.")
                return {"status": "ok"}

            if text == "status":
                send_message(sender, f"📌 State: {get_user_state(sender)} | Authenticated: {is_authenticated(sender)}")
                return {"status": "ok"}

            send_message(sender, "👋 Please say 'hello' to get started.")
            return {"status": "ok"}


        if not is_authenticated(sender):
            send_message(sender, "🔒 Please verify by saying 'hello' first.")
            return {"status": "ok"}

        # Button flow
        if msg_type == "interactive":
            button_id = msg["interactive"]["button_reply"]["id"]
            set_user_intent(sender, button_id)

            if button_id == "upload_invoice":
                send_message(sender, "📤 Please upload your invoice.")
            elif button_id == "upload_cheque":
                send_message(sender, "📤 Please upload a scanned cheque.")
            return {"status": "ok"}

        # Media handling
        if msg_type in ["image", "document"]:
            intent = get_user_intent(sender)
            if intent not in ["upload_invoice", "upload_cheque"]:
                send_message(sender, "❗ Please select an option first using the buttons.")
                return {"status": "ok"}

            media_id = msg[msg_type]["id"]
            meta_url = f"https://graph.facebook.com/v19.0/{media_id}"
            meta = requests.get(meta_url, params={"access_token": ACCESS_TOKEN}).json()
            media_url = meta.get("url")

            if not media_url:
                send_message(sender, "⚠️ Failed to get your file. Please try again.")
                return {"status": "ok"}

            try:
                file_bytes = requests.get(media_url, headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}).content
            except Exception as e:
                print("❌ Error downloading file:", e)
                send_message(sender, "⚠️ Failed to download your file.")
                return {"status": "ok"}

            try:
                ocr_text = ocr_from_bytes(file_bytes)
            except Exception as e:
                print("❌ OCR failed:", e)
                send_message(sender, "❌ OCR failed. Please upload a clear image or PDF.")
                return {"status": "ok"}

            email = get_user_email(sender)

            if intent == "upload_invoice":
                prompt = f"""
                    You are an intelligent invoice parser.
                    
                    From the OCR text below, extract invoice number, seller name, buyer name, date, and each item with quantity & amount.
                    
                    Return only multiple VALUES tuples in this format:
                    (email, invoice_number, sellers_name, buyers_name, date, item, quantity, amount)
                    
                    For example, output exactly like this:
                    ('{email}', 'INV001', 'SellerName', 'BuyerName', '2025-07-18', 'Desk', 10, 10000),
                    ('{email}', 'INV001', 'SellerName', 'BuyerName', '2025-07-18', 'Chair', 5, 5000)
                    
                    ⚠ Include the email as '{email}' in each tuple (taken from the user session).
                    Convert amounts to integers. Format date to YYYY-MM-DD.
                    Do NOT add INSERT INTO statement, comments, explanation, or code blocks — only the raw tuples separated by commas.
                    
                    OCR TEXT:
                    \"\"\"{ocr_text}\"\"\"
                    """
                try:
                    sql_response = ask_openai(prompt)
                    print("OpenAI response:", sql_response)
                    send_message(sender, sql_response)
            
                    # Parse returned tuples
                    rows = []
                    for line in sql_response.strip().splitlines():
                        line = line.strip().rstrip(',')
                        if line.startswith("(") and line.endswith(")"):
                            parts = [v.strip().strip("'") for v in line[1:-1].split(",")]
                            if len(parts) == 8:
                                rows.append(parts)
            
                    for row in rows:
                        email, invoice_number, sellers_name, buyers_name, date, item, quantity_str, amount_str = row
                        quantity = int(quantity_str)
                        amount = int(amount_str)
            
                        # Insert into upload_invoice
                        insert_result = supabase.table("upload_invoice").insert({
                            "email": email,
                            "invoice_number": invoice_number,
                            "sellers_name": sellers_name,
                            "buyers_name": buyers_name,
                            "date": date,
                            "item": item,
                            "quantity": quantity,
                            "amount": amount
                        }).execute()
            
                        # Match in tally_invoice
                        match_result = supabase.table("tally_invoice").select("*").match({
                            "invoice_number": invoice_number,
                            "sellers_name": sellers_name,
                            "buyers_name": buyers_name,
                            "date": date,
                            "item": item,
                            "quantity": quantity,
                            "amount": amount
                        }).execute()
            
                        is_match = bool(match_result.data)
                        print(f"✅ Match found: {is_match}")
            
                    send_message(sender, "✅ Invoice uploaded successfully and matched.")
            
                except Exception as e:
                    print("❌ Error processing invoice:", e)
                    send_message(sender, "⚠ Failed to process invoice. Try again.")

            elif intent == "upload_cheque":
                prompt = f"""
                    You are an intelligent cheque parser.
                    1. Only return the SQL query as plain text without any description, comments, code blocks, or extra characters.
                    2. No use of Markdown or enclosing query in ```sql or ``` blocks.
                    3. Generate the query in a single line or properly formatted with minimal whitespace.
                    4. Ensure the query uses valid SQL syntax that can be executed directly in SQL Server.
                    5.Dont use any /n in the code.
                    6.The name of table is "upload_cheique".
                    
                    Extract the following:
                    - Account Holder Name
                    - Receiver Name
                    - Cheque Date (DDMMYYYY)
                    - Bank Name
                    - Account Number
                    - Amount
                    
                    Return one SQL query like:
                    
                    INSERT INTO upload_cheique (email, payee_name, senders_name, amount, date, bank_name, account_number)
                    VALUES ('{email}', 'Receiver Name', 'Sender Name', 5000, '2025-07-01', 'Bank Name', '1234567890');
                    
                    Convert amount to integer, format date as YYYY-MM-DD.
                    
                    OCR TEXT:
                    \"\"\"{ocr_text}\"\"\"
                """

            try:

                sql_response = ask_openai(prompt)
                print("SQL to execute:", sql_response)
                send_message(sender, sql_response)

                # ⚡ Parse values tuples from OpenAI response
                rows = []
                for line in sql_response.strip().splitlines():
                    line = line.strip().rstrip(',')
                    if line.startswith("(") and line.endswith(")"):
                        parts = [v.strip().strip("'") for v in line[1:-1].split(",")]
                        if len(parts) == 7:  # invoice_number, sellers_name, buyers_name, date, item, quantity, amount
                            rows.append(parts)
                
                for row in rows:
                    invoice_number, sellers_name, buyers_name, date, item, quantity_str, amount_str = row
                    quantity = int(quantity_str)
                    amount = int(amount_str)
                
                    email = get_user_email(sender)  # ✅ always from session
                
                    # Insert
                    insert_result = supabase.table("upload_invoice").insert({
                        "email": email,
                        "invoice_number": invoice_number,
                        "sellers_name": sellers_name,
                        "buyers_name": buyers_name,
                        "date": date,
                        "item": item,
                        "quantity": quantity,
                        "amount": amount
                    }).execute()
                
                    # Match in tally_invoice
                    match_result = supabase.table("tally_invoice").select("*").match({
                        "invoice_number": invoice_number,
                        "sellers_name": sellers_name,
                        "buyers_name": buyers_name,
                        "date": date,
                        "item": item,
                        "quantity": quantity,
                        "amount": amount
                    }).execute()
                
                    is_match = bool(match_result.data)
                
                    # Update tally
                    inserted_id = insert_result.data[0]['id']
                    supabase.table("upload_invoice").update({"tally": is_match}).eq("id", inserted_id).execute()


                send_message(sender, "✅ Your document has been uploaded successfully.")
                send_message(sender, f"🧾 Cheque uploaded. Match found in tally_cheque: {is_match}")

            
            except Exception as e:
                print("❌ Error during OpenAI/DB processing:", e)
                send_message(sender, "⚠ Failed to understand or store the document. Try again.")

    except Exception as e:
        print("❌ Unhandled error:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})

    return {"status": "ok"}
