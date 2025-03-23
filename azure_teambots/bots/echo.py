from botbuilder.core import TurnContext
from .abstract import AbstractBot

class EchoBot(AbstractBot):
    """A simple Echo Bot that echoes back user messages."""

    async def on_message_activity(self, turn_context: TurnContext):
        """Handles message activities by echoing back the user's message."""
        # Get the user's message
        user_message = turn_context.activity.text

        # Log the received message
        self.logger.debug(f"Received message: {user_message}")

        # Echo back the message
        await turn_context.send_activity(f"You said: {user_message}")

        # Optionally, you can manage attachments if you expect any
        if turn_context.activity.attachments:
            attachments = self.manage_attachments(turn_context)
            await turn_context.send_activity(
                f"You sent {len(attachments)} attachment(s)."
            )

        # Save any state changes
        await self.save_state_changes(turn_context)
