import pandas as pd
from navconfig import BASE_DIR
from navigator.handlers.types import AppHandler
# Tasker:
from navigator.background import BackgroundQueue
from navigator_auth import AuthHandler
from azure_teams_bot.conf import (
    MS_TENANT_ID,
    BOTDEV_CLIENT_ID,
    BOTDEV_CLIENT_SECRET,
)
try:
    from azure_teams_bot import AzureBots
    from azure_teams_bot.bots import EchoBot
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
        # if AZUREBOT_INSTALLED:
        # Odoo Test Bot:
        bot = EchoBot(
            app=self.app,
            bot_name='Edu',
            welcome_message='Welcome to Edu Bot, you can ask me anything about T-ROC.',
            client_id=BOTDEV_CLIENT_ID,
            client_secret=BOTDEV_CLIENT_SECRET,
            route='/api/edu/messages'
        )
        AzureBots(
            app=self.app,
            bots=[bot],
            tenant_id=MS_TENANT_ID
        )
