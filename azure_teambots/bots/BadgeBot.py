from botbuilder.dialogs import (
    DialogSet,
    DialogTurnStatus
)
from botbuilder.core import TurnContext, MessageFactory
from botbuilder.schema import (
    Activity,
    Attachment,
    ActivityTypes
)
from .abstract import AbstractBot
from .dialogs.badge import BadgeDialog


class BadgeBot(AbstractBot):
    """
    bot that handles incoming messages from users related to badges.
    """
    commands: list = ['/badge', '/reward']
    welcome_message: str = "Welcome! You can use this bot to send " \
        "badges. Try typing '/badge' to start."

    def __init__(
        self,
        app,
        conversation_state,
        user_state,
        dialog=None,
        **kwargs
    ):
        super().__init__(app, conversation_state, user_state, dialog)
        self.dialog_set = DialogSet(
            self.conversation_state.create_property("dialog_state")
        )
        self.badge_dialog = BadgeDialog(
            bot=self,
            submission_callback=self.process_submission
        )
        self.dialog_set.add(self.badge_dialog)

    async def on_invoke_activity(self, turn_context: TurnContext):
        print('TRIGGER THIS >> ', turn_context.activity.name)
        if turn_context.activity.name == "adaptiveCard/action":
            # Handle the Adaptive Card submit action here.
            # Extract the submitted data
            data = turn_context.activity.value
            print('HERE > ', data)

            # Now, you can process the submission data. For instance,
            # if you have a method
            # to specifically handle this, like `process_submission`,
            # you can call it here.
            await self.process_submission(data, turn_context)

            # You must return a response to the invoke activity.
            # Here's how you could create a simple response.
            return self._create_invoke_response()

        # Make sure to call the base method if you didn't handle
        # the invoke activity.
        return await super().on_invoke_activity(turn_context)

    def _create_invoke_response(self, body=None):
        return Activity(value=body, type="invokeResponse")

    async def on_message_activity(self, turn_context: TurnContext):
        dialog_context = await self.dialog_set.create_context(turn_context)
        ## Get the user's profile
        user_profile = await self.get_user_profile(turn_context)

        if turn_context.activity.value:
            # Assuming the response is from an Adaptive Card submit action
            turn_context.turn_state["BadgeBot.user_profile"] = user_profile
            turn_context.turn_state["BadgeBot.info"] = turn_context.activity.value
            await dialog_context.continue_dialog()

        elif turn_context.activity.text.lower().strip() in self.commands:
            await dialog_context.begin_dialog("BadgeDialog")
        else:
            results = await dialog_context.continue_dialog()
            print('RESULTS > ', results)
            if results.status == DialogTurnStatus.Empty:
                # Handle conversation updates or other message activities
                pass

        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)

    async def process_submission(self, data, turn_context: TurnContext):
        print('RECEIVE DATA > ', data)
        # receiver_email = data['receiverEmail']
        # message = data['message']
        # reward_id = data['rewardChoice']
        # result = {
        #     'receiver_email': receiver_email,
        #     'message': message,
        #     'reward_id': reward_id
        # }
        # print('DATA:', result)
        # print('APP >> ', self._app)
        print('DO IT THINGS WITH DATA')
        thanks = self.create_approval_adaptive_card()
        await turn_context.send_activity(
            thanks
        )

    def create_approval_adaptive_card(self):
        # Create and return the adaptive card content for approval
        return MessageFactory.text(
            "Badge was Sent."
        )

    def create_denial_adaptive_card(self):
        # Create and return the adaptive card content for denial
        return MessageFactory.text(
            "Badge was not Sent."
        )
