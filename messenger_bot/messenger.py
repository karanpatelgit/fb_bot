import random
import re
from database import Database
from ai import AIClient
from config import settings
from messenger import send_quick_replies, send_text_message

QUICK_MENU = [
    {"title": "🎬 Latest Content", "payload": "MENU_LATEST"},
    {"title": "💡 Ask Me Anything", "payload": "MENU_ASK"},
    {"title": "🎁 Exclusive Tips", "payload": "MENU_TIPS"},
    {"title": "📞 Contact Creator", "payload": "MENU_CONTACT"},
    {"title": "🌟 About Me", "payload": "MENU_ABOUT"},
]

TIPS_POOL = [
    "Daily consistency > perfection. Roz thoda karo.",
    "First 3 seconds hook strong rakho.",
    "Audience comments ka reply karo, trust banta hai.",
    "Batch content banao weekend pe to stay regular.",
    "Ek niche pe focus karo for faster growth.",
    "Storytelling add karo, sirf info mat do.",
    "Analytics weekly check karo, guesswork kam hoga.",
]


class MessageHandler:
    def __init__(self, db: Database, ai_client: AIClient):
        self.db = db
        self.ai = ai_client

    def handle_message(self, psid: str, message_id: str, text: str):
        if self.db.is_duplicate_message(message_id):
            return

        first_time = self.db.ensure_user(psid)
        clean_text = (text or "").strip()
        topic = self._detect_topic(clean_text)
        self.db.add_message(message_id, psid, "user", clean_text, topic=topic)

        if first_time:
            self.send_welcome(psid)

        if clean_text.lower() in {"stop", "unsubscribe"}:
            self.db.set_subscribed(psid, False)
            reply = "Done! Aap unsubscribe ho gaye. Wapas aana ho to 'start' bhejo 🙂"
            send_text_message(psid, reply)
            self.db.add_message(None, psid, "bot", reply, topic="unsubscribe")
            return
        if clean_text.lower() in {"start", "subscribe"}:
            self.db.set_subscribed(psid, True)

        special = self._special_response(psid, clean_text)
        if special:
            send_text_message(psid, special)
            self.db.add_message(None, psid, "bot", special, topic=topic)
            return

        history = self.db.get_last_messages(psid, 10)
        history_summary = " | ".join(f"{m['sender_type']}: {m['text']}" for m in history if m.get("text"))
        ai_reply, language = self.ai.chat(clean_text, history_summary)
        self.db.update_language(psid, language)
        send_text_message(psid, ai_reply)
        self.db.add_message(None, psid, "bot", ai_reply, topic=topic)

    def send_welcome(self, psid: str):
        msg = (
            f"Hey! Main {settings.creator_name} ka assistant hoon ✨\n"
            f"Yahan tum {settings.creator_niche} se related help, tips aur fun chats kar sakte ho!"
        )
        send_quick_replies(psid, msg, QUICK_MENU)

    def _special_response(self, psid: str, text: str) -> str | None:
        t = text.lower()
        if t in {"menu", "help"}:
            send_quick_replies(psid, "Yeh raha quick menu 👇", QUICK_MENU)
            return None
        if re.search(r"\breal person\b|\bhuman\b|creator se baat", t):
            if settings.creator_psid:
                send_text_message(settings.creator_psid, f"User {psid} requested human handoff.")
            return f"Main {settings.creator_name} ko notify kar raha hoon, wo jald hi reply karenge! 🙏"
        if t.startswith("/tips"):
            return "\n".join(f"{i+1}. {tip}" for i, tip in enumerate(random.sample(TIPS_POOL, 5)))
        if t.startswith("/quote"):
            return """"सपने वो नहीं जो नींद में आते हैं,
सपने वो हैं जो आपको सोने नहीं देते।" 💫"""
        if t.startswith("/joke"):
            return "Teacher: Homework kahan hai?\nStudent: Sir, network issue tha... notebook sync nahi hui 😅"
        if t.startswith("/fact"):
            return "Fact: Human brain images se text se 60,000x faster process karta hai. Isliye thumbnails matter karte hain!"

        name_match = re.search(r"(?:my name is|i am|mai|main)\s+([A-Za-z\u0900-\u097F ]{2,30})", text, re.I)
        if name_match:
            name = name_match.group(1).strip().title()
            self.db.update_name(psid, name)
            return f"Nice to meet you, {name}! 🤝"

        bday_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        if "birthday" in t and bday_match:
            self.db.update_birthday(psid, bday_match.group(1))
            return "Awesome! Birthday saved 🎉 Us din special wish pakka!"

        if any(x in t for x in ["price", "cost", "fees"]):
            return f"Pricing details yahan mil jayenge: {settings.price_info_url}"
        if "collab" in t:
            return f"Collab ke liye form fill karo: {settings.collab_form_url}"
        if any(x in t for x in ["buy", "purchase"]):
            return f"Purchase info ke liye yeh link check karo: {settings.purchase_url}"
        if any(x in t for x in ["support", "issue", "problem"]):
            return f"Support team yahan help karegi: {settings.support_url}"
        if any(x in t for x in ["idiot", "stupid", "hate", "gali"]):
            return "Chalo positive baat karte hain 🙏 Main help karne ke liye yahan hoon."
        return None

    def _detect_topic(self, text: str) -> str:
        t = text.lower()
        if any(x in t for x in ["price", "cost", "fees"]):
            return "pricing"
        if "collab" in t:
            return "collaboration"
        if any(x in t for x in ["buy", "purchase"]):
            return "purchase"
        if any(x in t for x in ["support", "issue", "problem"]):
            return "support"
        if t.startswith("/"):
            return t.split()[0].lstrip("/")
        return "general"
