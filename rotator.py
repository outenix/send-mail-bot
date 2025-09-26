import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os

ACCOUNT_FILE = "account.json"
EMAIL_FILE = "email.json"


# =========================
# ACCOUNT HANDLING
# =========================
def load_accounts():
    if not os.path.exists(ACCOUNT_FILE):
        with open(ACCOUNT_FILE, "w") as f:
            json.dump([], f)

    with open(ACCOUNT_FILE, "r") as f:
        try:
            accounts = json.load(f)
        except json.JSONDecodeError:
            accounts = []

    return accounts


def save_accounts(accounts):
    with open(ACCOUNT_FILE, "w") as f:
        json.dump(accounts, f, indent=2)


def get_accounts():
    accounts = load_accounts()
    available = [acc for acc in accounts if acc.get("used", 0) < 2]
    usedup = [acc for acc in accounts if acc.get("used", 0) >= 2]
    return available, usedup


def rotate_account():
    available, _ = get_accounts()
    return available[0] if available else None


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


# =========================
# TARGET HANDLING
# =========================
def load_targets():
    if not os.path.exists(EMAIL_FILE):
        with open(EMAIL_FILE, "w") as f:
            json.dump({"targets": []}, f)

    with open(EMAIL_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {"targets": []}

    # Jika salah format (list), ubah jadi dict
    if isinstance(data, list):
        data = {"targets": data}

    if "targets" not in data:
        data["targets"] = []

    return data


def save_targets(data):
    with open(EMAIL_FILE, "w") as f:
        json.dump(data, f, indent=2)


def add_target(email_target):
    data = load_targets()
    if email_target not in data["targets"]:
        data["targets"].append(email_target)
    save_targets(data)


def get_targets():
    data = load_targets()
    return data.get("targets", [])


# =========================
# EMAIL SENDER (GMAIL APP PASSWORD)
# =========================
def send_mail(sender_email, app_password, target_email, subject, body):
    try:
        # Gunakan MIMEMultipart supaya fleksibel (bisa HTML/attachment juga kalau perlu)
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = target_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, app_password)  # pakai App Password Gmail
            server.sendmail(sender_email, target_email, msg.as_string())

        return True, "Email berhasil dikirim."
    except Exception as e:
        return False, str(e)
