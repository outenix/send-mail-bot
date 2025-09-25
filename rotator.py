import json, os, tempfile
from threading import Lock

ACCOUNT_FILE = "account.json"
EMAIL_FILE = "email.json"
MAX_USES = 2
_accounts_lock = Lock()

def ensure_file(path, default_content):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_content, f, indent=2)

def load_json(path, default_content):
    ensure_file(path, default_content)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    fd, tmp_path = tempfile.mkstemp(dir=".", prefix=".tmp_", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            json.dump(data, tmp, indent=2, ensure_ascii=False)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try: os.remove(tmp_path)
        except: pass
        raise

# ------------------------
# Account management
# ------------------------
def load_accounts():
    return load_json(ACCOUNT_FILE, [])

def save_accounts(accounts):
    save_json(ACCOUNT_FILE, accounts)

def add_account(email, app_password):
    with _accounts_lock:
        accounts = load_accounts()
        accounts.append({"email": email, "app_password": app_password, "used": 0})
        save_accounts(accounts)

def delete_used_accounts():
    with _accounts_lock:
        accounts = load_accounts()
        accounts = [a for a in accounts if a.get("used", 0) < MAX_USES]
        save_accounts(accounts)

def get_accounts():
    accounts = load_accounts()
    available = [a for a in accounts if a.get("used", 0) < MAX_USES]
    usedup = [a for a in accounts if a.get("used", 0) >= MAX_USES]
    return available, usedup

def get_next_account():
    accounts = load_accounts()
    for idx, acc in enumerate(accounts):
        if acc.get("used", 0) < MAX_USES:
            return acc, idx, accounts
    return None, -1, accounts

def increment_used(accounts, index):
    accounts[index]["used"] = accounts[index].get("used", 0) + 1
    save_accounts(accounts)

# ------------------------
# Email tujuan management
# ------------------------
def load_targets():
    return load_json(EMAIL_FILE, [])

def save_targets(targets):
    save_json(EMAIL_FILE, targets)

def add_target(email_target):
    targets = load_targets()
    targets.append({"target": email_target})
    save_targets(targets)

def get_first_target():
    targets = load_targets()
    return targets[0]["target"] if targets else None
