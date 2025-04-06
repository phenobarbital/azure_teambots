import re
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

        # Configure additional properties
        self.debug_mode = kwargs.get('debug_mode', False)
        self.strip_quotes = kwargs.get('strip_quotes', True)

        self.logger.info(
            f"Initialized EchoChannelBot with mention trigger: {self.mention_text}"
        )
        if self.debug_mode:
            self.logger.info(
                "Debug mode enabled - will log additional information"
            )

    def debug_log_activity(self, activity):
        """Helper method to log detailed activity information when in debug mode"""
        if not self.debug_mode:
            return

        self.logger.debug("--- Activity Debug Information ---")
        self.logger.debug(f"Text: {activity.text}")
        self.logger.debug(f"Type: {activity.type}")
        self.logger.debug(f"ID: {activity.id}")
        self.logger.debug(f"Channel ID: {activity.channel_id}")

        # Log conversation details
        if hasattr(activity, 'conversation') and activity.conversation:
            self.logger.debug(f"Conversation ID: {activity.conversation.id}")
            if hasattr(activity.conversation, 'conversation_type'):
                self.logger.debug(f"Conversation Type: {activity.conversation.conversation_type}")

        # Log entities if available
        if hasattr(activity, 'entities') and activity.entities:
            self.logger.debug(f"Entities count: {len(activity.entities)}")
            for i, entity in enumerate(activity.entities):
                self.logger.debug(f"Entity {i} type: {entity.type}")
                self.logger.debug(f"Entity {i} properties: {vars(entity)}")
        else:
            self.logger.debug("No entities found in activity")

        # Log recipient info
        if hasattr(activity, 'recipient') and activity.recipient:
            self.logger.debug(f"Recipient ID: {activity.recipient.id}")
            self.logger.debug(f"Recipient Name: {activity.recipient.name}")

        self.logger.debug("--- End Activity Debug Info ---")

    def process_teams_mention(self, text):
        """
        Process a message that might contain Teams mentions in the format <at>Name</at>.

        Args:
            text (str): The message text to process

        Returns:
            str: The cleaned message text with mentions and trigger word removed
        """
        # First, check for mentions in Teams format
        if "<at>" in text and "</at>" in text:
            # Extract all mentions
            mentions = re.findall(r'<at>.*?</at>', text)

            # Remove all mentions
            cleaned_text = text
            for mention in mentions:
                cleaned_text = cleaned_text.replace(mention, "").strip()
        else:
            cleaned_text = text

        # Now remove the trigger word if present
        if self.mention_text.lower() in cleaned_text.lower():
            parts = cleaned_text.lower().split(self.mention_text.lower(), 1)
            cleaned_text = parts[1].strip() if len(parts) > 1 else ""

        # Strip quotes if enabled
        if self.strip_quotes and cleaned_text and (
            (cleaned_text.startswith('"') and cleaned_text.endswith('"')) or
            (cleaned_text.startswith("'") and cleaned_text.endswith("'"))
        ):
            cleaned_text = cleaned_text[1:-1]

        return cleaned_text

    async def on_message_activity(self, turn_context: TurnContext):
        """
        Handles message activities by responding to mentions in a channel.
        """
        # Get the activity from the turn context
        activity = turn_context.activity

        # Log detailed debug information if in debug mode
        self.debug_log_activity(activity)

        # Check if this is from a channel on Teams
        is_teams_message = activity.channel_id == "msteams"
        is_channel_message = (
            is_teams_message and hasattr(activity.conversation, 'conversation_type')
            and activity.conversation.conversation_type == 'channel'
        )

        print(f"Is Teams Message: {is_teams_message}, Is Channel Message: {is_channel_message}")
        self.logger.notice(
            f"Is Teams Message: {is_teams_message}, Is Channel Message: {is_channel_message}"
        )

        if is_teams_message and is_channel_message:
            # First check if we have a mention tag in the text
            if "<at>" in activity.text:
                # Get our bot name
                bot_name = self._bot_name
                mention_pattern = f"<at>{bot_name}</at>"

                # Check if our bot was the one mentioned
                if mention_pattern in activity.text:
                    self.logger.debug(
                        f"Bot '{bot_name}' was explicitly mentioned in the message"
                    )

                    # Process the message to extract content after mention and trigger word
                    message_text = activity.text
                    processed_message = self.process_teams_mention(message_text)

                    # Check if the trigger word is in the original message
                    if self.mention_text.lower() in message_text.lower():
                        # Reply with an echo of the processed message
                        self.logger.debug(f"Processed message: '{processed_message}'")
                        await turn_context.send_activity(f"Echo: {processed_message}")

                        # Save state and return
                        await self.save_state_changes(turn_context)
                        return

            # Fallback: try with the entity-based approach
            if await self.was_bot_mentioned(turn_context):
                self.logger.debug("Bot was mentioned via entity detection")

                # Extract the actual message content
                message_without_mentions = self.remove_mentions_from_text(turn_context)

                # Check if the trigger word is in the message
                if self.mention_text.lower() in message_without_mentions.lower():
                    # Process to get content after trigger word
                    processed_message = self.process_teams_mention(message_without_mentions)

                    # Reply with an echo
                    await turn_context.send_activity(f"Echo: {processed_message}")
                    self.logger.debug("Sent echo response via entity detection")

                    # Save state and return
                    await self.save_state_changes(turn_context)
                    return

        # Handle direct messages to the bot (could be in Teams or other channels)
        elif is_teams_message and not is_channel_message:
            # For direct messages in Teams, check if the message contains our trigger word
            if self.mention_text.lower() in activity.text.lower():
                # Process the message to extract content after the trigger word
                parts = activity.text.lower().split(self.mention_text.lower(), 1)
                if len(parts) > 1:
                    message_content = parts[1].strip()

                    # Strip quotes if needed
                    if self.strip_quotes and message_content and (
                        (message_content.startswith('"') and message_content.endswith('"')) or
                        (message_content.startswith("'") and message_content.endswith("'"))
                    ):
                        message_content = message_content[1:-1]

                    # Send echo response
                    await turn_context.send_activity(f"Echo: {message_content}")
                    await self.save_state_changes(turn_context)
                    return

            # If no trigger word, just echo back the message as is
            user_message = activity.text
            self.logger.debug(f"Processing as direct Teams message: '{user_message}'")
            await turn_context.send_activity(f"You said: {user_message}")
        else:
            # Regular message in other channels - just echo back
            user_message = activity.text
            self.logger.debug(f"Processing as regular message: '{user_message}'")
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

            # For Teams, the mention is usually in the text with <at>BotName</at>
            # We'll first check if our bot name is in the message with at-tags
            if f"<at>{self._bot_name}</at>" in turn_context.activity.text:
                return True

            # Check for bot ID in mentions (safer way to check)
            if hasattr(turn_context.activity, 'entities') and turn_context.activity.entities:
                for entity in turn_context.activity.entities:
                    # Debug information about entity structure
                    self.logger.debug(f"Entity type: {entity.type}, Entity properties: {vars(entity)}")

                    # Check if this is a mention entity (different implementations might have different structures)
                    if entity.type == "mention":
                        # Check if mentioned ID matches bot ID
                        if hasattr(entity, 'mentioned') and hasattr(entity.mentioned, 'id') and entity.mentioned.id == bot_id:  # noqa: E501
                            return True
                        # If entity has direct ID property
                        elif hasattr(entity, 'id') and entity.id == bot_id:
                            return True
                        # If entity has text that contains the bot name (fallback)
                        elif hasattr(entity, 'text') and self._bot_name.lower() in entity.text.lower():
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

        # In Teams, mentions appear as <at>BotName</at> in the text
        # First try to remove this format
        if turn_context.activity.channel_id == "msteams":
            # Try to find the bot name in an at-mention tag
            at_mention = f"<at>{self._bot_name}</at>"
            if at_mention in text:
                text = text.replace(at_mention, "").strip()

        # If there are entities, try to process them too
        if hasattr(turn_context.activity, 'entities') and turn_context.activity.entities:
            # Process each mention entity if it has start/end indices
            for entity in turn_context.activity.entities:
                if entity.type == "mention":
                    try:
                        # Try to remove by indices if available
                        if hasattr(entity, 'start_index') and hasattr(entity, 'end_index'):
                            mention_text = text[entity.start_index:entity.end_index]
                            text = text.replace(mention_text, "").strip()
                        # Fallback: if entity has text property, try to remove it directly
                        elif hasattr(entity, 'text'):
                            text = text.replace(entity.text, "").strip()
                    except Exception as e:
                        self.logger.warning(f"Error removing mention: {str(e)}")

        return text
