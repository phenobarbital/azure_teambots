import pandas as pd
from navconfig import BASE_DIR
from navigator.handlers.types import AppHandler
# Tasker:
from navigator.background import BackgroundQueue
from navigator_auth import AuthHandler
from azure_teambots.conf import (
    MS_TENANT_ID,
    BOTDEV_CLIENT_ID,
    BOTDEV_CLIENT_SECRET,
)
try:
    from azure_teambots import AzureBots
    from azure_teambots.bots import EchoChannelBot
    from azure_teambots.bots.listener import TeamsChannelBot
    AZUREBOT_INSTALLED = True
except ImportError as exc:
    print(exc)
    AZUREBOT_INSTALLED = False


class Main(AppHandler):
    """
    Main App Handler for Parrot Application.
    """
    app_name: str = 'Parrot'
    enable_static: bool = True
    enable_pgpool: bool = True

    def configure(self):
        super(Main, self).configure()
        ### Auth System
        # create a new instance of Auth System
        auth = AuthHandler()
        auth.setup(self.app)
        # Tasker: Background Task Manager:
        tasker = BackgroundQueue(
            app=self.app,
            max_workers=5,
            queue_size=5
        )
        # Azure Bot:
        bot = EchoChannelBot(
            app=self.app,
            bot_name='EchoChannel',
            id='botdev',
            welcome_message="Hello! I'm EchoChannel. Mention me with 'echo' and I'll repeat your message!",
            client_id=BOTDEV_CLIENT_ID,
            client_secret=BOTDEV_CLIENT_SECRET,
            mention_text="echo",  # This is the trigger word
            debug_mode=True,      # Enable detailed logging
            strip_quotes=True,    # Remove quotes around the echoed text
        )
        botconfig = {
            "cls": "EchoChannelBot",
            "bot_name": "EchoChannel",
            "id": "botdev",
            "welcome_message": "Hello! I'm EchoChannel. Mention me with 'echo' and I'll repeat your message!",
            "mention_text": "echo",  # This is the trigger word
            "client_id": BOTDEV_CLIENT_ID,
            "client_secret": BOTDEV_CLIENT_SECRET,
            "debug_mode": True,      # Enable detailed logging
            "strip_quotes": True,    # Remove quotes around the echoed text
        }
        AzureBots(
            app=self.app,
            bots=[botconfig],
            tenant_id=MS_TENANT_ID
        )
