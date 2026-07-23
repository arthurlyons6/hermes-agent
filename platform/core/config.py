import os
from pathlib import Path
from dotenv import load_dotenv
from core.vault import optional

load_dotenv()


class Config:
    def __init__(self) -> None:
        self.TELEGRAM_BOT_TOKEN: str = optional("TELEGRAM_BOT_TOKEN", "")
        self.HERMES_HOME: str = optional("HERMES_HOME", str(Path.home() / "AppData" / "Local" / "hermes"))
        self.BLACKGOLD_GROUP: str = optional("BLACKGOLD_GROUP", "-1005488739957")
        self.DAILY_BRIEF_CRON: str = optional("DAILY_BRIEF_CRON", "0 8 * * *")
        self.WEEKLY_AUDIT_CRON: str = optional("WEEKLY_AUDIT_CRON", "0 6 * * 1")
