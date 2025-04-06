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
from .bots import EchoBot


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
    # Define available bot types
    BOT_TYPES = {
        "echo": EchoBot,
        # Add other bot types as they're implemented
        # "channel": ChannelBot,
        # "private": PrivateChatBot,
        # "wizard": WizardBot,
        # "file": FileBot,
    }

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
        self.bots: dict = {}
        self.logger = logging.getLogger('AzureBot.Manager')
        self.logger.notice(
            f"AzureBot: Starting Azure Bot Service with {len(bots)} Bots."
        )
        # Other arguments:
        self._kwargs = kwargs
        self._bots = bots or []
        # Calling Setup:
        self.setup(app)

    def create_bot(self, cfg: Union[BotConfig, dict]):
        """
        Creates a New Bot instance and adds it to the AzureBot service.

        Args:
            config: Configuration object containing bot settings.

        Returns:
            An instance of the specified bot type.
        """
        if isinstance(cfg, dict):
            bot_name = cfg.pop('bot_name')
            botcls = cfg.pop('cls', 'BaseBot')
        else:
            self.logger.error(
                "AzureBot: Invalid Bot Configuration."
            )
            raise ValueError(
                f"Invalid bot configuration:{cfg!r}"
            )
        bot = cfg.pop('id', bot_name.upper())
        client_id = cfg.pop('client_id', config.get(f'{bot}_CLIENT_ID'))
        client_secret = cfg.pop('client_secret', config.get(f'{bot}_CLIENT_SECRET'))
        if client_id is None or client_secret is None:
            raise ValueError(
                f"Missing Client ID or Secret for bot: {bot}"
            )

        # Check if the bot class is available
        bot_class = self.BOT_TYPES.get(botcls)
        if not bot_class:
            clspath = "azure_teambots.bots"
            try:
                bot_module = importlib.import_module(
                    clspath
                )
                bot_class = getattr(bot_module, botcls)
            except (ImportError, AttributeError) as ex:
                self.logger.error(
                    f"AzureBot: Failed to load bot {botcls} from {clspath}. Error: {ex!s}"
                )
                raise ex from None
        if not bot_class:
            self.logger.error(
                f"AzureBot: Bot class {botcls} not found in {self.BOT_TYPES}."
            )
            raise ValueError(
                f"Invalid bot class: {botcls}."
            )
        # Create a new instance of the bot class
        return bot_class(
            bot_name=bot_name,
            id=bot,
            client_id=client_id,
            client_secret=client_secret,
            route=f'/api/{bot.lower()}/messages',
            app=self.app,
            **cfg
        )

    def add_bot(self) -> AbstractBot:
        """
        Adds a new bot instance to the AzureBot service.

        Returns:
            An instance of the specified bot type.
        """
        pass

    def load_bot(self, bot_name: str) -> AbstractBot:
        """
        Loads the bot logic based on the specified bot type.

        Returns:
            An instance of the specified bot type.
        """
        try:
            clspath = f"azure_teambots.bots.{bot_name}"
            bot = bot_name.upper()
            client_id = config.get(f'{bot}_CLIENT_ID')
            client_secret = config.get(f'{bot}_CLIENT_SECRET')
            if client_id is None or client_secret is None:
                raise ValueError(
                    f"Missing Client ID or Secret for bot: {bot}"
                )
            bot_module = importlib.import_module(
                clspath
            )
            bot_class = getattr(bot_module, bot_name)
            return bot_class(
                bot_name=bot_name,
                id=bot_name.lower(),
                client_id=client_id,
                client_secret=client_secret,
                route=f'/api/{bot_name.lower()}/messages',
                app=self.app,
            )
        except ValueError:
            raise
        except (ImportError, AttributeError) as exc:
            self.logger.error(
                f"Failed to load bot: {exc}, Defaulting to BaseBot."
            )
            # Create a new instance of BaseBot with the provided credentials
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
            if isinstance(bot, AbstractBot):
                bt = bot
            elif isinstance(bot, str):
                # Create a new Bot instance based on class name:
                bt = self.load_bot(bot)
            elif isinstance(bot, dict):
                bt = self.create_bot(bot)
            else:
                self.logger.warning(
                    "AzureBot: Invalid Bot Type."
                )
                continue
            try:
                bt.setup(self.app)
                self.bots[bt.id] = bt
            except Exception as err:
                self.logger.error(
                    f"AzureBot: Failed to setup bot {bt.id}: {err}"
                )
                raise RuntimeError(
                    f"AzureBot: Failed to setup bot {bt.id}: {err}"
                ) from err
        # startup operations over extension backend
        self.app.on_startup.append(self.on_startup)
        # cleanup operations over Auth backend
        self.app.on_cleanup.append(self.on_cleanup)
        ## Configure Routes
        router = self.app.router
        # More Generic Approach
        router.add_route(
            "GET", r"/api/v1/azurebots/{bot}", self._botmessage, name='azurebot_message'
        )
        router.add_route(
            "POST", r"/api/v1/azurebots/{bot}", self._botmessage, name="azurebot_message_post"
        )

    async def on_startup(self, app):
        """
        Some Authentication backends need to call an Startup.
        """
        for name, bot in self.bots.items():
            try:
                await bot.on_startup(app)
            except Exception as err:
                self.logger.exception(
                    f"Error on Startup Bot Backend {name!s} init: {err}"
                )
                raise RuntimeError(
                    f"Error on Startup Auth Backend {name!s} init: {err}"
                ) from err

    async def on_cleanup(self, app):
        """
        Cleanup the processes
        """
        for name, bot in self.bots.items():
            try:
                await bot.on_cleanup(app)
            except Exception as err:
                self.logger.exception(
                    f"Error on Cleanup Auth Backend {name} init: {err}"
                )

    async def _botmessage(self, request: web.Request):
        """
        Handles incoming bot messages and routes them to the appropriate bot logic.

        Args:
            request: The incoming HTTP request containing the bot activity.

        Returns:
            A web.Response indicating the result of the processing.
        """
        # Extract bot name from the URL path
        bot_name = request.match_info.get('bot')
        if bot_name is None:
            return web.Response(
                status=400, text="Bot name not provided."
            )
        # Check if the bot exists in the registered bots
        if bot_name not in self.bots:
            return web.Response(
                status=404, text=f"Bot with name {bot_name} not found."
            )
        # Get the bot instance and process the request
        bot = self.bots[bot_name]
        return await bot.messages(request)
