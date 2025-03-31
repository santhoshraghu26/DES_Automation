import csv
import requests
import smtplib
import ssl
import os
from email.message import EmailMessage
from datetime import datetime
from zoneinfo import ZoneInfo



# === LOGIN ===
def login(email="amit@davidenergy.com", password="pOcGbd2dtEA5BOlG8BM4a"):
    url = "https://truepriceenergy.com:8080/login"
    querystring = {"email": email, "password": password}
    response = requests.post(url, params=querystring, verify=False)
    return eval(response.text)["access_token"]

# === DOWNLOAD DATA ===
def get_data(access_token, curve, iso, strip, file_suffix):
    url = "https://truepriceenergy.com:8080/get_data"
    querystring = {
        "start": "2025-04-01",
        "end": "2030-04-01",
        "operating_day": "",
        "curve_type": curve,
        "iso": iso,
        "strip": strip,
        "history": False,
        "type": "csv"
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, params=querystring, headers=headers, verify=False)

    filename = f"{curve}_{iso}_{file_suffix}.csv"
    with open(filename, "wb") as file:
        file.write(response.content)
    return filename

# === SEND EMAIL with both attachments ===
def send_email(sender, password, recipients, subject, body, attachments):
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(body)

    for attachment_path in attachments:
        with open(attachment_path, "rb") as f:
            file_data = f.read()
            file_name = os.path.basename(attachment_path)
        msg.add_attachment(file_data, maintype="application", subtype="csv", filename=file_name)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
        smtp.login(sender, password)
        smtp.send_message(msg)

# === MAIN AUTOMATION ===
def automated_task():
    access_token = login()

    # Download energy and nonenergy NYISO data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    file1 = get_data(access_token, "energy", "nyiso", "7x8", f"energy_{timestamp}")
    file2 = get_data(access_token, "nonenergy", "nyiso", "7x24", f"nonenergy_{timestamp}")

    # Email setup
    sender_email = "soruganty@truelightenergy.com"
    sender_password = os.environ["EMAIL_PASSWORD"]

    send_email(
        sender=sender_email,
        password=sender_password,
        recipients=[
        "blarcher@truelightenergy.com",
        "arohan@truelightenergy.com",
        "mconstantine@truelightenergy.com"
    ],
        eastern_time = datetime.now(ZoneInfo("America/New_York"))
        subject=f"NYISO Energy & Nonenergy Data - {eastern_time.strftime('%Y-%m-%d %I:%M %p %Z')}",
        body="Hi Team,\n\nPlease find attached the latest NYISO energy and nonenergy data files.\n\nBest,\nSanthosh",
        attachments=[file1, file2]
    )

# Run now
if __name__ == "__main__":
    automated_task()
