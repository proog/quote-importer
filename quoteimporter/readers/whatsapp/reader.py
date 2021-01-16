"""Read WhatsApp logs"""
from .handlers import *
from .models import WhatsAppOptions


class WhatsAppLogReader:
    """Read a WhatsApp log file"""

    def __init__(self, options: WhatsAppOptions):
        self.handlers = [
            AttachmentMatchHandler(options),
            NamedAttachmentOmittedMatchHandler(options),
            AttachmentOmittedMatchHandler(options),
            MessageMatchHandler(options),
            SubjectMatchHandler(options),
            IconMatchHandler(options),
            JoinMatchHandler(options),
            LeaveMatchHandler(options),
            KickMatchHandler(options),
            SystemMatchHandler(options),
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
