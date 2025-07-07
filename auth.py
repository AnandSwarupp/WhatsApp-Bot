import random
import smtplib
from email.mime.text import MIMEText

user_states = {}
user_emails = {}
user_otps = {}
user_intent = {}

def get_user_state(sender):
    return user_states.get(sender)

def set_user_state(sender, state):
    user_states[sender] = state

def set_user_email(sender, email):
    user_emails[sender] = email

def get_user_email(sender):
    return user_emails.get(sender)

def set_user_otp(sender, otp):
    user_otps[sender] = otp

def get_user_otp(sender):
    return user_otps.get(sender)

def clear_user(sender):
    user_states.pop(sender, None)
    user_otps.pop(sender, None)
    user_emails.pop(sender, None)

def send_otp_email(to_email, otp):
    msg = MIMEText(f"Your OTP is: {otp}")
    msg["Subject"] = "Your FinBot OTP"
    msg["From"] = "youremail@example.com"
    msg["To"] = to_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login("youremail@example.com", "your_app_password")
            server.send_message(msg)
        print(f"✅ OTP sent to {to_email}")
    except Exception as e:
        print("❌ Email error:", e)

def generate_and_send_otp(sender, email):
    otp = str(random.randint(100000, 999999))
    set_user_otp(sender, otp)
    set_user_state(sender, "awaiting_otp")
    send_otp_email(email, otp)

def set_user_intent(sender, intent):
    user_intent[sender] = intent

def get_user_intent(sender):
    return user_intent.get(sender, "unknown")

