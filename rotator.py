import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ACCOUNTS_FILE = "accounts.json"
TARGETS_FILE = "targets.json"


# =========================
# JSON HANDLING
# =========================
def load_json(path, default):
    if not os.path.exists(path):
        save_json(path, default)
        return default
    with open(path, "r") as f:
        try:
            return json.load(f)
        except:
            return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_accounts():
    return load_json(ACCOUNTS_FILE, [])


def save_accounts(accounts):
    save_json(ACCOUNTS_FILE, accounts)


def load_targets():
    return load_json(TARGETS_FILE, {"targets": []})


def save_targets(targets):
    save_json(TARGETS_FILE, targets)


# =========================
# ACCOUNT MANAGEMENT
# =========================
def get_accounts():
    accounts = load_accounts()
    available = [a for a in accounts if a.get("used", 0) < 2]
    usedup = [a for a in accounts if a.get("used", 0) >= 2]
    return available, usedup


def rotate_account():
    accounts = load_accounts()
    available = [a for a in accounts if a.get("used", 0) < 2]
    if not available:
        return None
    return available[0]  # ambil yang pertama


def mark_account_used(email):
    accounts = load_accounts()
    for acc in accounts:
        if acc["email"] == email:
            acc["used"] = acc.get("used", 0) + 1
    save_accounts(accounts)


def delete_used():
    accounts = load_accounts()
    accounts = [a for a in accounts if a.get("used", 0) < 2]
    save_accounts(accounts)


# =========================
# TARGET MANAGEMENT
# =========================
def get_targets():
    data = load_targets()
    return data.get("targets", [])


def add_target(email_target):
    data = load_targets()
    if email_target not in data["targets"]:
        data["targets"].append(email_target)
    save_targets(data)


# =========================
# SENDING EMAIL
# =========================
def send_mail(sender_email, app_password, target_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = target_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, target_email, msg.as_string())
        server.quit()

        return True, "Email sent"
    except Exception as e:
        return False, str(e)
