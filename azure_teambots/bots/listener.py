from botbuilder.core import TurnContext
from botbuilder.schema import ActivityTypes, ChannelAccount
# from msgraph_core import GraphClient
# from azure.identity.aio import ClientSecretCredential
from botbuilder.schema.teams import TeamsChannelAccount, TeamInfo
from botbuilder.core.teams import TeamsInfo
from .abstract import AbstractBot
from azure_teambots.conf import (
    MS_TENANT_ID,
    BOTDEV_CLIENT_ID,
    BOTDEV_CLIENT_SECRET,
)


class TeamsChannelBot(AbstractBot):
    async def on_message_activity(self, turn_context: TurnContext):
        print(':: Channel Bot :: ')
        # Check if the message is from a Teams channel
        if turn_context.activity.channel_id == 'msteams' and turn_context.activity.conversation.conversation_type == "channel":
            # Get the sender's Teams user profile
            # Initialize variables
            user_id = turn_context.activity.from_property.id
            user_name = turn_context.activity.from_property.name or "Unknown"

            # Get the team and channel IDs
            team_id = turn_context.activity.channel_data["team"]["id"]
            channel_id = turn_context.activity.channel_data["channel"]["id"]

            print("Team ID: ", team_id)
            print("Channel ID: ", channel_id)

            # # Authenticate with Microsoft Graph
            # credential = ClientSecretCredential(
            #     tenant_id=MS_TENANT_ID,
            #     client_id=BOTDEV_CLIENT_ID,
            #     client_secret=BOTDEV_CLIENT_SECRET,
            # )

            # graph_client = GraphClient(credential=credential)

            # Get messages from the channel
            # response = await graph_client.get(
            #     f'/teams/{team_id}/channels/{channel_id}/messages'
            # )

            # messages = await response.json()

            # # Process messages
            # for message in messages.get('value', []):
            #     self.logger.info(
            #         f"Message from {message['from']['user']['displayName']}: {message['body']['content']}"
            #     )

            # print(':: Channel Bot Messages :: ')
            # print(messages)

            # Gets the details for the given team id.
            team_details = await TeamsInfo.get_team_details(turn_context)
            team_name = team_details.name
            try:
                sender: TeamsChannelAccount = await TeamsInfo.get_member(
                    turn_context, turn_context.activity.from_property.id
                )
                user_id = sender.id
                display_name = sender.name
                username = sender.user_principal_name
                user_role = sender.user_role
            except Exception as e:
                self.logger.error(
                    f"Error getting user profile: {e}"
                )
                # Use available information from the activity
                sender = turn_context.activity.from_property

            # Extract message details
            channel_id = turn_context.activity.conversation.id
            message_text = turn_context.activity.text
            timestamp = turn_context.activity.timestamp

            print('HERE > ', channel_id, message_text)

            # # Log or process the message
            # self.logger.notice(
            #     f"Team: {team_name}, Channel ID: {channel_id}"
            # )

            # # Log or process the message
            # self.logger.info(
            #     f"Team: {team_info.name if team_info else 'Unknown'}, Channel ID: {channel_id}"
            # )
            # self.logger.info(
            #     f"Message from {user_name} ({user_id}) at {timestamp}: {message_text}"
            # )

            # Send a response
            await turn_context.send_activity("Message received and processed.")
        else:
            # Handle other message types or direct messages
            await super().on_message_activity(turn_context)
