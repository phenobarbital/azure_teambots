from typing import Optional, Union
from collections.abc import Callable, Awaitable
from aiohttp import web
# from helpers.dialog_helper import DialogHelper
from navconfig.logging import logging
from botbuilder.core.teams import TeamsInfo
from botbuilder.core import (
    ActivityHandler,
    TurnContext,
    CardFactory,
    MessageFactory,
    ConversationState,
    UserState
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
from .models import UserProfile, ConversationData
from .interfaces.messages import MessageHandler

class BotException(Exception):
    """
    Base exception class for bot-related errors.
    """
    pass


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
        app: web.Application,
        conversation_state: ConversationState = None,
        user_state: UserState = None,
        dialog: Dialog = None,
        **kwargs
    ):
        self.__name__ = self.__class__.__name__
        self.app = app  # type: ignore
        self.kwargs = kwargs
        self._conversation_state = None
        self._user_state = None
        self.dialog_set = None
        self.welcome_message: str = 'Welcome to this Bot.'
        # Conversation State:
        if conversation_state:
            self.conversation_state = conversation_state
        # Create a UserProfile on self.user_state
        if user_state:
            self.user_state = user_state
        # Dialog:
        self.dialog = dialog
        #
        self.logger = logging.getLogger(
            name=f'AzureBot.{self.__name__}'
        )
        super().__init__()

    @property
    def user_state(self):
        return self._user_state

    @user_state.setter
    def user_state(self, value):
        self._user_state = value
        self.user_profile_accessor = self._user_state.create_property(
            "UserProfile"
        )

    @property
    def conversation_state(self):
        return self._conversation_state

    @conversation_state.setter
    def conversation_state(self, value):
        self._conversation_state = value
        self.conversation_data_accessor = self._conversation_state.create_property(
            "ConversationData"
        )
        self.set_dialog_state()

    def set_dialog_state(self):
        self.dialog_state = self._conversation_state.create_property(
            "DialogState"
        )

    def get_message(
        self,
        message,
        activity_type=None,
        attachments: list = None,
        **kwargs
    ) -> Activity:
        msg = Activity(
            type=activity_type or ActivityTypes.message,
            text=message,
            attachments=attachments,
            **kwargs
        )
        return msg

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
        print('CAE AQUI PROFILE > ', turn_context.activity.channel_id)
        if turn_context.activity.channel_id == 'msteams':
            try:
                user_profile = await TeamsInfo.get_member(
                    turn_context,
                    turn_context.activity.from_property.id
                )
                return user_profile
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
                if content_url:
                    attachment_list.append(
                        {
                            "name": name,
                            "content_url": content_url,
                            "content_type": content_type
                        }
                    )
        return attachment_list

    async def on_message_activity(self, turn_context: TurnContext):
        print('=== ON MESSAGE ACTIVITY === ')
        # Listen for the command to send a badge
        if turn_context.activity.text:
            if turn_context.activity.text.lower().strip() in self.commands:
                if callable(self.commands_callback):
                    await self.commands_callback(turn_context)
        elif turn_context.activity.value:
            if callable(self.activity_callback):
                await self.activity_callback(  # pylint: disable=not-callable,E1102
                    turn_context.activity.value,
                    turn_context
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
                        await turn_context.send_activity(
                            f"Hi there { member.name }. " + self.welcome_message
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
            if turn_context.activity.text:
                if turn_context.activity.text.lower().strip() in self.commands:
                    await self.commands_callback(turn_context, user_profile)
            # Save any state changes that might have occurred during the turn.
            await self._conversation_state.save_changes(
                turn_context
            )
            await self._user_state.save_changes(
                turn_context
            )
        elif turn_context.activity.channel_id == 'webchat':
            # Howto: Evaluate WebChat
            await super().on_turn(turn_context)
            # Save any state changes that might have occurred during the turn.
            await self._conversation_state.save_changes(
                turn_context
            )
            await self._user_state.save_changes(
                turn_context
            )
        else:
            # TODO: Evaluate different channels
            await super().on_turn(turn_context)
            # Save any state changes that might have occurred during the turn.
            await self._conversation_state.save_changes(
                turn_context
            )
            await self._user_state.save_changes(
                turn_context
            )

    async def send_adaptive_card(self, turn_context: TurnContext, **kwargs):
        message = Activity(
            type=ActivityTypes.message,
            attachments=[self.create_card({})]
        )
        await turn_context.send_activity(message)

    commands_callback = send_adaptive_card
