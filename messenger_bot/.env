import logging
import re
import time
from functools import lru_cache
from groq import Groq

from config import settings

logger = logging.getLogger(__name__)


def detect_language(text: str) -> str:
    devanagari = bool(re.search(r"[\u0900-\u097F]", text))
    ascii_letters = bool(re.search(r"[A-Za-z]", text))
    if devanagari and not ascii_letters:
        return "hindi"
    if ascii_letters and not devanagari and all(ord(ch) < 128 for ch in text):
        return "english"
    return "hinglish"


def system_prompt(creator_name: str, creator_niche: str, history_summary: str, language: str) -> str:
    base = (
        f"You are {creator_name}'s AI assistant for Facebook Messenger. "
        f"Creator niche: {creator_niche}. You are friendly, funny, human-like, and engaging. "
        "Keep replies 2-4 short lines max with natural emojis. Never sound robotic. "
        "Do not reveal you are AI unless directly asked. If asked personal/private creator life, politely redirect. "
    )
    if language == "english":
        style = "Reply only in natural English."
    elif language == "hindi":
        style = "केवल प्राकृतिक हिंदी में जवाब दें।"
    else:
        style = "Reply in natural Hinglish (Hindi + English mix) like Indian creators."
    return f"{base} {style} Context from earlier chat: {history_summary}"


class AIClient:
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)

    @lru_cache(maxsize=256)
    def cached_short_response(self, prompt_key: str) -> str:
        return self._generate(prompt_key, language="hinglish", history_summary="")

    def _generate(self, user_text: str, language: str, history_summary: str) -> str:
        models = [settings.primary_model, settings.fallback_model]
        last_error = None
        for model in models:
            for attempt in range(3):
                try:
                    completion = self.client.chat.completions.create(
                        model=model,
                        temperature=0.7,
                        max_tokens=220,
                        messages=[
                            {
                                "role": "system",
                                "content": system_prompt(
                                    settings.creator_name,
                                    settings.creator_niche,
                                    history_summary,
                                    language,
                                ),
                            },
                            {"role": "user", "content": user_text},
                        ],
                    )
                    return completion.choices[0].message.content.strip()
                except Exception as exc:
                    last_error = exc
                    logger.warning("Groq call failed model=%s attempt=%s error=%s", model, attempt + 1, exc)
                    time.sleep(0.7 * (attempt + 1))
        logger.error("Groq failed for all models: %s", last_error)
        return "Ek second... 😅 dobara try karo!"

    def chat(self, user_text: str, history_summary: str) -> tuple[str, str]:
        language = detect_language(user_text)
        if len(user_text.strip()) < 40:
            return self.cached_short_response(f"{language}:{user_text.strip().lower()}"), language
        return self._generate(user_text, language, history_summary), language
