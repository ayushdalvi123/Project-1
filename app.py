import os
import random
import re
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=None)

# ---------------------------------------------------------------------------
# Bot logic: simple rule-based replies. Replace get_reply() with an LLM/API
# call later if you want smarter answers.
# ---------------------------------------------------------------------------
RULES = [
    (r"\b(hi|hello|hey|namaste)\b",
     ["Hello! How can I help you today?", "Hi there! What can I do for you?"]),
    (r"\bhow are you\b",
     ["I'm just code, but I'm running great. How about you?"]),
    (r"\b(your name|who are you)\b",
     ["I'm a little Python chatbot built with Flask."]),
    (r"\b(time|clock)\b",
     [lambda: "The server time is " + datetime.now().strftime("%I:%M %p") + "."]),
    (r"\b(date|today)\b",
     [lambda: "Today is " + datetime.now().strftime("%A, %d %B %Y") + "."]),
    (r"\b(help|what can you do)\b",
     ["I can chat, tell you the time or date, and tell a joke. Try: 'tell me a joke'."]),
    (r"\bjoke\b",
     ["Why do programmers prefer dark mode? Because light attracts bugs.",
      "There are 10 kinds of people: those who understand binary and those who don't."]),
    (r"\b(thanks|thank you)\b",
     ["You're welcome!", "Happy to help!"]),
    (r"\b(bye|goodbye|see you)\b",
     ["Goodbye! Have a great day.", "See you soon!"]),
]

FALLBACKS = [
    "I'm not sure I understand. Could you rephrase that?",
    "Hmm, I don't know that one yet. Try asking for help.",
]


def get_reply(message: str) -> str:
    text = message.lower().strip()
    for pattern, answers in RULES:
        if re.search(pattern, text):
            answer = random.choice(answers)
            return answer() if callable(answer) else answer
    return random.choice(FALLBACKS)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/style.css")
def css():
    return send_from_directory(BASE_DIR, "style.css")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"reply": "Please type something."}), 400
    return jsonify({"reply": get_reply(message)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
