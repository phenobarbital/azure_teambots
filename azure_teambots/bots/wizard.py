# Create a new file: azure_teambots/bots/wizard_bot.py
from botbuilder.core import TurnContext, CardFactory
from botbuilder.schema import ActivityTypes, Activity, Attachment
from .abstract import AbstractBot
from ..models import ConversationData

class WizardBot(AbstractBot):
    """A bot that guides users through a multi-step process using Adaptive Cards."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commands = ["wizard", "start_wizard", "reset"]
        self.default_message = "I can guide you through a step-by-step process. Type 'wizard' to begin."

    async def on_message_activity(self, turn_context: TurnContext):
        """Handle message activities and manage the wizard state."""
        # Get conversation data to track wizard state
        conversation_data = await self.conversation_data_accessor.get(
            turn_context, ConversationData
        )

        # Initialize wizard_step if it doesn't exist
        if not hasattr(conversation_data, 'wizard_step'):
            conversation_data.wizard_step = 0
            conversation_data.wizard_data = {}

        # Handle incoming message
        message_text = turn_context.activity.text.lower().strip() if turn_context.activity.text else ""

        # Check for commands
        if message_text in ["wizard", "start_wizard"]:
            # Start or restart the wizard
            conversation_data.wizard_step = 1
            conversation_data.wizard_data = {}
            await self._send_wizard_step(turn_context, conversation_data)

        elif message_text == "reset":
            # Reset the wizard
            conversation_data.wizard_step = 0
            conversation_data.wizard_data = {}
            await turn_context.send_activity("Wizard has been reset. Type 'wizard' to start again.")

        elif turn_context.activity.value:
            # Handle card submission
            await self._process_card_submission(turn_context, conversation_data)

        elif conversation_data.wizard_step > 0:
            # If in a wizard but received text instead of card submission
            await turn_context.send_activity(
                "Please use the card to continue. Type 'reset' if you need to start over."
            )

        else:
            # Default message for non-wizard interactions
            await turn_context.send_activity(
                "Type 'wizard' to start the guided process."
            )

        # Save state
        await self.conversation_data_accessor.set(turn_context, conversation_data)
        await self.save_state_changes(turn_context)

    async def _process_card_submission(self, turn_context: TurnContext, conversation_data: ConversationData):
        """Process adaptive card submissions and move to the next wizard step."""
        submission = turn_context.activity.value
        current_step = conversation_data.wizard_step

        # Store submitted data
        conversation_data.wizard_data.update(submission)

        # Move to next step
        conversation_data.wizard_step += 1

        # If wizard is complete
        if conversation_data.wizard_step > 3:  # Assuming 3-step wizard
            await self._complete_wizard(turn_context, conversation_data)
        else:
            # Send next step
            await self._send_wizard_step(turn_context, conversation_data)

    async def _send_wizard_step(self, turn_context: TurnContext, conversation_data: ConversationData):
        """Send the appropriate adaptive card for the current wizard step."""
        step = conversation_data.wizard_step

        if step == 1:
            card = self._create_step1_card()
        elif step == 2:
            card = self._create_step2_card(conversation_data.wizard_data)
        elif step == 3:
            card = self._create_step3_card(conversation_data.wizard_data)
        else:
            # Should not happen, but just in case
            card = None

        if card:
            message = Activity(
                type=ActivityTypes.message,
                attachments=[CardFactory.adaptive_card(card)]
            )
            await turn_context.send_activity(message)

    async def _complete_wizard(self, turn_context: TurnContext, conversation_data: ConversationData):
        """Complete the wizard and display a summary."""
        wizard_data = conversation_data.wizard_data

        # Create summary text
        summary = (
            f"Wizard Complete! Here's a summary of your information:\n\n"
            f"Name: {wizard_data.get('name', 'Not provided')}\n"
            f"Department: {wizard_data.get('department', 'Not provided')}\n"
            f"Request Type: {wizard_data.get('requestType', 'Not provided')}\n"
            f"Priority: {wizard_data.get('priority', 'Not provided')}\n"
            f"Description: {wizard_data.get('description', 'Not provided')}"
        )

        # Send summary
        await turn_context.send_activity(summary)

        # Create completion card
        completion_card = {
            "type": "AdaptiveCard",
            "version": "1.0",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Request Submitted Successfully",
                    "weight": "bolder",
                    "size": "large"
                },
                {
                    "type": "TextBlock",
                    "text": "Thank you for completing the wizard.",
                    "wrap": True
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Start Another Request",
                    "data": {
                        "action": "restart_wizard"
                    }
                }
            ]
        }

        message = Activity(
            type=ActivityTypes.message,
            attachments=[CardFactory.adaptive_card(completion_card)]
        )
        await turn_context.send_activity(message)

        # Reset wizard state
        conversation_data.wizard_step = 0

    def _create_step1_card(self):
        """Create the first step card for collecting basic information."""
        return {
            "type": "AdaptiveCard",
            "version": "1.0",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Step 1: Basic Information",
                    "weight": "bolder",
                    "size": "medium"
                },
                {
                    "type": "TextBlock",
                    "text": "Please provide your name and department",
                    "wrap": True
                },
                {
                    "type": "Input.Text",
                    "id": "name",
                    "placeholder": "Your name",
                    "label": "Name"
                },
                {
                    "type": "Input.ChoiceSet",
                    "id": "department",
                    "label": "Department",
                    "choices": [
                        {"title": "IT", "value": "IT"},
                        {"title": "HR", "value": "HR"},
                        {"title": "Finance", "value": "Finance"},
                        {"title": "Marketing", "value": "Marketing"},
                        {"title": "Operations", "value": "Operations"}
                    ],
                    "style": "compact"
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Next",
                    "data": {
                        "step": 1
                    }
                }
            ]
        }

    def _create_step2_card(self, previous_data):
        """Create the second step card for collecting request details."""
        return {
            "type": "AdaptiveCard",
            "version": "1.0",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Step 2: Request Details",
                    "weight": "bolder",
                    "size": "medium"
                },
                {
                    "type": "TextBlock",
                    "text": f"Hi {previous_data.get('name', '')}, please specify your request type",
                    "wrap": True
                },
                {
                    "type": "Input.ChoiceSet",
                    "id": "requestType",
                    "label": "Request Type",
                    "choices": [
                        {"title": "Access Request", "value": "Access"},
                        {"title": "Hardware Issue", "value": "Hardware"},
                        {"title": "Software Issue", "value": "Software"},
                        {"title": "Other", "value": "Other"}
                    ],
                    "style": "expanded"
                },
                {
                    "type": "Input.ChoiceSet",
                    "id": "priority",
                    "label": "Priority",
                    "choices": [
                        {"title": "Low", "value": "Low"},
                        {"title": "Medium", "value": "Medium"},
                        {"title": "High", "value": "High"},
                        {"title": "Critical", "value": "Critical"}
                    ],
                    "style": "compact"
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Next",
                    "data": {
                        "step": 2
                    }
                }
            ]
        }

    def _create_step3_card(self, previous_data):
        """Create the third step card for collecting additional details."""
        return {
            "type": "AdaptiveCard",
            "version": "1.0",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Step 3: Additional Information",
                    "weight": "bolder",
                    "size": "medium"
                },
                {
                    "type": "TextBlock",
                    "text": f"Request Type: {previous_data.get('requestType', '')} (Priority: {previous_data.get('priority', '')})",
                    "wrap": True
                },
                {
                    "type": "Input.Text",
                    "id": "description",
                    "placeholder": "Please describe your request in detail",
                    "label": "Description",
                    "isMultiline": True
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit",
                    "data": {
                        "step": 3
                    }
                }
            ]
        }
