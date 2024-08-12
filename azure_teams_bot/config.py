""" Bot Configuration """
from .conf import (
    MS_CLIENT_ID,
    MS_CLIENT_SECRET,
)


class BotConfig:
    """Bot Configuration Class."""
    APP_ID: str = MS_CLIENT_ID
    APP_PASSWORD: str = MS_CLIENT_SECRET