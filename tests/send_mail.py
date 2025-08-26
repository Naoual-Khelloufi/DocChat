import ssl
import smtplib
from email.mime.text import MIMEText
import streamlit as st

#Load SMTP settings from secrets.toml
cfg = st.secrets["smtp"]

#Create a simple test message
msg = MIMEText("Congrats the test email was sent successfully!", "plain", "utf-8")
msg["subject"] = "SMTP Test"
msg["From"] = cfg["from"]
msg["To"] = cfg["user"] # will send to the same Gmail account

#Connect to the SMTP server and send the email
with smtplib.SMTP(cfg["host"], cfg["port"]) as s:
    #Enable TLS encryption
    s.starttls(context = ssl.create_default_context())
    #Login using Gmail user + app password
    s.login(cfg["user"], cfg["password"])
    #Send the message
    s.sendmail(msg["From"],[msg["To"]], msg.as_string())