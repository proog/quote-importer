import json
from typing import Iterator

from quoteimporter.models import Quote

from .handlers import (
    AttachmentMessageHandler,
    BaseHandler,
    GroupPhotoHandler,
    GroupTitleHandler,
    InviteHandler,
    JoinHandler,
    PinMessageHandler,
    PollMessageHandler,
    TextMessageHandler,
)
from .models import TelegramOptions


class TelegramLogReader:
    """Read a Telegram JSON formatted export"""

    def __init__(self, options: TelegramOptions):
        self.handlers: list[BaseHandler] = [
            TextMessageHandler(options),
            AttachmentMessageHandler(options),
            PollMessageHandler(options),
            GroupPhotoHandler(options),
            JoinHandler(options),
            PinMessageHandler(options),
            InviteHandler(options),
            GroupTitleHandler(options),
        ]

    def read(self, json_stream, skip=0) -> Iterator[Quote]:
        doc = json.load(json_stream)
        messages = doc["messages"]
        sequence_id = 1
        skipped = 0

        for message in messages:
            if skipped < skip:
                skipped += 1
                continue

            handled = False
            for handler in self.handlers:
                if not handler.can_handle(message):
                    continue

                yield handler.handle(message, sequence_id, messages)
                handled = True
                break

            if handled:
                sequence_id += 1
            else:
                print("Unknown %s" % json.dumps(message))
