import json
import os.path
from datetime import datetime

from quoteimporter.models import Attachment, Quote, QuoteType

from .models import TelegramOptions


class BaseHandler:
    def __init__(self, options: TelegramOptions):
        self.channel = options.channel
        self.source = options.source
        self.export_dir = options.export_dir

    def can_handle(self, message: dict) -> bool:
        raise NotImplementedError

    def handle(
        self, message: dict, sequence_id: int, all_messages: list[dict]
    ) -> Quote:
        raise NotImplementedError

    def parse_date(self, message: dict):
        return datetime.strptime(message["date"], "%Y-%m-%dT%H:%M:%S")

    def join_text(self, message: dict) -> str:
        """Telegram will batch several text types together in a list. This method joins them back together."""
        text = message["text"]

        if isinstance(text, list):
            text = "".join(
                [part if isinstance(part, str) else part["text"] for part in text]
            )

        return text

    def read_attachment(self, relative_path: str):
        """Read media attachments from files in the chat export directory"""
        filename = os.path.basename(relative_path)

        if self.export_dir:
            complete_path = os.path.join(self.export_dir, relative_path)

            if os.path.isfile(complete_path):
                with open(complete_path, "rb") as f:
                    return Attachment(filename, f.read())

        return Attachment(filename, None)


class TextMessageHandler(BaseHandler):
    def can_handle(self, message: dict) -> bool:
        return (
            message["type"] == "message"
            and "text" in message
            and "media_type" not in message
            and "poll" not in message
        )

    def handle(self, message: dict, sequence_id: int, all_messages: list[dict]):
        return Quote(
            self.channel,
            sequence_id,
            message["from"],
            self.join_text(message),
            self.parse_date(message),
            QuoteType.message,
            self.source,
            json.dumps(message),
        )


class AttachmentMessageHandler(BaseHandler):
    def can_handle(self, message: dict) -> bool:
        return message["type"] == "message" and message.get("media_type") in [
            "sticker",
            "animation",
            "video_file",
            "audio_file",
            "voice_message",
        ]

    def handle(self, message: dict, sequence_id: int, all_messages: list[dict]):
        media_type = message["media_type"]
        text = self.join_text(message)
        attachment = None

        if media_type == "sticker":
            text = message.get("sticker_emoji", text)
            attachment = self.read_attachment(message["file"])
        elif media_type in ["animation", "video_file", "audio_file", "voice_message"]:
            attachment = self.read_attachment(message["file"])

        return Quote(
            self.channel,
            sequence_id,
            message["from"],
            text,
            self.parse_date(message),
            QuoteType.attachment,
            self.source,
            json.dumps(message),
            attachment,
        )


class PollMessageHandler(BaseHandler):
    def can_handle(self, message: dict) -> bool:
        return message["type"] == "message" and "poll" in message

    def handle(self, message: dict, sequence_id: int, all_messages: list[dict]):
        return Quote(
            self.channel,
            sequence_id,
            message["from"],
            json.dumps(message["poll"]),
            self.parse_date(message),
            QuoteType.message,
            self.source,
            json.dumps(message),
        )


class GroupPhotoHandler(BaseHandler):
    def can_handle(self, message: dict) -> bool:
        return message["type"] == "service" and message["action"] == "edit_group_photo"

    def handle(self, message: dict, sequence_id: int, all_messages: list[dict]):
        attachment = self.read_attachment(message["photo"])

        return Quote(
            self.channel,
            sequence_id,
            message["actor"],
            message["action"],
            self.parse_date(message),
            QuoteType.subject,
            self.source,
            json.dumps(message),
            attachment,
        )


class InviteHandler(BaseHandler):
    def can_handle(self, message: dict) -> bool:
        return message["type"] == "service" and message["action"] == "invite_members"

    def handle(self, message: dict, sequence_id: int, all_messages: list[dict]):
        return Quote(
            self.channel,
            sequence_id,
            message["actor"],
            f'Invited {", ".join(m for m in message["members"])}',
            self.parse_date(message),
            QuoteType.system,
            self.source,
            json.dumps(message),
        )


class JoinHandler(BaseHandler):
    def can_handle(self, message: dict) -> bool:
        return (
            message["type"] == "service" and message["action"] == "join_group_by_link"
        )

    def handle(self, message: dict, sequence_id: int, all_messages: list[dict]):
        return Quote(
            self.channel,
            sequence_id,
            message["actor"],
            message["action"],
            self.parse_date(message),
            QuoteType.join,
            self.source,
            json.dumps(message),
        )


class PinMessageHandler(BaseHandler):
    def can_handle(self, message: dict) -> bool:
        return message["type"] == "service" and message["action"] == "pin_message"

    def handle(self, message: dict, sequence_id: int, all_messages: list[dict]):
        pinned_id = message["message_id"]
        pinned_message = next((m for m in all_messages if m["id"] == pinned_id), None)
        pinned_text = (
            f"{pinned_message['from']}: {pinned_message['text']}"
            if pinned_message
            else ""
        )

        return Quote(
            self.channel,
            sequence_id,
            message["actor"],
            pinned_text,
            self.parse_date(message),
            QuoteType.subject,
            self.source,
            json.dumps(message),
        )


class GroupTitleHandler(BaseHandler):
    def can_handle(self, message: dict) -> bool:
        return message["type"] == "service" and message["action"] in [
            "migrate_from_group",
            "edit_group_title",
        ]

    def handle(self, message: dict, sequence_id: int, all_messages: list[dict]):
        return Quote(
            self.channel,
            sequence_id,
            message["actor"],
            message["title"],
            self.parse_date(message),
            QuoteType.subject,
            self.source,
            json.dumps(message),
        )
