import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    page_access_token: str = os.getenv("PAGE_ACCESS_TOKEN", "")
    verify_token: str = os.getenv("VERIFY_TOKEN", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    admin_key: str = os.getenv("ADMIN_KEY", "")
    creator_name: str = os.getenv("CREATOR_NAME", "Creator")
    creator_niche: str = os.getenv("CREATOR_NICHE", "content creation")
    creator_psid: str = os.getenv("CREATOR_PSID", "")
    collab_form_url: str = os.getenv("COLLAB_FORM_URL", "https://example.com/collab")
    purchase_url: str = os.getenv("PURCHASE_URL", "https://example.com/offers")
    support_url: str = os.getenv("SUPPORT_URL", "https://example.com/support")
    price_info_url: str = os.getenv("PRICE_INFO_URL", "https://example.com/pricing")
    port: int = int(os.getenv("PORT", "5000"))
    sqlite_path: str = os.getenv("SQLITE_PATH", "bot.db")
    primary_model: str = "llama-3.3-70b-versatile"
    fallback_model: str = "llama-3.1-8b-instant"
    max_message_length: int = 2000


settings = Settings()
