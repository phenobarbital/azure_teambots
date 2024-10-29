from botbuilder.core import TurnContext
from botbuilder.schema import ActivityTypes, ChannelAccount
from botbuilder.schema.teams import TeamsChannelAccount, TeamInfo
from botbuilder.core.teams import TeamsInfo
from .abstract import AbstractBot


class TeamsChannelBot(AbstractBot):
    async def on_message_activity(self, turn_context: TurnContext):
        print(':: Channel Bot :: ')
        # Check if the message is from a Teams channel
        if turn_context.activity.channel_id == 'msteams' and \
           turn_context.activity.conversation.conversation_type == "channel":

            # Get the sender's Teams user profile
            try:
                sender: TeamsChannelAccount = await TeamsInfo.get_member(
                    turn_context, turn_context.activity.from_property.id
                )
            except Exception as e:
                self.logger.error(f"Error getting user profile: {e}")
                return

            # Get the team and channel info
            team_info: TeamInfo = turn_context.activity.teams_get_team_info()
            channel_id = turn_context.activity.conversation.id

            # Extract message details
            user_id = sender.id
            user_name = sender.name
            message_text = turn_context.activity.text
            timestamp = turn_context.activity.timestamp

            # Log or process the message
            self.logger.info(
                f"Team: {team_info.name}, Channel ID: {channel_id}"
            )
            self.logger.info(
                f"Message from {user_name} ({user_id}) at {timestamp}: {message_text}"
            )

            # Optionally, perform additional actions
            # For example, save the message to a database or trigger a workflow

            # You can also send a response if needed
            await turn_context.send_activity("Message received and processed.")
        else:
            # Handle other message types or direct messages
            await super().on_message_activity(turn_context)
