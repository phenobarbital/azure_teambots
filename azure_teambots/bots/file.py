# Create a new file: azure_teambots/bots/file_bot.py
import os
import base64
import aiohttp
import tempfile
from botbuilder.core import TurnContext, CardFactory
from botbuilder.schema import (
    ActivityTypes,
    Activity,
    Attachment,
    AttachmentData,
    ContentTypes,
    HeroCard,
    CardImage
)
from .abstract import AbstractBot

class FileBot(AbstractBot):
    """A bot that can handle file uploads and send files."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commands = ["upload", "sendimage", "help"]
        self.default_message = "I can help with file uploads and downloads. Type 'help' for more information."
        # Create a temp directory for file storage if needed
        self.temp_dir = tempfile.mkdtemp()

    async def on_message_activity(self, turn_context: TurnContext):
        """Handle messages and file-related commands."""
        # Check for attachments first
        if turn_context.activity.attachments:
            await self._handle_attachments(turn_context)
            return

        # Handle text commands
        if turn_context.activity.text:
            text = turn_context.activity.text.lower().strip()

            if text == "help":
                await self._send_help(turn_context)
            elif text == "upload":
                await self._prompt_for_upload(turn_context)
            elif text.startswith("sendimage"):
                # Extract image name if provided
                parts = text.split(maxsplit=1)
                image_name = parts[1] if len(parts) > 1 else "sample.png"
                await self._send_image(turn_context, image_name)
            else:
                await turn_context.send_activity(
                    "I don't understand that command. Type 'help' to see what I can do."
                )

        # Save state
        await self.save_state_changes(turn_context)

    async def _handle_attachments(self, turn_context: TurnContext):
        """Process uploaded attachments."""
        attachments = self.manage_attachments(turn_context)

        if not attachments:
            await turn_context.send_activity("No valid attachments found.")
            return

        # Process each attachment
        for attachment in attachments:
            name = attachment.get("name", "unknown_file")
            content_type = attachment.get("content_type", "application/octet-stream")
            content_url = attachment.get("content_url", "")

            if content_url:
                # Log the attachment
                self.logger.info(f"Received attachment: {name} ({content_type})")

                # Acknowledge receipt
                await turn_context.send_activity(
                    f"Received file: {name} ({content_type})"
                )

                # Optionally download the file
                if self._should_download_file(content_type):
                    try:
                        file_path = await self._download_file(content_url, name)
                        await turn_context.send_activity(
                            f"File saved successfully to: {file_path}"
                        )
                    except Exception as e:
                        self.logger.error(f"Error downloading file: {str(e)}")
                        await turn_context.send_activity(
                            "There was an error processing your file."
                        )

    def _should_download_file(self, content_type: str) -> bool:
        """Determine if we should download this file type."""
        # Set allowed file types for download
        allowed_types = [
            "image/jpeg",
            "image/png",
            "image/gif",
            "application/pdf",
            "text/plain",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]

        return content_type.lower() in allowed_types

    async def _download_file(self, content_url: str, filename: str) -> str:
        """Download a file from a URL and return the file path."""
        # Create a safe filename
        safe_filename = os.path.basename(filename)
        file_path = os.path.join(self.temp_dir, safe_filename)

        # Download the file
        async with aiohttp.ClientSession() as session:
            async with session.get(content_url) as response:
                if response.status == 200:
                    with open(file_path, 'wb') as f:
                        while True:
                            chunk = await response.content.read(1024)
                            if not chunk:
                                break
                            f.write(chunk)
                else:
                    raise Exception(f"Failed to download file: HTTP {response.status}")

        return file_path

    async def _send_help(self, turn_context: TurnContext):
        """Send help information about file capabilities."""
        help_text = (
            "Here's how I can help with files:\n\n"
            "- Upload a file: Just attach it to a message and send it to me\n"
            "- Request an upload: Type 'upload' to get a prompt\n"
            "- Get a sample image: Type 'sendimage'\n"
            "- Get a specific image: Type 'sendimage filename.png'"
        )
        await turn_context.send_activity(help_text)

    async def _prompt_for_upload(self, turn_context: TurnContext):
        """Send a message prompting the user to upload a file."""
        await turn_context.send_activity(
            "Please upload a file by clicking the attachment button in your chat window."
        )

    async def _send_image(self, turn_context: TurnContext, image_name: str = "sample.png"):
        """Send an image to the user."""
        # For demo purposes, we'll generate a simple image
        # In a real bot, you might retrieve from storage or generate dynamically

        if image_name == "sample.png":
            # This is a simple 1x1 pixel PNG as a base64 string
            # In a real bot, you would use actual images
            image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

            # Create an attachment from the image data
            image_attachment = self._create_attachment_from_base64(
                image_data,
                "image/png",
                "sample.png"
            )

            # Create a hero card with the image
            card = HeroCard(
                title="Sample Image",
                text="Here's the image you requested",
                images=[CardImage(url=image_attachment.content_url)]
            )

            # Create and send the response
            message = Activity(
                type=ActivityTypes.message,
                attachments=[CardFactory.hero_card(card)]
            )
            await turn_context.send_activity(message)

            # Also send the raw image as an attachment
            image_msg = Activity(
                type=ActivityTypes.message,
                text="Here's the raw image file:",
                attachments=[image_attachment]
            )
            await turn_context.send_activity(image_msg)
        else:
            # If specific image requested but not available
            await turn_context.send_activity(
                f"Sorry, I don't have the image '{image_name}'. Try 'sendimage' for a sample image."
            )

    def _create_attachment_from_base64(self, base64_data: str, content_type: str, name: str) -> Attachment:
        """Create an attachment from base64-encoded data."""
        return Attachment(
            name=name,
            content_type=content_type,
            content_url=f"data:{content_type};base64,{base64_data}"
        )
