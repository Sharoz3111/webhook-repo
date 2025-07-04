from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["github_webhooks"]
collection = db["events"]

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    event = request.headers.get('X-GitHub-Event')

    author = data.get("sender", {}).get("login")
    timestamp = datetime.utcnow().strftime('%d %B %Y - %I:%M %p UTC')

    if event == "push":
        to_branch = data.get("ref", "").split("/")[-1]
        message = f'{author} pushed to {to_branch} on {timestamp}'
    elif event == "pull_request":
        pr = data.get("pull_request", {})
        from_branch = pr.get("head", {}).get("ref")
        to_branch = pr.get("base", {}).get("ref")
        if pr.get("merged"):
            message = f'{author} merged branch {from_branch} to {to_branch} on {timestamp}'
        else:
            message = f'{author} submitted a pull request from {from_branch} to {to_branch} on {timestamp}'
    else:
        return jsonify({"message": "Ignored event"}), 200

    collection.insert_one({"message": message, "timestamp": datetime.utcnow()})
    return jsonify({"message": "Event stored"}), 200

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/events')
def get_events():
    events = list(collection.find().sort("timestamp", -1).limit(10))
    return jsonify([{"message": e["message"]} for e in events])
