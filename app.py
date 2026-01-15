from flask import Flask, render_template, request, jsonify
import json
import re

app = Flask(__name__)

def load_intents():
    with open("intents.json", "r", encoding="utf-8") as f:
        return json.load(f)

INTENTS = load_intents()

# ------------------ Core math helpers ------------------
def ohm_law(V, I, R):
    try:
        V = float(V) if V not in (None, "", "none") else None
        I = float(I) if I not in (None, "", "none") else None
        R = float(R) if R not in (None, "", "none") else None

        if V is None and I is not None and R is not None:
            return f"Voltage = {I * R} V"
        elif I is None and V is not None and R is not None:
            return f"Current = {V / R} A"
        elif R is None and V is not None and I is not None:
            return f"Resistance = {V / I} Ω"
        else:
            return "Enter any two values (V, I, R) to calculate the third."
    except Exception:
        return "Invalid input for Ohm's law."

def sp_resistors(values: str):
    try:
        parts = [x.strip() for x in values.split(",") if x.strip() != ""]
        R = [float(x) for x in parts]
        if len(R) < 2:
            return "Enter at least two resistors (e.g., 10,5,20)"
        series = sum(R)
        parallel = 1 / sum(1 / r for r in R)
        return f"Series = {series} Ω\nParallel = {parallel:.3f} Ω"
    except Exception:
        return "Invalid resistor list. Example: 10,5,20"

# ------------------ Intent matching ------------------
def match_intent(message: str):
    msg = message.lower().strip()
    for intent in INTENTS.get("intents", []):
        for pattern in intent.get("patterns", []):
            if pattern.lower() in msg:
                return intent
    return None

def handle_user_input(msg: str):
    msg_lower = msg.lower().strip()

    # "Explain" commands (front-end will open explanation panels)
    if "explain ohm" in msg_lower:
        return {"type": "explain", "topic": "ohm"}
    if "explain and" in msg_lower:
        return {"type": "explain", "topic": "and"}
    if "explain or" in msg_lower:
        return {"type": "explain", "topic": "or"}
    if "explain not" in msg_lower:
        return {"type": "explain", "topic": "not"}

    # Parse Ohm input like: V=10 I=2  (any order)
    if "v=" in msg_lower or "i=" in msg_lower or "r=" in msg_lower:
        def grab(tag):
            if tag not in msg_lower:
                return None
            # take token after tag up to whitespace
            return msg_lower.split(tag, 1)[1].strip().split()[0]

        V = grab("v=")
        I = grab("i=")
        R = grab("r=")
        return {"type": "text", "text": ohm_law(V, I, R)}

    # Resistor from chat: pull numbers and compute
    if any(k in msg_lower for k in ["resistor", "series", "parallel"]):
        nums = re.findall(r"\d+(?:\.\d+)?", msg_lower)
        if nums:
            return {"type": "text", "text": sp_resistors(",".join(nums))}

    # Intent-based short answers
    intent = match_intent(msg_lower)
    if intent:
        # pick the first response for simplicity
        responses = intent.get("responses", [])
        if responses:
            return {"type": "text", "text": responses[0]}

    return {"type": "text", "text": "I can explain Ohm’s Law, logic gates, or solve resistor problems."}

# ------------------ Routes ------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    msg = (data.get("message") or "").strip()
    if not msg:
        return jsonify({"type": "text", "text": "Type something first."})
    return jsonify(handle_user_input(msg))

@app.route("/api/ohm", methods=["POST"])
def api_ohm():
    data = request.get_json(force=True)
    V = data.get("V", "")
    I = data.get("I", "")
    R = data.get("R", "")
    return jsonify({"result": ohm_law(V, I, R)})

@app.route("/api/resistors", methods=["POST"])
def api_resistors():
    data = request.get_json(force=True)
    values = data.get("values", "")
    return jsonify({"result": sp_resistors(values)})

if __name__ == "__main__":
    app.run(debug=True)
