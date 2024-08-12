import pandas as pd
from navconfig import BASE_DIR
from navigator.handlers.types import AppHandler
# Tasker:
from navigator.background import BackgroundQueue
from navigator_auth import AuthHandler
try:
    from azure_teams_bot import AzureBot
    from azure_teams_bot.bots import ChatBot, AgentBot
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
        odoo = ChatBot(
            app=self.app,
            bot_name='Oddie',
            welcome_message='Welcome to Odoo Bot, you can ask me anything about Odoo ERP.'
        )
        AzureBot(
            app=self.app,
            bots=[odoo],
            route='/api/oddie/messages'
        )
