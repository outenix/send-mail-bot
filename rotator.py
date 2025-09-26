import smtplib
from email.mime.text import MIMEText
import json
import os

ACCOUNT_FILE = "account.json"
EMAIL_FILE = "email.json"


def load_accounts():
    if not os.path.exists(ACCOUNT_FILE):
        with open(ACCOUNT_FILE, "w") as f:
            json.dump([], f)
    with open(ACCOUNT_FILE, "r") as f:
        return json.load(f)


def save_accounts(accounts):
    with open(ACCOUNT_FILE, "w") as f:
        json.dump(accounts, f, indent=2)


def load_targets():
    if not os.path.exists(EMAIL_FILE):
        with open(EMAIL_FILE, "w") as f:
            json.dump({"targets": []}, f)
    with open(EMAIL_FILE, "r") as f:
        return json.load(f)


def save_targets(data):
    with open(EMAIL_FILE, "w") as f:
        json.dump(data, f, indent=2)


def rotate_account():
    accounts = load_accounts()
    for acc in accounts:
        if acc.get("used", 0) < 2:
            return acc
    return None


def mark_account_used(email):
    accounts = load_accounts()
    for acc in accounts:
        if acc["email"] == email:
            acc["used"] = acc.get("used", 0) + 1
    save_accounts(accounts)


def reset_used():
    accounts = load_accounts()
    for acc in accounts:
        acc["used"] = 0
    save_accounts(accounts)


def delete_used():
    accounts = load_accounts()
    accounts = [acc for acc in accounts if acc.get("used", 0) < 2]
    save_accounts(accounts)


def send_mail(sender_email, app_password, target_email, subject, body):
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["From"] = sender_email
        msg["To"] = target_email
        msg["Subject"] = subject

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.send_message(msg)

        return True, "Email berhasil dikirim."
    except Exception as e:
        return False, str(e)


def add_target(email_target):
    data = load_targets()
    if "targets" not in data:
        data["targets"] = []
    if email_target not in data["targets"]:
        data["targets"].append(email_target)
    save_targets(data)


def get_targets():
    data = load_targets()
    return data.get("targets", [])


# 🔹 Tambahan untuk kompatibilitas main.py
def get_accounts():
    accounts = load_accounts()
    available = [acc for acc in accounts if acc.get("used", 0) < 2]
    usedup = [acc for acc in accounts if acc.get("used", 0) >= 2]
    return available, usedup
