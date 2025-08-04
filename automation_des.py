# Re-running the full code after state reset to ensure all functions are redefined properly.

import os
import csv
import requests
import smtplib
import ssl
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
def get_data(access_token, start_date, end_date, curve, iso, strip, history, file_suffix):
    url = "https://truepriceenergy.com:8080/get_data"
    querystring = {
        "start": start_date,
        "end": end_date,
        "curve_type": curve,
        "iso": iso,
        "strip": strip,
        "history": history,
        "type": "csv"
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, params=querystring, headers=headers, verify=False)
    filename = f"{curve}_{iso}_{file_suffix}.csv"

    with open(filename, "wb") as file:
        file.write(response.content)
        
    return filename, response.status_code

# === SEND EMAIL ===
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

# === MAIN AUTOMATION TASK ===
def automated_task():
    access_token = login()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')

    # Define all curve combinations
    combinations = [
        # Energy
        ("energy", "ercot", ['7x8', '5x16', '2x16']),
        ("energy", "isone", ['7x8', '5x16', '2x16']),
        ("energy", "nyiso", ['7x8', '5x16', '2x16']),
        ("energy", "miso", ['7x8', '5x16', '2x16']),
        ("energy", "pjm", ['7x8', '5x16', '2x16']),
        # Nonenergy
        ("nonenergy", "pjm", ['7x24']),
        ("nonenergy", "ercot", ['7x24']),
        ("nonenergy", "nyiso", ['7x24']),
        ("nonenergy", "isone", ['7x24']),
        # REC
        ("rec", "ercot", ['7x24']),
        ("rec", "isone", ['7x24']),
        ("rec", "nyiso", ['7x24']),
        ("rec", "pjm", ['7x24']),
    ]

    attachments = []
    status_logs = []

    for curve, iso, strip in combinations:
        history = True if (curve == "rec" and iso == "isone") else False
        filename, status = get_data(
            access_token=access_token,
            start_date="2000-01-01",
            end_date="9999-12-31",
            curve=curve,
            iso=iso,
            strip=strip,
            history=history,
            file_suffix=timestamp
        )
        attachments.append(filename)
        if status == 200:
            status_logs.append(f"Fetched {curve.upper()} - {iso.upper()} | Status: {status}")
        else:
            status_logs.append(f"[ERROR] Failed to fetch data for {curve.upper()} - {iso.upper()} (Status Code: {status})")

    # Email configuration
    sender_email = "soruganty@truelightenergy.com"
    sender_password = os.environ["EMAIL_PASSWORD"]
    #sender_password = os.environ.get("EMAIL_PASSWORD", "your_password_here")  # Replace or load from env
    recipients = [
        "blarcher@truelightenergy.com",
        "arohan@truelightenergy.com",
        "mconstantine@truelightenergy.com",
        "soruganty@truelightenergy.com"
    ]
    eastern_time = datetime.now(ZoneInfo("America/New_York"))
    subject = f"DES API Report - {eastern_time.strftime('%Y-%m-%d %I:%M %p %Z')}"
    body = (
        "Hi Team,\n\n"
        "Please find attached DES API Report for energy, nonenergy, and rec curve data files for each ISO.\n\n"
        "Fetch Status Summary:\n" +
        "\n".join(status_logs) +
        "\n\nBest,\nSantosh Oruganty"
    )
    
    send_email(sender_email, sender_password, recipients, subject, body, attachments)

# Run the task
automated_task()

