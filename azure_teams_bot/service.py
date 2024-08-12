import os
import importlib
from http import HTTPStatus
from typing import Optional, Union
from aiohttp import web
from botbuilder.core import (
    ConversationState,
    MemoryStorage,
    UserState,
)
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity
from botbuilder.integration.aiohttp import (
    ConfigurationBotFrameworkAuthentication
)
from navconfig.logging import logging
from navigator.applications.base import BaseApplication  # pylint: disable=E0611
from navigator.types import WebApp   # pylint: disable=E0611
from .adapters import AdapterHandler
from .conf import (
    MS_CLIENT_ID,
    MS_CLIENT_SECRET,
)
from .config import BotConfig
from .bots.abstract import AbstractBot
from .bots.base import BaseBot


class AzureBot:
    """
    A bot handler class for integrating a bot with the Azure Bot Service using
    aiohttp and the Bot Framework SDK.

    This class sets up an aiohttp web application to listen for incoming
    bot messages and process them accordingly.
    It utilizes the CloudAdapter for handling the authentication and
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
        route: str = '/api/v1/messages',
        bots: list[Union[AbstractBot, str]] = None,
        config: Optional[Union[BotConfig, dict]] = None,
        client_id: str = None,
        secret_id: str = None,
        **kwargs
    ):
        """
        Initializes a new instance of the AzureBot class.

        Args:
            **kwargs: Arbitrary keyword arguments containing
              the MicrosoftAppId and MicrosoftAppPassword.
        """
        self._adapter = None
        self.bots: list = []
        self.logger = logging.getLogger('Navigator.Bot')
        if config:
            if isinstance(config, BotConfig):
                self._config = config
            elif isinstance(config, dict):
                self._config = BotConfig(**config)
            else:
                raise ValueError(
                    "AzureBot: Invalid Config for BotConfig."
                )
            self.app_id = self._config.APP_ID
            self.app_password = self._config.APP_PASSWORD
        else:
            self.app_id = client_id if client_id else MS_CLIENT_ID
            self.app_password = secret_id if secret_id else MS_CLIENT_SECRET
            self._config = BotConfig()
            self._config.APP_ID = self.app_id
            self._config.APP_PASSWORD = self.app_password
        os.environ["MicrosoftAppId"] = self.app_id
        os.environ["MicrosoftAppPassword"] = self.app_password
        self.logger.notice(
            "AzureBot: Starting Azure Bot Service..."
        )
        # Other arguments:
        self._kwargs = kwargs
        self._bots = bots
        # Calling Setup:
        self.setup(app, route)

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
                conversation_state=self._conversation_state,
                user_state=self._user_state
            )
        except (ImportError, AttributeError) as exc:
            self.logger.error(
                f"Failed to load bot: {exc}"
            )
            return BaseBot(
                app=self.app,
                conversation_state=self._conversation_state,
                user_state=self._user_state
            )

    def setup(
        self,
        app: web.Application,
        route: str = "/api/messages"
    ) -> web.Application:
        """
        Configures the aiohttp web application to handle
          bot messages at a specified route.

        Args:
            app: The aiohttp web application instance to configure.
            route: The HTTP route to listen for incoming bot messages.
             Defaults to "/api/messages".

        Returns:
            The configured aiohttp web Application instance.
        """
        if isinstance(app, BaseApplication):
            self.app = app.get_app()
        elif isinstance(app, WebApp):
            self.app = app  # register the app into the Extension
        # Add Error Handler:
        self.app.middlewares.append(aiohttp_error_middleware)
        # Memory and User State Management
        self._memory = MemoryStorage()
        self._user_state = UserState(self._memory)
        self._conversation_state = ConversationState(self._memory)
        # adapter
        self._adapter = AdapterHandler(
            config=self._config,
            logger=self.logger,
            conversation_state=self._conversation_state
        )
        # Bot instances:
        for bot in self._bots:
            if isinstance(bot, str):
                self.bots.append(self._load_bot(bot))
            elif isinstance(bot, AbstractBot):
                bot.app = self.app
                bot.conversation_state = self._conversation_state
                bot.user_state = self._user_state
                self.bots.append(bot)
            else:
                raise ValueError(
                    "AzureBot: Invalid Bot Type."
                )
        # adding routes:
        self.app.router.add_post(route, self.messages)
        # add bot routes to exception routes
        try:
            _auth = self.app['auth']
            _auth.add_exclude_list(route)
        except Exception as e:
            self.logger.error(f"Auth Error: {e}")

    # Bot message handler:
    # Listen for incoming requests on /api/messages
    async def messages(self, request: web.Request) -> web.Response:
        """
        Processes incoming HTTP requests containing bot activities
         and generates appropriate responses.

        Args:
            request: The incoming HTTP request to process.

        Returns:
            An aiohttp web Response object, typically with
             a status code of HTTPStatus.OK.
        """
        # Main bot message handler.
        if "application/json" in request.headers["Content-Type"]:
            body = await request.json()
        else:
            return web.Response(
                status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE
            )
        activity = Activity().deserialize(body)
        auth_header = request.headers.get('Authorization', '')
        # TODO: routing to various Bots
        try:
            response = await self._adapter.process_activity(
                auth_header, activity, self.bots[0].on_turn
            )
            if response:
                return web.json_response(
                    data=response.body,
                    status=response.status
                )
            return web.Response(status=HTTPStatus.OK)
        except Exception as exc:
            print(exc)
