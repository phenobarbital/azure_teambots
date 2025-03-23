from botbuilder.core.card_factory import CardFactory
from botbuilder.schema import Activity, ActivityTypes
from botbuilder.core import (
    TurnContext,
)


class CardBot:

    def create_adaptive_card(self) -> dict:
        card_data = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.3",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Hello!, you are sending a Recognition Badge to someone:"
                },
                {
                    "type": "Input.ChoiceSet",
                    "id": "rewardChoice",
                    "style": "compact",
                    "value": "1",
                    "choices": [
                        {
                            "title": "Valuable Reward",
                            "value": "1"
                        },
                        {
                            "title": "Assignable Reward",
                            "value": "2"
                        },
                        {
                            "title": "A very Special Reward",
                            "value": "3"
                        }
                    ]
                },
                {
                    "type": "Input.Text",
                    "id": "receiverEmail",
                    "placeholder": "Receiver's email"
                },
                {
                    "type": "Input.Text",
                    "id": "message",
                    "isMultiline": True,
                    "maxLength": 300,
                    "placeholder": "Your message"
                },
                {
                    "type": "ActionSet",
                    "actions": [
                        {
                            "type": "Action.Submit",
                            "title": "Send",
                            "data": {
                                "action": "submit"
                            }
                        }
                    ]
                }
            ]
        }
        return card_data

    async def on_message_activity(self, turn_context: TurnContext):
        if turn_context.activity.text.lower() == '/badge':
            card_data = self.create_adaptive_card()
            await turn_context.send_activity(
                Activity(  # Use the imported Activity class
                    type=ActivityTypes.message,
                    attachments=[CardFactory.adaptive_card(card_data)]
                )
            )

    async def on_turn(self, turn_context: TurnContext):
        if turn_context.activity.type == ActivityTypes.message:
            # Check if the message is a command to send a card
            if turn_context.activity.text and turn_context.activity.text.lower().strip() == '/badge':
                await self.on_message_activity(turn_context)
            # Check if the message is a response from an Adaptive Card
            elif turn_context.activity.value:
                print(turn_context.activity)
                await self.process_form_submission(
                    turn_context.activity.value,
                    turn_context
                )
            else:
                # Echo the message text back to the user.
                await turn_context.send_activity(
                    f"I heard you say {turn_context.activity.text}"
                )

    async def process_form_submission(self, data, turn_context):
        print('RECEIVE DATA > ', data)
        receiver_email = data['receiverEmail']
        message = data['message']
        reward_id = data['rewardChoice']

        result = {
            'receiver_email': receiver_email,
            'message': message,
            'reward_id': reward_id
        }
        print('DATA:', result)
        await turn_context.send_activity(
            "Thank you for your Submission!"
        )
