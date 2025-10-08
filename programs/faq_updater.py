from flask import Flask, request, jsonify
import os

app = Flask(__name__)

ACTIONS_FILE = "actions/actions.py"
FAQ_FLOW_FILE = "data/flows/faqs_flow.yml"
LARAVEL_API_BASE = "https://your-laravel-app.com/api/faqs"

@app.route("/update-faq", methods=["POST"])
def update_faq():
    data = request.get_json()
    intent = data["intent"]
    description = data.get("description", f"Handles {intent} related questions")

    action_name = f"action_utter_{intent}"
    class_name = to_camel_case(action_name)

    # --- Append new action class to actions.py ---
    with open(ACTIONS_FILE, "a") as f:
        f.write(f"""

class {class_name}(Action):
    def name(self):
        return "{action_name}"

    def run(self, dispatcher, tracker, domain):
        import requests
        intent = "{intent}"
        url = "{LARAVEL_API_BASE}/" + intent
        res = requests.get(url).json()
        dispatcher.utter_message(text=res.get("response"))
        return []
""")

    # --- Append new flow ---
    with open(FAQ_FLOW_FILE, "a") as f:
        f.write(f"""
{intent}_flow:
    description: {description}
    steps:
      - action: {action_name}
""")

    return jsonify({"status": "success", "intent": intent, "action": action_name})

def to_camel_case(s):
    return ''.join(word.title() for word in s.split('_'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
