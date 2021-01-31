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

    def handle(self, message: dict, sequence_id: int) -> Quote:
        raise NotImplementedError

    def parse_date(self, message: dict):
        return datetime.strptime(message["date"], "%Y-%m-%dT%H:%M:%S")

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

    def handle(self, message: dict, sequence_id: int):
        return Quote(
            self.channel,
            sequence_id,
            message["from"],
            message["text"],
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
        ]

    def handle(self, message: dict, sequence_id: int):
        media_type = message["media_type"]
        text = message["text"]
        attachment = None

        if media_type == "sticker":
            text = message.get("sticker_emoji", text)
            attachment = self.read_attachment(message["file"])
        elif media_type in ["animation", "video_file"]:
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


class SystemHandler(BaseHandler):
    def can_handle(self, message: dict) -> bool:
        return message["type"] == "service" and message["action"] in [
            "edit_group_photo"
        ]

    def handle(self, message: dict, sequence_id: int):
        action = message.get("action", None)

        if action == "edit_group_photo":
            attachment = self.read_attachment(message["photo"])
        else:
            attachment = None

        return Quote(
            self.channel,
            sequence_id,
            message["actor"],
            message["action"],
            self.parse_date(message),
            QuoteType.system,
            self.source,
            json.dumps(message),
            attachment,
        )
