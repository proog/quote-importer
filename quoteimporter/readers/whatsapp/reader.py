"""Read WhatsApp logs"""
from datetime import timedelta, timezone

from quoteimporter.models import Attachment, Quote, QuoteType

from .handlers import (
    AttachmentMatchHandler,
    AttachmentOmittedMatchHandler,
    IconMatchHandler,
    JoinMatchHandler,
    KickMatchHandler,
    LeaveMatchHandler,
    MessageMatchHandler,
    NamedAttachmentOmittedMatchHandler,
    SubjectMatchHandler,
    SystemMatchHandler,
)


class WhatsAppLogReader:
    """Read a WhatsApp log file"""

    def __init__(
        self,
        channel,
        utc_offset,
        date_order,
        you,
        source="whatsapp",
        attachment_dir=None,
    ):
        self.handlers = [
            AttachmentMatchHandler(
                channel, utc_offset, date_order, you, source, attachment_dir
            ),
            NamedAttachmentOmittedMatchHandler(
                channel, utc_offset, date_order, you, source, attachment_dir
            ),
            AttachmentOmittedMatchHandler(
                channel, utc_offset, date_order, you, source, attachment_dir
            ),
            MessageMatchHandler(
                channel, utc_offset, date_order, you, source, attachment_dir
            ),
            SubjectMatchHandler(
                channel, utc_offset, date_order, you, source, attachment_dir
            ),
            IconMatchHandler(
                channel, utc_offset, date_order, you, source, attachment_dir
            ),
            JoinMatchHandler(
                channel, utc_offset, date_order, you, source, attachment_dir
            ),
            LeaveMatchHandler(
                channel, utc_offset, date_order, you, source, attachment_dir
            ),
            KickMatchHandler(
                channel, utc_offset, date_order, you, source, attachment_dir
            ),
            SystemMatchHandler(
                channel, utc_offset, date_order, you, source, attachment_dir
            ),
        ]

    def read(self, iterable, skip=0):
        """Transform lines from iterable into quotes"""
        sequence_id = 1
        current = None
        skipped = 0

        for line in iterable:
            # whatsapp tends to add U+200E (left-to-right mark) chars at strange locations, but we don't care about those
            line = line.rstrip("\r\n").replace("\u200e", "")

            if skipped < skip:
                skipped += 1
                continue

            handled = False
            for handler in self.handlers:
                if not handler.can_handle(line):
                    continue

                if current is not None:
                    yield current

                current = handler.handle(line, sequence_id)
                sequence_id += 1
                handled = True
                break

            if handled:
                continue

            if current is not None:
                current.message += "\n" + line  # append to unfinished quote
                current.raw += "\n" + line
                continue

            print("Unknown %s" % line)

        if current is not None:
            yield current
