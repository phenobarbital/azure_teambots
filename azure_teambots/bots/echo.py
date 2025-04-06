from botbuilder.core import TurnContext
from botbuilder.schema import Activity, ActivityTypes
from botbuilder.schema.teams import TeamsChannelAccount
from botbuilder.core.teams import TeamsInfo
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


class EchoChannelBot(AbstractBot):
    """
    A bot that responds to mentions in a channel with echo responses.
    """

    def __init__(self, bot_name, app, **kwargs):
        super().__init__(bot_name, app, **kwargs)
        self.mention_text = kwargs.get('mention_text', 'echo')
        self.logger.info(f"Initialized EchoChannelBot with mention trigger: {self.mention_text}")

    async def on_message_activity(self, turn_context: TurnContext):
        """
        Handles message activities by responding to mentions in a channel.
        """
        # Get the activity from the turn context
        activity = turn_context.activity

        # Check if this is from a channel (not a direct message)
        if hasattr(activity.conversation, 'conversation_type') and activity.conversation.conversation_type == 'channel':
            self.logger.debug(f"Received channel message: {activity.text}")

            # Check if the bot was mentioned
            if await self.was_bot_mentioned(turn_context):
                # Extract the actual message content (remove the mention part)
                message_without_mentions = self.remove_mentions_from_text(turn_context)

                # Check if the trigger word is in the message
                if self.mention_text.lower() in message_without_mentions.lower():
                    # Reply with an echo
                    await turn_context.send_activity(f"Echo: {message_without_mentions}")
                    self.logger.debug(
                        "Sent echo response to channel message"
                    )
        else:
            # For direct messages, use the regular EchoBot behavior
            user_message = activity.text
            self.logger.debug(f"Received direct message: {user_message}")
            await turn_context.send_activity(f"You said: {user_message}")

        # Handle attachments
        if activity.attachments:
            attachments = self.manage_attachments(turn_context)
            await turn_context.send_activity(
                f"You sent {len(attachments)} attachment(s)."
            )

        # Save state changes
        await self.save_state_changes(turn_context)

    async def was_bot_mentioned(self, turn_context: TurnContext) -> bool:
        """
        Determines if the bot was mentioned in the incoming activity.

        Returns:
            bool: True if the bot was mentioned, False otherwise.
        """
        # If the channel is Teams, we can use the TeamsInfo to check for mentions
        if turn_context.activity.channel_id == "msteams":
            # Get the bot's ID
            bot_id = turn_context.activity.recipient.id

            # Check mentions in the entities
            if turn_context.activity.entities:
                for entity in turn_context.activity.entities:
                    if entity.type == "mention" and entity.mentioned.id == bot_id:
                        return True

        # For other channels or as a fallback, check if the bot's name is in the message
        return self._bot_name.lower() in turn_context.activity.text.lower()

    def remove_mentions_from_text(self, turn_context: TurnContext) -> str:
        """
        Removes mention entities from the message text.

        Returns:
            str: Message text with mentions removed.
        """
        text = turn_context.activity.text

        # If there are no entities, return the original text
        if not turn_context.activity.entities:
            return text

        # Process each mention entity
        for entity in turn_context.activity.entities:
            if entity.type == "mention":
                # Get the mention text and remove it from the message
                mention_text = text[entity.start_index:entity.end_index]
                text = text.replace(mention_text, "").strip()

        return text
