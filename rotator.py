import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
import os
import re

ACCOUNT_FILE = "account.json"
EMAIL_FILE = "email.json"
EXTRA_INFO_FILE = "extra_info.txt"
LOG_FILE = "logs.zip"


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

    # Konversi format lama: [{"target": "email"}] → {"targets": ["email"]}
    if isinstance(data, list):
        fixed_targets = []
        for item in data:
            if isinstance(item, dict) and "target" in item:
                fixed_targets.append(item["target"])
            elif isinstance(item, str):
                fixed_targets.append(item)
        data = {"targets": fixed_targets}

    # Pastikan key "targets" ada
    if "targets" not in data:
        data["targets"] = []

    return data


def save_targets(data):
    with open(EMAIL_FILE, "w") as f:
        json.dump(data, f, indent=2)


def is_valid_email(email: str) -> bool:
    if not email or not isinstance(email, str):
        return False
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None


def add_target(email_target):
    data = load_targets()
    email_target = str(email_target).strip()

    if not is_valid_email(email_target):
        return False

    if email_target not in data["targets"]:
        data["targets"].append(email_target)

    save_targets(data)
    return True


def get_targets():
    data = load_targets()
    return data.get("targets", [])


# =========================
# EMAIL SENDER (GMAIL APP PASSWORD)
# =========================
def send_mail(sender_email, app_password, target_email, subject, body):
    try:
        target_email = str(target_email).strip()
        if not is_valid_email(target_email):
            return False, "Alamat email tujuan tidak valid."

        subject = str(subject)
        body = str(body)

        # Tambahkan extra info jika ada
        if os.path.exists(EXTRA_INFO_FILE):
            with open(EXTRA_INFO_FILE, "r", encoding="utf-8") as f:
                extra_text = f.read().strip()
            if extra_text:
                body += "\n\n" + extra_text

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = target_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        # Sisipkan file logs.zip jika ada
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "rb") as f:
                part = MIMEBase("application", "zip")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{os.path.basename(LOG_FILE)}"',
                )
                msg.attach(part)

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, app_password)  # Gunakan App Password Gmail
            server.sendmail(sender_email, [target_email], msg.as_string())

        return True, "Email berhasil dikirim."
    except Exception as e:
        return False, str(e)
