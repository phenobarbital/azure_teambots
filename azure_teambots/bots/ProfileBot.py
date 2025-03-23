from botbuilder.core.card_factory import CardFactory
from botbuilder.schema import Activity, ActivityTypes
from botbuilder.core import (
    TurnContext,
)
from .abstract import AbstractBot
from .helpers import DialogHelper


class ProfileBot(AbstractBot):
    commands: list = ['/profile']
    welcome_message: str = """
    Welcome! You can use this bot to view your profile.
    Try typing '/profile' to start."""

    async def on_message_activity(self, turn_context: TurnContext):
        await DialogHelper.run_dialog(
            self.dialog,
            turn_context,
            self.conversation_state.create_property("DialogState"),
        )
