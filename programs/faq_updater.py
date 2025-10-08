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
import re
import sys
import traceback
from filelock import FileLock
from datetime import datetime
import hmac
import subprocess
from pathlib import Path

app = Flask(__name__)

# Paths (relative to this file)
# Paths (relative to this file)
ACTIONS_FILE = Path("actions/faqs.py")
FAQS_FLOW_FILE = Path("data/flows/ticketing_faq.yml")

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
    Includes debug prints for easier troubleshooting.
    """
    cls_name = action_class_name(intent_norm)
    func_name = action_function_name(intent_norm)
    pattern = rf"class\s+{re.escape(cls_name)}\s*\("
    lock_path = str(ACTIONS_FILE) + LOCK_SUFFIX
    os.makedirs(os.path.dirname(str(ACTIONS_FILE)), exist_ok=True)

    # Ensure actions.py exists
    if not os.path.exists(ACTIONS_FILE):
        try:
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
            print(f"[faq_updater] Created new actions file at {ACTIONS_FILE}")
        except Exception as e:
            print(f"[faq_updater] ERROR creating actions.py at {ACTIONS_FILE}: {e}", file=sys.stderr)
            traceback.print_exc()
            raise

    try:
        with FileLock(lock_path, timeout=LOCK_TIMEOUT):
            with open(ACTIONS_FILE, "r+", encoding="utf-8") as f:
                content = f.read()
                if re.search(pattern, content):
                    print(f"[faq_updater] Action class {cls_name} already exists in {ACTIONS_FILE}")
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
                print(f"[faq_updater] Appended action class {cls_name} to {ACTIONS_FILE}")
        return True
    except Exception as e:
        print(f"[faq_updater] ERROR appending action class {cls_name}: {e}", file=sys.stderr)
        traceback.print_exc()
        return False

def append_flow(intent_norm: str, description: str) -> bool:
    """
    Appends a flow block to faqs_flow.yml.
    Returns True if appended, False if already exists.
    Tries to preserve existing file indentation:
      - If file contains an indented flow key (under a 'flows:' section), append with same indent.
      - If file contains a top-level 'flows:' key, append under it with 2-space indent.
      - Otherwise append as a top-level flow block.
    """
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(str(FAQS_FLOW_FILE)), exist_ok=True)
    lock_path = str(FAQS_FLOW_FILE) + LOCK_SUFFIX
    try:
        if not os.path.exists(str(FAQS_FLOW_FILE)):
            # create empty file
            with open(str(FAQS_FLOW_FILE), "w", encoding="utf-8") as f:
                f.write("# FAQ flows (auto-appended)\n\n")
            print(f"[faq_updater] Created new flows file at {FAQS_FLOW_FILE}")
    except Exception as e:
        print(f"[faq_updater] ERROR creating flows file {FAQS_FLOW_FILE}: {e}", file=sys.stderr)
        traceback.print_exc()
        return False

    key = flow_key(intent_norm)
    try:
        with FileLock(lock_path, timeout=LOCK_TIMEOUT):
            with open(str(FAQS_FLOW_FILE), "r+", encoding="utf-8") as f:
                content = f.read()

                # If the exact key exists anywhere (top-level or indented), skip
                if re.search(rf"^\s*{re.escape(key)}\s*:", content, flags=re.MULTILINE):
                    print(f"[faq_updater] Flow {key} already exists in {FAQS_FLOW_FILE}")
                    return False

                # Detect indentation style:
                # 1) look for an indented flow key (e.g., "  appendix_f_flow:")
                m = re.search(r"^(\s+)[a-z0-9_]+_flow\s*:", content, flags=re.MULTILINE)
                if m:
                    indent = m.group(1)
                    print(f"[faq_updater] Detected indented flow style (indent={len(indent)} spaces)")
                else:
                    # 2) detect a top-level 'flows:' section
                    has_flows_section = bool(re.search(r'^\s*flows\s*:\s*$', content, flags=re.MULTILINE))
                    if has_flows_section:
                        indent = "  "  # default 2-space indent under flows:
                        print("[faq_updater] Detected 'flows:' section; will append under it with 2-space indent")
                    else:
                        indent = None
                        print("[faq_updater] No flows section detected; will append top-level flow")

                desc_single = description.replace("\n", " ").replace(":", "\\:")

                if indent is not None:
                    # Append under flows: (indented block)
                    flow_block = f"""

{indent}{key}:
{indent}  description: {desc_single}
{indent}  steps:
{indent}    - action: {action_function_name(intent_norm)}
"""
                else:
                    # Append as top-level flow
                    flow_block = f"""

{key}:
  description: {desc_single}
  steps:
    - action: {action_function_name(intent_norm)}
"""

                f.seek(0, os.SEEK_END)
                f.write(flow_block)
                print(f"[faq_updater] Appended flow {key} to {FAQS_FLOW_FILE} (indent={'top' if indent is None else len(indent)})")
        return True
    except Exception as e:
        print(f"[faq_updater] ERROR appending flow {key}: {e}", file=sys.stderr)
        traceback.print_exc()
        return False

def verify_secret(req) -> bool:
    """
    Verifies the request using a simple token header if FAQ_UPDATER_SECRET is set.
    Header: X-FAQ-UPDATER-TOKEN
    Prints header for debugging (but avoids printing secret value).
    """
    if not FAQ_UPDATER_SECRET:
        print("[faq_updater] No FAQ_UPDATER_SECRET configured — accepting requests without token")
        return True
    token = req.headers.get("X-FAQ-UPDATER-TOKEN", "")
    if not token:
        print("[faq_updater] Missing X-FAQ-UPDATER-TOKEN header")
        return False
    # Debug: do not print token value directly; just show presence and length
    print(f"[faq_updater] Received token header of length {len(token)}")
    return hmac.compare_digest(token, FAQ_UPDATER_SECRET)

@app.route("/update-faq", methods=["POST"])
def update_faq():
    try:
        print("[faq_updater] /update-faq called")
        # Print headers for debugging (avoid printing secret value)
        for k, v in request.headers.items():
            if k.lower() == "x-faq-updater-token":
                print(f"[faq_updater] Header {k}: <HIDDEN token length {len(v)}>")
            else:
                print(f"[faq_updater] Header {k}: {v}")
        if not verify_secret(request):
            print("[faq_updater] Secret verification failed")
            return jsonify({"ok": False, "error": "unauthorized"}), 401

        data = request.get_json(force=True)
        print(f"[faq_updater] Payload: {data}")

        intent = data.get("intent")
        description = data.get("description", "") or ""
        if not intent:
            print("[faq_updater] Missing 'intent' in payload")
            return jsonify({"ok": False, "error": "intent required"}), 400

        intent_norm = normalize_intent(intent)
        print(f"[faq_updater] Normalized intent: {intent_norm}")

        # Attempt to append action and flow, capture errors separately
        try:
            action_appended = append_action_class(intent_norm)
        except Exception as e:
            print(f"[faq_updater] Exception while appending action for {intent_norm}: {e}", file=sys.stderr)
            traceback.print_exc()
            return jsonify({"ok": False, "error": "action_append_failed", "details": str(e)}), 500

        try:
            flow_appended = append_flow(intent_norm, description)
        except Exception as e:
            print(f"[faq_updater] Exception while appending flow for {intent_norm}: {e}", file=sys.stderr)
            traceback.print_exc()
            return jsonify({"ok": False, "error": "flow_append_failed", "details": str(e)}), 500

        # Optionally trigger a restart command (non-blocking) if requested or env var set
        restart_flag = data.get("restart_actions", False)
        if restart_flag:
            cmd = os.environ.get("RASA_ACTIONS_RESTART_CMD")
            if cmd:
                try:
                    print(f"[faq_updater] Spawning restart command: {cmd}")
                    subprocess.Popen(cmd, shell=True)
                except Exception as e:
                    print(f"[faq_updater] Failed to spawn restart command: {e}", file=sys.stderr)
                    traceback.print_exc()

        result = {
            "ok": True,
            "intent": intent,
            "intent_normalized": intent_norm,
            "action_appended": action_appended,
            "flow_appended": flow_appended
        }
        print(f"[faq_updater] Result: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"[faq_updater] Unexpected error in /update-faq: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("FAQ_UPDATER_PORT", 5001))
    app.run(host="0.0.0.0", port=port)