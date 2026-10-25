import ast
import operator
import os
import random
import re
from datetime import datetime, timedelta, timezone

from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=None)

IST = timezone(timedelta(hours=5, minutes=30))


def now_ist():
    return datetime.now(IST)


# ---------------------------------------------------------------------------
# Simple, safe maths: "2 plus 2", "10 divided by 4", "(3+4)*5"
# ---------------------------------------------------------------------------
OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ValueError("exponent too large")
        return OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
        return OPS[type(node.op)](_eval(node.operand))
    raise ValueError("unsupported")


def try_math(text):
    t = text.lower()
    for word, sym in [
        ("multiplied by", "*"), ("divided by", "/"), ("to the power of", "**"),
        ("plus", "+"), ("minus", "-"), ("times", "*"), ("into", "*"),
        ("x", "*"), ("mod", "%"),
    ]:
        t = re.sub(r"(?<=\d)\s*\b" + re.escape(word) + r"\b\s*(?=\d)", f" {sym} ", t) \
            if word == "x" else t.replace(word, f" {sym} ")
    expr = "".join(re.findall(r"[\d+\-*/().%\s]", t)).strip()
    if not re.search(r"\d\s*[+\-*/%]+\s*\(?-?\d", expr):
        return None
    try:
        value = _eval(ast.parse(expr, mode="eval"))
    except Exception:
        return None
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    elif isinstance(value, float):
        value = round(value, 6)
    return f"The answer is {value}."


# ---------------------------------------------------------------------------
# Rule list. Order matters: the first match wins, so specific rules go first.
# An answer can be a string or a function that returns a string.
# ---------------------------------------------------------------------------
RULES = [
    # --- about the bot ---
    (r"\b(daily routine|your routine|what do you do all day)\b",
     ["I'm a bot, so no morning chai for me. I just wait here 24/7 for your messages!"]),
    (r"\b(how are you|how r u|how do you do)\b",
     ["I'm doing great, thanks for asking! How about you?"]),
    (r"\b(your name|who are you|what are you)\b",
     ["I'm a little Python chatbot built with Flask."]),
    (r"\b(who (made|created|built) you|your (creator|developer|owner))\b",
     ["I was built with Python, HTML and CSS by my owner, and deployed on Render."]),
    (r"\b(how old are you|your age)\b",
     ["I was born the day I was deployed, so I'm very young!"]),
    (r"\b(where do you live|where are you from)\b",
     ["I live on a cloud server, somewhere on the internet."]),
    (r"\b(are you (a )?(human|real|robot|bot)|are you ai)\b",
     ["I'm a rule-based chatbot, not a human. I follow programmed rules."]),
    (r"\b(help|what can you do|commands)\b",
     ["I can chat, do simple maths (try '12 times 4'), tell the time and date, "
      "tell jokes, share fun facts and answer some basic questions."]),

    # --- time and date (India time) ---
    (r"\b(how many (numbers|digits) (are )?(in|on) (a |the )?clock)\b",
     ["A normal clock shows 12 numbers, from 1 to 12."]),
    (r"\b(what('s| is)? the time|current time|time now|time is it|\btime\b)\b",
     [lambda: "The time in India is " + now_ist().strftime("%I:%M %p") + "."]),
    (r"\b(what('s| is)? the date|today'?s? date|\bdate\b)\b",
     [lambda: "Today is " + now_ist().strftime("%A, %d %B %Y") + "."]),
    (r"\b(what day|which day|day is it|today)\b",
     [lambda: "Today is " + now_ist().strftime("%A") + "."]),
    (r"\b(how many days in a (week|year)|days in a week)\b",
     ["A week has 7 days and a normal year has 365 days (366 in a leap year)."]),
    (r"\b(how many months)\b",
     ["There are 12 months in a year."]),
    (r"\b(how many (hours|minutes|seconds))\b",
     ["A day has 24 hours, an hour has 60 minutes and a minute has 60 seconds."]),

    # --- fun ---
    (r"\bjoke\b",
     ["Why do programmers prefer dark mode? Because light attracts bugs.",
      "There are 10 kinds of people: those who understand binary and those who don't.",
      "Why did the computer go to the doctor? It had a virus.",
      "I would tell you a UDP joke, but you might not get it."]),
    (r"\b(fun fact|interesting fact|tell me a fact|fact)\b",
     ["Honey never spoils. Edible honey has been found in ancient Egyptian tombs.",
      "Octopuses have three hearts.",
      "A day on Venus is longer than a year on Venus.",
      "Bananas are berries, but strawberries are not."]),
    (r"\b(quote|motivat|inspire)\b",
     ["The secret of getting ahead is getting started.",
      "Small steps every day lead to big results.",
      "Don't watch the clock; do what it does. Keep going."]),
    (r"\b(riddle)\b",
     ["What has hands but can't clap? A clock!"]),
    (r"\b(flip a coin|toss a coin|coin toss)\b",
     [lambda: "It's " + random.choice(["heads", "tails"]) + "!"]),
    (r"\b(roll a dice|roll a die|dice)\b",
     [lambda: "You rolled a " + str(random.randint(1, 6)) + "."]),
    (r"\b(random number)\b",
     [lambda: "Your random number is " + str(random.randint(1, 100)) + "."]),

    # --- general knowledge ---
    (r"\belephant\b",
     ["An elephant is big. It's the largest land animal on Earth, weighing up to about 6,000 kg."]),
    (r"\b(ant|mouse|insect)\b.*\b(small|big)\b|\b(small|big)\b.*\b(ant|mouse|insect)\b",
     ["Those are small animals!"]),
    (r"\b(whale)\b",
     ["The blue whale is the largest animal ever known to have lived."]),
    (r"\b(tiger|lion)\b",
     ["Big cats are powerful hunters. The tiger is India's national animal."]),
    (r"\b(capital of india|india'?s capital)\b",
     ["The capital of India is New Delhi."]),
    (r"\b(capital of (the )?(usa|us|america|united states))\b",
     ["The capital of the USA is Washington, D.C."]),
    (r"\b(capital of (the )?(uk|england|britain))\b",
     ["The capital of the UK is London."]),
    (r"\b(capital of japan)\b",
     ["The capital of Japan is Tokyo."]),
    (r"\b(national animal of india)\b",
     ["The national animal of India is the Bengal tiger."]),
    (r"\b(national bird of india)\b",
     ["The national bird of India is the Indian peacock."]),
    (r"\b(prime minister of india)\b",
     ["I may be out of date on this one, so please check a news site for the current answer."]),
    (r"\b(largest planet|biggest planet)\b",
     ["Jupiter is the largest planet in our solar system."]),
    (r"\b(how many planets)\b",
     ["There are 8 planets in our solar system."]),
    (r"\b(largest ocean|biggest ocean)\b",
     ["The Pacific Ocean is the largest ocean."]),
    (r"\b(tallest mountain|highest mountain)\b",
     ["Mount Everest is the tallest mountain above sea level, at about 8,849 metres."]),
    (r"\b(what is python)\b",
     ["Python is a popular, beginner-friendly programming language. I'm written in it!"]),
    (r"\b(what is html)\b",
     ["HTML is the language that gives a web page its structure."]),
    (r"\b(what is css)\b",
     ["CSS styles web pages: colours, fonts, spacing and layout."]),
    (r"\b(what is (a )?chatbot)\b",
     ["A chatbot is a program that talks to people through text, like me."]),
    (r"\b(weather)\b",
     ["I can't check live weather yet, but a quick search for 'weather near me' will help."]),

    # --- chit-chat ---
    (r"\b(i am|i'm|im) (sad|upset|tired|bored|angry)\b",
     ["I'm sorry to hear that. Want a joke or a fun fact to cheer you up?"]),
    (r"\b(i am|i'm|im) (good|fine|great|happy|okay|ok)\b",
     ["Glad to hear that!"]),
    (r"\b(good morning)\b", ["Good morning! Hope you have a great day."]),
    (r"\b(good afternoon)\b", ["Good afternoon! How can I help?"]),
    (r"\b(good evening)\b", ["Good evening! What can I do for you?"]),
    (r"\b(good night)\b", ["Good night! Sleep well."]),
    (r"\b(hi|hello|hey|hii+|namaste|hola)\b",
     ["Hello! How can I help you today?", "Hi there! What can I do for you?"]),
    (r"\b(thanks|thank you|thx)\b",
     ["You're welcome!", "Happy to help!"]),
    (r"\b(sorry)\b", ["No problem at all!"]),
    (r"\b(i love you|love you)\b", ["That's kind of you! I'm just code, but I appreciate it."]),
    (r"\b(ok|okay|cool|nice|great|wow)\b", ["Glad you think so! Anything else?"]),
    (r"\b(bye|goodbye|see you|see ya)\b",
     ["Goodbye! Have a great day.", "See you soon!"]),
]

FALLBACKS = [
    "I don't know that one yet. Try 'help' to see what I can do.",
    "I'm still learning! You can ask me for a joke, a fun fact, the time, or a maths question.",
    "Hmm, I can't answer that. Could you ask it in a different way?",
]


def get_reply(message: str) -> str:
    text = message.lower().strip()

    # 1. maths first ("2 plus 2", "12*5")
    maths = try_math(text)
    if maths:
        return maths

    # 2. keyword rules
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
