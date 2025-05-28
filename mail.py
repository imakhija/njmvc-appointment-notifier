import os
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage

def sendAppointments(appts):
    # to configure, add your own email address and app password variables to the environment
    load_dotenv()
    GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

    msg = EmailMessage()
    msg["Subject"] = "NJMVC APPOINTMENTS AVAILABLE"
    msg.set_content(appts)
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = os.getenv("DELIVERY_ADDRESS") # email address where you want to receive appointment notifications

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        smtp.send_message(msg)