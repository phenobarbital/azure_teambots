from typing import Any, Union
from collections.abc import Awaitable, Callable
from botbuilder.dialogs.prompts import (
    TextPrompt,
    ChoicePrompt,
    PromptOptions
)
from botbuilder.dialogs import (
    ComponentDialog,
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
    DialogTurnStatus
)
from botbuilder.core import (
    MessageFactory,
    CardFactory
)
from botbuilder.dialogs.choices import Choice


class BadgeDialog(ComponentDialog):
    def __init__(
        self,
        bot: Any = None,
        submission_callback: Union[Awaitable, Callable] = None,
        dialog_id: str = "BadgeDialog"
    ):
        super(BadgeDialog, self).__init__(dialog_id)
        self.add_dialog(TextPrompt("TextPrompt"))
        self.add_dialog(ChoicePrompt("ChoicePrompt"))
        self.bot = bot
        self.submission_callback = submission_callback
        self.add_dialog(
            WaterfallDialog("WaterfallDialog", [
                self.ask_for_name_step,
                self.ask_for_badge_step,
                self.confirmation_step,
            ])
        )
        self.initial_dialog_id = "WaterfallDialog"

    async def ask_for_name_step(self, step_context: WaterfallStepContext):
        # Define the Adaptive Card content
        card_content = {
            "type": "AdaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "size": "Medium",
                    "weight": "Bolder",
                    "text": "Hello! Please enter the name or email of the awarded person:"
                },
                {
                    "type": "Input.Text",
                    "id": "recipientName",
                    "placeholder": "Enter name or email"
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit"
                }
            ],
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.3"
        }
        # Create and send the Adaptive Card
        card = CardFactory.adaptive_card(card_content)
        await step_context.context.send_activity(
            MessageFactory.attachment(card)
        )
        # Indicate to the WaterfallDialog to wait for the next turn
        return DialogTurnResult(
            DialogTurnStatus.Waiting
        )

    def get_badge_form(self, person):
        card_data = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.3",
            "body": [
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
        name = person["name"]
        email = person["email"]
        # Adding the badges (calculated from the database)
        card_data['body'].insert(
            0,
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
            }
        )
        # adding the message:
        card_data["body"].insert(
            0,
            {
                "type": "TextBlock",
                "text": f"You are sending a Badge to {name} ({email})."
            }
        )
        return card_data

    async def ask_for_badge_step(self, step_context: WaterfallStepContext):
        recipient_info = step_context.context.turn_state.get("BadgeBot.info")
        # look for person in database:
        print('RECIPIENT > ', recipient_info)
        # assuming person was found (sample person):
        step_context.context.turn_state["BadgeBot.receiver"] = recipient_info
        person = {
            "name": "Jesus Lara",
            "username": "jlara",
            "email": "jlara@trocglobal.com"
        }
        if person:
            # Create and send the Adaptive Card
            card_data = self.get_badge_form(person)
            card = self.bot.create_card(card_data)
            message = MessageFactory.attachment(card)
            await step_context.context.send_activity(message)
            # return await step_context.next(person)
            return DialogTurnResult(DialogTurnStatus.Waiting)
        else:
            # Send a message if no person was found
            await step_context.context.send_activity(
                "Nobody was found with that information."
            )
            return await step_context.replace_dialog(
                self.id,
                options={
                    "prompt": "Let's try again.\n \
                        Please enter the name or email of the awarded person:"
                }
            )

    async def confirmation_step(
        self,
        step_context: WaterfallStepContext,
        **kwargs
    ):
        print('AQUI ===', kwargs)
        data = step_context.context.turn_state.get("BadgeBot.info")
        print('OBJ > ', step_context)
        print('HERE >>> ')
        print(data)
        await self.submission_callback(
            data,
            step_context.context
        )
        return await step_context.end_dialog()
