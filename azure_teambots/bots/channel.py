# Create a new file: azure_teambots/bots/channel_bot.py
from botbuilder.core import TurnContext
from botbuilder.schema import ActivityTypes
from botbuilder.schema.teams import TeamInfo, TeamsChannelAccount
from botbuilder.core.teams import TeamsInfo
from .abstract import AbstractBot


class ChannelBot(AbstractBot):
    """A bot that listens for @ mentions in channels and responds to commands."""

    def __init__(self, *args, **kwargs):
        """Initialize the ChannelBot.

        Set up the bot's command list.
        """
        super().__init__(*args, **kwargs)
        # Define commands that the bot responds to
        self.commands = ["help", "info", "status"]

    async def on_message_activity(self, turn_context: TurnContext):
        """Handle messages, focusing on those with @ mentions."""
        # Check if this is a channel message with a mention
        if turn_context.activity.channel_data and "team" in turn_context.activity.channel_data:
            # Get the text without the mention
            text = self._remove_mention_text(turn_context.activity.text)

            # Log the cleaned message
            self.logger.info(f"Received channel message: {text}")

            # Check if the text starts with a command
            command = text.strip().lower().split()[0] if text and text.strip() else ""

            if command in self.commands:
                await self._handle_command(command, turn_context)
            else:
                # If not a recognized command but still mentioned
                await turn_context.send_activity(
                    f"I don't recognize that command. Try one of: {', '.join(self.commands)}"
                )
        else:
            # For direct messages, use the standard behavior
            await super().on_message_activity(turn_context)

    def _remove_mention_text(self, text: str) -> str:
        """Remove the @mention part from the message."""
        if not text:
            return ""

        # In Teams, mentions are in the format <at>BotName</at>
        # We'll use a simple string replacement approach
        parts = text.split(">")
        if len(parts) > 1:
            # Return everything after the first mention
            return "".join(parts[1:]).strip()
        return text.strip()

    async def _handle_command(self, command: str, turn_context: TurnContext):
        """Handle known commands."""
        if command == "help":
            await turn_context.send_activity(
                f"Available commands: {', '.join(self.commands)}"
            )
        elif command == "info":
            # Get team and channel information
            team_details = await TeamsInfo.get_team_details(turn_context)
            channel_info = turn_context.activity.channel_data.get("channel", {})

            response = (
                f"Team: {team_details.name}\n"
                f"Channel: {channel_info.get('name', 'Unknown')}\n"
                f"Bot: {self._bot_name}"
            )
            await turn_context.send_activity(response)
        elif command == "status":
            await turn_context.send_activity("I'm up and running!")

        # Save state after handling command
        await self.save_state_changes(turn_context)
