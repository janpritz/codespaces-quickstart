# rasa_files/faq_updater.py
# Flask microservice that accepts POST /update-faq and appends dynamic FAQ actions and flows
#
# Usage:
#   export FAQ_UPDATER_SECRET="your-secret"                # optional (recommended)
#   export RASA_ACTIONS_RESTART_CMD="supervisorctl restart rasa-actions"  # optional
#   python rasa_files/faq_updater.py
#
# The service expects JSON:
#   { "intent": "Enrollment Schedule", "description": "Handles queries about enrollment dates.", "restart_actions": false }
#
# It will:
#  - normalize intent -> enrollment_schedule
#  - append an action class to rasa_files/actions.py named ActionUtterEnrollmentSchedule
#  - append a flow block to rasa_files/data/flows/faqs_flow.yml named enrollment_schedule_flow
#  - optionally spawn a restart command if RASA_ACTIONS_RESTART_CMD is set (non-blocking)
#
# Safety:
#  - Uses file locks (filelock) while writing files.
#  - Optional shared secret verification via X-FAQ-UPDATER-TOKEN header (FAQ_UPDATER_SECRET env var).

from flask import Flask, request, jsonify
import os
from pathlib import Path
import re
import sys
import traceback
from filelock import FileLock
from datetime import datetime
import hmac
import subprocess

app = Flask(__name__)

# Paths (relative to this file)
ACTIONS_FILE = Path("actions/faqs.py")
FAQS_FLOW_FILE = Path("data/flows/faqs_flow.yml")

# Lock suffix and timeout
LOCK_SUFFIX = ".lock"
LOCK_TIMEOUT = 10

# Optional secret for simple verification
FAQ_UPDATER_SECRET = os.environ.get("FAQ_UPDATER_SECRET")

def normalize_intent(intent: str) -> str:
    """
    Normalizes intent according to rules:
     - lowercase
     - spaces => underscores
     - strip non-alphanumeric/underscore characters
    """
    s = intent.strip().lower()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    return s

def camel_case(s: str) -> str:
    parts = s.split("_")
    return "".join(p.capitalize() for p in parts if p)

def action_class_name(intent_norm: str) -> str:
    return f"ActionUtter{camel_case(intent_norm)}"

def action_function_name(intent_norm: str) -> str:
    return f"action_utter_{intent_norm}"

def flow_key(intent_norm: str) -> str:
    return f"{intent_norm}_flow"

def append_action_class(intent_norm: str) -> bool:
    """
    Appends an action class to actions.py.
    Returns True if appended, False if already exists.
    """
    cls_name = action_class_name(intent_norm)
    func_name = action_function_name(intent_norm)
    pattern = rf"class\s+{re.escape(cls_name)}\s*\("
    lock_path = ACTIONS_FILE + LOCK_SUFFIX
    os.makedirs(os.path.dirname(ACTIONS_FILE), exist_ok=True)
    # Ensure actions.py exists
    if not os.path.exists(ACTIONS_FILE):
        # create a basic file header to be safe
        with open(ACTIONS_FILE, "w", encoding="utf-8") as f:
            f.write("# actions.py (auto-generated header)\n\n")
            f.write("from typing import Any, Text, Dict, List, Optional\n")
            f.write("import requests\n")
            f.write("from rasa_sdk import Action, Tracker\n")
            f.write("from rasa_sdk.executor import CollectingDispatcher\n\n")
            f.write('LARAVEL_API_BASE = "https://your-laravel-app.com"\n\n')
            f.write("def fetch_faq_response(intent_normalized: str, timeout: float = 5.0) -> str:\n")
            f.write("    try:\n")
            f.write("        r = requests.get(f\"{LARAVEL_API_BASE}/api/faqs/{intent_normalized}\", timeout=timeout)\n")
            f.write("        r.raise_for_status()\n")
            f.write("        data = r.json()\n")
            f.write("        return data.get('response', 'No answer available.')\n")
            f.write("    except Exception as e:\n")
            f.write("        print(f'[actions.py] fetch error: {e}')\n")
            f.write("        return 'No answer available.'\n\n")
            f.write("# Dynamic FAQ actions will be appended below\n\n")

    with FileLock(lock_path, timeout=LOCK_TIMEOUT):
        with open(ACTIONS_FILE, "r+", encoding="utf-8") as f:
            content = f.read()
            if re.search(pattern, content):
                return False
            # Prepare class code
            class_code = f"""
class {cls_name}(Action):
    def name(self) -> str:
        return "{func_name}"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        reply = fetch_faq_response("{intent_norm}")
        dispatcher.utter_message(text=reply)
        return []
"""
            f.seek(0, os.SEEK_END)
            f.write(class_code)
    return True

def append_flow(intent_norm: str, description: str) -> bool:
    """
    Appends a flow block to faqs_flow.yml.
    Returns True if appended, False if already exists.
    """
    lock_path = FAQS_FLOW_FILE + LOCK_SUFFIX
    if not os.path.exists(FAQS_FLOW_FILE):
        # create empty file
        with open(FAQS_FLOW_FILE, "w", encoding="utf-8") as f:
            f.write("# FAQ flows (auto-appended)\n\n")

    key = flow_key(intent_norm)
    with FileLock(lock_path, timeout=LOCK_TIMEOUT):
        with open(FAQS_FLOW_FILE, "r+", encoding="utf-8") as f:
            content = f.read()
            # check for existing top-level key
            if re.search(rf"^{re.escape(key)}\s*:", content, flags=re.MULTILINE):
                return False
            # normalize description line: escape YAML-sensitive characters minimally
            desc_single = description.replace("\n", " ").replace(":", "\\:")
            flow_block = f"""
{key}:
  description: {desc_single}
  steps:
    - action: {action_function_name(intent_norm)}
"""
            f.seek(0, os.SEEK_END)
            f.write(flow_block)
    return True

def verify_secret(req) -> bool:
    """
    Verifies the request using a simple token header if FAQ_UPDATER_SECRET is set.
    Header: X-FAQ-UPDATER-TOKEN
    """
    if not FAQ_UPDATER_SECRET:
        return True
    token = req.headers.get("X-FAQ-UPDATER-TOKEN", "")
    return hmac.compare_digest(token, FAQ_UPDATER_SECRET)

@app.route("/update-faq", methods=["POST"])
def update_faq():
    try:
        if not verify_secret(request):
            return jsonify({"ok": False, "error": "unauthorized"}), 401
        data = request.get_json(force=True)
        intent = data.get("intent")
        description = data.get("description", "") or ""
        if not intent:
            return jsonify({"ok": False, "error": "intent required"}), 400
        intent_norm = normalize_intent(intent)
        action_appended = append_action_class(intent_norm)
        flow_appended = append_flow(intent_norm, description)
        # Optionally trigger a restart command (non-blocking) if requested or env var set
        restart_flag = data.get("restart_actions", False)
        if restart_flag:
            cmd = os.environ.get("RASA_ACTIONS_RESTART_CMD")
            if cmd:
                try:
                    subprocess.Popen(cmd, shell=True)
                except Exception:
                    print("Failed to spawn restart command", file=sys.stderr)
        return jsonify({
            "ok": True,
            "intent": intent,
            "intent_normalized": intent_norm,
            "action_appended": action_appended,
            "flow_appended": flow_appended
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("FAQ_UPDATER_PORT", 5005))
    app.run(host="0.0.0.0", port=port)