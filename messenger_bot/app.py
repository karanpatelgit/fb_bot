import logging
from flask import Flask, jsonify, request

from ai import AIClient
from config import settings
from database import Database
from handlers import MessageHandler
from messenger import send_text_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
db = Database(settings.sqlite_path)
ai_client = AIClient()
handler = MessageHandler(db, ai_client)


@app.get("/webhook")
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == settings.verify_token:
        return challenge or "", 200
    return "Forbidden", 403


@app.post("/webhook")
def webhook():
    data = request.get_json(silent=True) or {}
    try:
        if data.get("object") == "page":
            for entry in data.get("entry", []):
                for messaging_event in entry.get("messaging", []):
                    message = messaging_event.get("message")
                    sender = messaging_event.get("sender", {})
                    if not message or "text" not in message:
                        continue
                    handler.handle_message(
                        psid=sender.get("id", ""),
                        message_id=message.get("mid", ""),
                        text=message.get("text", ""),
                    )
    except Exception:
        logger.exception("Webhook processing failed")
    return "EVENT_RECEIVED", 200


@app.post("/broadcast")
def broadcast():
    payload = request.get_json(silent=True) or {}
    if payload.get("admin_key") != settings.admin_key:
        return jsonify({"error": "unauthorized"}), 401

    message = (payload.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message required"}), 400

    subscribers = db.get_subscribers()
    sent = 0
    for psid in subscribers:
        send_text_message(psid, message)
        db.add_message(None, psid, "bot", message, topic="broadcast")
        sent += 1
    return jsonify({"ok": True, "sent": sent})


@app.get("/stats")
def stats():
    return jsonify(db.get_stats())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=settings.port)
