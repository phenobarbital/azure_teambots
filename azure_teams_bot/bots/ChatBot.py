# from botbuilder.core.card_factory import CardFactory
from typing import Any
from navigator.applications.base import BaseApplication
from botbuilder.dialogs import (
    DialogSet,
)
from botbuilder.schema import Activity, ActivityTypes
from botbuilder.core import (
    TurnContext,
)
from ..models import ChatResponse
from .abstract import AbstractBot
from ..models import UserProfile, ConversationData


class ChatBot(AbstractBot):
    """
    bot that handles incoming messages from users related to HR.
    """
    commands: list = ['/chat']
    default_message: str = """
    Welcome! this is a HR QA Bot, You can use this bot to obtain any answer to
    many questions related with HQ."""

    def __init__(
        self,
        app: BaseApplication,
        bot_name: str,
        bot: Any = None,
        conversation_state: Any = None,
        user_state: Any = None,
        dialog=None,
        **kwargs
    ):
        self._bot_name = bot_name
        self._bot = bot
        super().__init__(app, conversation_state, user_state, dialog)
        self.welcome_message: str = kwargs.get(
            'welcome_message',
            self.default_message
        )

    def set_dialog_state(self):
        self.dialog_set = DialogSet(
            self._conversation_state.create_property("dialog_state")
        )

    async def on_message_activity(self, turn_context: TurnContext):
        try:
            # Handle Attachments
            attachments = self.manage_attachments(turn_context)
            print('ATTACHMENTS > ', attachments)
            dialog_context = await self.dialog_set.create_context(turn_context)
            ## Get the user's profile
            user_profile = await self.user_profile_accessor.get(turn_context, UserProfile)
            conversation_data = await self.conversation_data_accessor.get(
                turn_context, ConversationData
            )
            # Send typing indicator
            await self.on_typing_activity(turn_context)
            try:
                manager = self.app['chatbot_manager']
            except KeyError:
                # Send the response back to the user
                await turn_context.send_activity(
                    Activity(
                        type=ActivityTypes.message,
                        text="Error: Chatbot Manager is not installed on this Channel."
                    )
                )
            # get user message:
            user_message = turn_context.activity.text
            # chatbot:
            # TODO: receive the Chatbot Name from context.
            if self._bot is None:
                chatbot = manager.get_chatbot(self._bot_name)
            else:
                chatbot = self._bot
            chatbot_response = None
            try:
                memory = chatbot.create_memory(key='chat_history')
                with chatbot.get_retrieval() as retrieval:
                    conversation = retrieval.conversation(
                        question=user_message,
                        search_kwargs={"k": 10},
                        memory=memory
                    )
                    response = conversation.invoke(user_message)
                    chatbot_response = response.response
                # async with chatbot.get_retrieval() as retrieval:
                #     qa = retrieval.qa(
                #         question=user_message,
                #         search_kwargs={"k": 20}
                #     )
                #     chatbot_response, _ = qa.question(user_message)
            except Exception as exc:
                error = f"**Error getting Chatbot:** {exc}"
                await turn_context.send_activity(
                    Activity(
                        type=ActivityTypes.message,
                        text=error
                    )
                )
            # Send the response back to the user
            await turn_context.send_activity(
                Activity(
                    type=ActivityTypes.message,
                    text=chatbot_response
                )
            )
        except Exception as exc:
            print(exc)
        await self._conversation_state.save_changes(turn_context)
        await self._user_state.save_changes(turn_context)
