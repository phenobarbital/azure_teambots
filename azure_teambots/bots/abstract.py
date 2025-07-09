from typing import Optional, Union, Any
from collections.abc import Callable, Awaitable
import uuid
from http import HTTPStatus
from aiohttp import web
from navconfig.logging import logging
from navigator.applications.base import BaseApplication  # pylint: disable=E0611
from navigator.types import WebApp   # pylint: disable=E0611
from botbuilder.core.teams import TeamsInfo
from botbuilder.core import (
    ActivityHandler,
    TurnContext,
    CardFactory,
    MessageFactory,
    ConversationState,
    MemoryStorage,
    UserState,
)
from botbuilder.schema import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    Attachment
)
from botbuilder.schema.teams import TeamsChannelAccount
from botbuilder.dialogs import Dialog
from .helpers import DialogHelper
from ..models import UserProfile, ConversationData
from .interfaces.messages import MessageHandler
from ..config import BotConfig
from ..adapters import AdapterHandler


class AbstractBot(ActivityHandler, MessageHandler):
    """
    Base class for a bot that handles incoming messages from users.
    """
    commands: list = []
    activity_callback: Optional[Union[Awaitable, Callable]] = None
    commands_callback: Optional[Union[Awaitable, Callable]] = None
    default_message: str = 'Welcome to this Bot.'
    info_message: str = (
        "Hello and Welcome back.\n"
        "You're receiving this because you're using this Agent Bot and joined to this conversation."
    )

    def __init__(
        self,
        bot_name: str,
        app: web.Application,
        config: Optional[Union[BotConfig, dict]] = None,
        client_id: str = None,
        client_secret: str = None,
        welcome_message: Optional[str] = None,
        dialog: Any = None,
        route: str = None,
        **kwargs
    ):
        self._bot_name = bot_name
        self._botid: str = kwargs.pop('id', uuid.uuid4().hex)
        # class name
        self.__name__ = self.__class__.__name__
        self.app: web.Application = app
        self._adapter = None
        self.dialog = dialog
        self.dialog_set = None
        # Memory and User State Management
        self._memory = None
        self.welcome_message: str = welcome_message or self.default_message
        self.logger = logging.getLogger(
            name=f'AzureBot.{self.__name__}'
        )
        if not config:
            config = BotConfig(
                client_id=client_id,
                client_secret=client_secret
            )
        elif isinstance(config, dict):
            config = BotConfig(**config)
        elif not isinstance(config, BotConfig):
            raise ValueError(
                "Invalid configuration provided."
            )
        self._config = config
        self.app_id = self._config.APP_ID or client_id
        self.app_password = self._config.APP_PASSWORD or client_secret

        if not self.app_id or not self.app_password:
            self.logger.error("AzureBot: Missing Microsoft App ID and App Password.")
            raise ValueError(
                "AzureBot: Missing Microsoft App ID and App Password."
            )
        self.kwargs = kwargs
        self._route = route or f"/api/{self._botid}/messages"
        super().__init__()
        self.logger.info(
            f"AzureBot: Initializing {self.__name__} with ID {self._botid}."
        )

    @property
    def id(self):
        return self._botid

    def setup(self, app: web.Application = None):
        if not self.app:
            if isinstance(app, BaseApplication):
                self.app = app.get_app()
            elif isinstance(app, WebApp):
                self.app = app  # register the app into the Extension
        # Memory and User State Management
        self._memory = MemoryStorage()
        # Use property setters to initialize accessors
        self.user_state = UserState(self._memory)
        self.conversation_state = ConversationState(self._memory)
        # Config adapter
        self._adapter = AdapterHandler(
            config=self._config,
            logger=self.logger,
            conversation_state=self.conversation_state
        )
        # adding routes:
        self.app.router.add_post(self._route, self.messages)
        # add bot routes to exception routes
        try:
            _auth = self.app['auth']
            _auth.add_exclude_list(self._route)
        except Exception as e:
            self.logger.error(
                f"Auth Exclusion Error: {e}"
            )
        # Register Startup and Cleanup handlers
        self.app.on_startup.append(self.on_startup)
        self.app.on_cleanup.append(self.on_cleanup)

    async def on_startup(self, app):
        """
        Some Authentication backends need to call an Startup.
        """
        pass

    async def on_cleanup(self, app):
        """
        Cleanup the processes
        """
        pass

    @property
    def user_state(self):
        return self._user_state

    @user_state.setter
    def user_state(self, value):
        self._user_state = value
        self.user_profile_accessor = self._user_state.create_property("UserProfile")

    @property
    def conversation_state(self):
        return self._conversation_state

    @conversation_state.setter
    def conversation_state(self, value):
        self._conversation_state = value
        self.conversation_data_accessor = self._conversation_state.create_property("ConversationData")
        self.set_dialog_state()

    def set_dialog_state(self):
        self.dialog_state = self._conversation_state.create_property("DialogState")

    def get_message(
        self,
        message,
        activity_type=None,
        attachments: list = None,
        **kwargs
    ) -> Activity:
        return Activity(
            type=activity_type or ActivityTypes.message,
            text=message,
            attachments=attachments,
            **kwargs
        )

    async def on_typing_activity(self, turn_context: TurnContext):
        try:
            # Send Typing Indicator (immediately)
            typing_activity = Activity(type=ActivityTypes.typing)
            typing_activity.relates_to = turn_context.activity.conversation
            await turn_context.send_activity(
                typing_activity
            )
        except Exception as exc:
            self.logger.error(
                f"Error sending typing indicator: {exc}"
            )

    def get_generic_profile(self, activity):
        return {
            "id": activity.from_property.id,
            "name": activity.from_property.name
        }

    async def get_user_profile(self, turn_context: TurnContext) -> TeamsChannelAccount:
        # Check if the channel ID is 'msteams'
        if turn_context.activity.channel_id == 'msteams':
            try:
                return await TeamsInfo.get_member(
                    turn_context,
                    turn_context.activity.from_property.id
                )
            except Exception as exc:
                self.logger.warning(
                    f"Error on Teams user's profile: {exc}"
                )
        else:
            self.logger.notice(
                f"Channel Service: {turn_context.activity.channel_id}"
            )
            # TODO: Evaluate different channels
            try:
                return self.get_generic_profile(turn_context.activity)
            except Exception as exc:
                self.logger.error(
                    f"Error getting user's profile: {exc}"
                )
            return None

    def manage_attachments(self, turn_context: TurnContext):
        attachments = turn_context.activity.attachments
        print('ATTACHMENTS > ', attachments)
        attachment_list = []
        if attachments:
            for attachment in attachments:
                print('ATTACHMENT > ', attachment)
                content_url = attachment.content_url
                content_type = attachment.content_type
                name = attachment.name
                self.logger.info(
                    f"Received attachment: {name} ({content_type}) at {content_url}"
                )
                # Check if the attachment is a file
                if content_url and content_type:
                    # Check if the content type is a file type
                    self.logger.info(
                        f"Attachment URL: {content_url}"
                    )
                    attachment_list.append(
                        {
                            "name": name,
                            "content_url": content_url,
                            "content_type": content_type
                        }
                    )
        return attachment_list

    async def on_message_activity(self, turn_context: TurnContext):
        """Handles incoming message activities."""
        print('=== ON MESSAGE ACTIVITY === ')
        # Listen for the command to send a badge
        if turn_context.activity.text:
            if turn_context.activity.text.lower().strip() in self.commands:
                if callable(self.commands_callback):
                    try:
                        await self.commands_callback(turn_context)
                    except Exception as exc:
                        self.logger.error(
                            f"Callback Error: {self.commands_callback.__name__}: {exc}"
                        )
        elif turn_context.activity.value:
            if callable(self.activity_callback):
                try:
                    await self.activity_callback(  # pylint: disable=not-callable,E1102
                        turn_context.activity.value,
                        turn_context
                    )
                except Exception as exc:
                    self.logger.error(
                        f"Callback Error: {self.activity_callback.__name__}: {exc}"
                    )
        else:
            user_response = turn_context.activity.text
            message = self.get_message(
                message=f"I heard you say {user_response}",
            )
            # Echo the message text back to the user.
            await turn_context.send_activity(
                message
            )
        # await DialogHelper.run_dialog(
        #     self.dialog,
        #     turn_context,
        #     self.conversation_state.create_property("DialogState"),
        # )

    async def on_members_added_activity(
        self,
        members_added: list[ChannelAccount],
        turn_context: TurnContext
    ):
        # Welcome new users
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                try:
                    if turn_context.activity.channel_id == 'msteams':
                        await turn_context.send_activity(
                            Activity(
                                type=ActivityTypes.message,
                                text=self.welcome_message
                            )
                        )
                    else:
                        name = member.name or None
                        if not name:
                            user_profile = await self.get_user_profile(
                                turn_context
                            )
                            if user_profile:
                                name = user_profile.get('name', None)
                        if not name:
                            message = f"Hello!. {self.welcome_message}"
                        else:
                            message = f"Hello {name}. {self.welcome_message}"
                        await turn_context.send_activity(
                            message
                        )
                        await turn_context.send_activity(self.info_message)
                except Exception as e:
                    if 'access_token' in str(e):
                        self.logger.error(
                            (
                                "We have Trouble to send Messages, the Bot is not Authorized."
                                "Please check the Bot's Permissions and User grants "
                                "(User.Read, User.ReadBasic.all)"
                            )
                        )
                    self.logger.error(
                        f"Failed to send activity: {str(e)}"
                    )

    async def save_state_changes(self, turn_context: TurnContext):
        await self.conversation_state.save_changes(
            turn_context
        )
        await self.user_state.save_changes(
            turn_context
        )

    async def on_turn(self, turn_context: TurnContext):
        ## Get the user's profile on MS Teams:
        print('=== ON TURN === ')
        if turn_context.activity.channel_id == 'msteams':
            user_profile = await self.user_profile_accessor.get(turn_context, UserProfile)
            conversation_data = await self.conversation_data_accessor.get(
                turn_context, ConversationData
            )
            if user_profile.name is None:
                userinfo = await self.get_user_profile(turn_context)
                if userinfo is not None:
                    user_profile.name = userinfo.name
                    user_profile.email = userinfo.email
                    user_profile.profile = vars(userinfo)
            ## Add Conversation Data:
            conversation_data.timestamp = turn_context.activity.timestamp
            conversation_data.channel_id = turn_context.activity.channel_id
            conversation_data.conversation_id = turn_context.activity.conversation.id
            # Save any state changes that might have occurred during the turn.
            await self.user_profile_accessor.set(turn_context, user_profile)
            await self.conversation_data_accessor.set(turn_context, conversation_data)
            # after, fire up the on_message_activity:
            await super().on_turn(turn_context)
            if turn_context.activity.text and turn_context.activity.text.lower().strip() in self.commands:
                await self.commands_callback(turn_context, user_profile)
            # Save any state changes that might have occurred during the turn.
            await self.save_state_changes(turn_context)
        elif turn_context.activity.channel_id == 'webchat':
            # Howto: Evaluate WebChat
            await super().on_turn(turn_context)
            # Save any state changes that might have occurred during the turn.
            await self.save_state_changes(turn_context)
        else:
            # TODO: Evaluate different channels
            await super().on_turn(turn_context)
            # Save any state changes that might have occurred during the turn.
            await self.save_state_changes(turn_context)

    async def send_adaptive_card(self, turn_context: TurnContext, **kwargs):
        message = Activity(
            type=ActivityTypes.message,
            attachments=[self.create_card({})]
        )
        await turn_context.send_activity(message)

    commands_callback = send_adaptive_card

    # Bot message handler:
    # Listen for incoming requests on /api/{?}/messages
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
        if request.content_type.lower() == 'application/json':
            body = await request.json()
        else:
            return web.Response(status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

        activity = Activity().deserialize(body)
        auth_header = request.headers.get('Authorization', '')
        # TODO: routing to various Bots
        try:
            response = await self._adapter.process_activity(
                auth_header, activity, self.on_turn
            )
            if response:
                return web.json_response(
                    data=response.body,
                    status=response.status
                )
            return web.Response(status=HTTPStatus.OK)
        except Exception as exc:
            self.logger.error(
                f"Error processing activity: {exc}", exc_info=True
            )
            return web.Response(
                status=HTTPStatus.INTERNAL_SERVER_ERROR
            )
