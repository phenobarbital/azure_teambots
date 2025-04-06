# Create a new file: azure_teambots/bots/private_chat_bot.py
from botbuilder.core import TurnContext
from botbuilder.schema import ActivityTypes
from .abstract import AbstractBot

class PrivateChatBot(AbstractBot):
    """A bot designed for private chat interactions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commands = ["start", "help", "profile"]
        self.default_message = "I'm your personal assistant. Type 'help' to see what I can do."

    async def on_message_activity(self, turn_context: TurnContext):
        """Handle direct message activities."""
        user_message = turn_context.activity.text.strip().lower() if turn_context.activity.text else ""

        if user_message in self.commands:
            await self._handle_command(user_message, turn_context)
        else:
            # For any other message, provide a helpful response
            await turn_context.send_activity(
                "I'm not sure what you're asking. Type 'help' to see available commands."
            )

        # Save state after handling message
        await self.save_state_changes(turn_context)

    async def _handle_command(self, command: str, turn_context: TurnContext):
        """Handle commands in private chat."""
        if command == "help":
            help_text = (
                "Here's what I can do:\n"
                "- 'start': Begin a conversation\n"
                "- 'profile': Show your profile information\n"
                "- 'help': Show this help message"
            )
            await turn_context.send_activity(help_text)

        elif command == "start":
            # Get user profile info for personalized greeting
            user_profile = await self.user_profile_accessor.get(turn_context, UserProfile)
            name = user_profile.name or "there"

            await turn_context.send_activity(f"Hello, {name}! How can I assist you today?")

        elif command == "profile":
            user_profile = await self.user_profile_accessor.get(turn_context, UserProfile)

            if user_profile.name:
                profile_text = (
                    f"Name: {user_profile.name}\n"
                    f"Email: {user_profile.email or 'Not available'}"
                )
                await turn_context.send_activity(profile_text)
            else:
                await turn_context.send_activity("I don't have your profile information yet.")
