""" Bot Configuration """
from .conf import (
    MS_CLIENT_ID,
    MS_CLIENT_SECRET,
)


class BotConfig:
    """Bot Configuration Class."""
    APP_ID: str = MS_CLIENT_ID
    APP_PASSWORD: str = MS_CLIENT_SECRET

    def __init__(self, **kwargs):
        self.APP_ID = kwargs.get('client_id', MS_CLIENT_ID)
        self.APP_PASSWORD = kwargs.get('client_secret', MS_CLIENT_SECRET)
