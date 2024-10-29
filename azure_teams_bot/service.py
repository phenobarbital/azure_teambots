import importlib
from typing import Union
from aiohttp import web
from botbuilder.core.integration import aiohttp_error_middleware
from navconfig import config
from navconfig.logging import logging
from navigator.applications.base import BaseApplication  # pylint: disable=E0611
from navigator.types import WebApp   # pylint: disable=E0611
from .config import BotConfig
from .bots.abstract import AbstractBot
from .bots.base import BaseBot


logging.getLogger(name='msrest').setLevel(logging.INFO)

class AzureBots:
    """
    A bot handler class for integrating Bots with the Azure Bot Service using
    aiohttp and the Bot Framework SDK.

    This class sets up an aiohttp web application to listen for incoming
    bot messages and process them accordingly.
    Every bot utilizes the CloudAdapter for handling the authentication and
    communication with the Bot Framework Service.

    Attributes:
        _adapter (AdapterHandler): The adapter handler for processing
          incoming bot activities.
        logger (Logger): Logger instance for logging messages and errors.
        app_id (str): The Microsoft App ID for the bot, used
           for authentication with the Bot Framework.
        app_password (str): The Microsoft App Password for the bot,
          used for authentication.
        _config (BotConfig): Configuration object containing bot settings.
        _memory (MemoryStorage): In-memory storage for bot state management.
        _user_state (UserState): State management for user-specific data.
        _conversation_state (ConversationState): State management
          for conversation-specific data.
        bot (Bot): Instance of the bot logic handling user interactions.

    Methods:
        setup(app, route: str = "/api/messages") -> web.Application:
            Configures the aiohttp web application to handle bot messages
              and sets up state management.

        messages(request: web.Request) -> web.Response:
            The main handler for processing incoming HTTP requests
              containing bot activities.

    Example:
        # Initialize and setup the AzureBot with an aiohttp application
        bot = AzureBot()
        bot.setup(app)

    Note:
        Ensure that the MicrosoftAppId and MicrosoftAppPassword are
          securely stored and not hardcoded in production.
    """
    def __init__(
        self,
        app: web.Application,
        bots: list[Union[AbstractBot, str]] = None,
        **kwargs
    ):
        """
        Initializes a new instance of the AzureBots class.

        Args:
            **kwargs: Arbitrary keyword arguments containing
              the MicrosoftAppId and MicrosoftAppPassword.
        """
        self.bots: list = []
        self.logger = logging.getLogger('Navigator.Bots')
        self.logger.notice(
            f"AzureBot: Starting Azure Bot Service with {len(bots)} Bots."
        )
        # Other arguments:
        self._kwargs = kwargs
        self._bots = bots
        # Calling Setup:
        self.setup(app)

    def create_bot(self, config: Union[BotConfig, dict]):
        """
        Creates a New Bot instance and adds it to the AzureBot service.

        Args:
            config: Configuration object containing bot settings.

        Returns:
            An instance of the specified bot type.
        """
        pass

    def add_bot(self) -> AbstractBot:
        """
        Adds a new bot instance to the AzureBot service.

        Returns:
            An instance of the specified bot type.
        """
        pass

    def _load_bot(self, bot_name: str) -> AbstractBot:
        """
        Loads the bot logic based on the specified bot type.

        Returns:
            An instance of the specified bot type.
        """
        try:
            clspath = f"services.bot.bots.{bot_name}"
            bot_module = importlib.import_module(
                clspath
            )
            bot_class = getattr(bot_module, bot_name)
            return bot_class(
                app=self.app,
            )
        except (ImportError, AttributeError) as exc:
            self.logger.error(
                f"Failed to load bot: {exc}"
            )
            bot = bot_name.upper()
            client_id = config.get(f'{bot}_CLIENT_ID')
            client_secret = config.get(f'{bot}_CLIENT_SECRET')
            return BaseBot(
                bot_name=bot_name,
                app=self.app,
                client_id=client_id,
                client_secret=client_secret,
                route=f'/api/v1/{bot_name.lower()}/messages'
            )

    def setup(
        self,
        app: web.Application,
    ) -> web.Application:
        """
        Configures the aiohttp web application to handle
          bot messages at a specified route.

        Args:
            app: The aiohttp web application instance to configure.

        Returns:
            The configured aiohttp web Application instance.
        """
        if isinstance(app, BaseApplication):
            self.app = app.get_app()
        elif isinstance(app, WebApp):
            self.app = app  # register the app into the Extension
        # Add Error Handler:
        self.app.middlewares.append(aiohttp_error_middleware)
        # Bot Configuration of instances:
        for bot in self._bots:
            if isinstance(bot, str):
                bt = self._load_bot(bot)
            elif isinstance(bot, AbstractBot):
                bt = bot
            else:
                self.logger.warning(
                    "AzureBot: Invalid Bot Type."
                )
                continue
            bt.setup(self.app)
            self.bots.append(bt)
