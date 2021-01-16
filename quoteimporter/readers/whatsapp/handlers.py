import os.path
import re
from datetime import datetime, timedelta, timezone

from quoteimporter.models import Attachment, Quote, QuoteType

from .models import DateOrder, WhatsAppOptions

"""
Matches all combinations of:
- 1 and 2 digit day of month
- 1 and 2 digit month
- 1, 2 and 4 digit year
- time with and without seconds
- time units separated by colon or dot
- time and author separated by colon-space, space-dash-space, or time enclosed in brackets
Remember to check the length of the year and time when parsing!
"""
TIMESTAMP_PATTERN = (
    r"\[?(\d{1,2}\/\d{1,2}\/\d{1,4}), (\d{2}.\d{2}(?:.\d{2})?)(?::| -|\])"
)


class MatchHandler:
    pattern: re.Pattern = None

    def __init__(self, options: WhatsAppOptions):
        self.channel = options.channel
        self.tzinfo = timezone(timedelta(hours=options.utc_offset))
        self.date_order = options.date_order
        self.you = options.you
        self.source = options.source
        self.attachment_dir = options.attachment_dir

    def can_handle(self, line: str) -> bool:
        return self.pattern.match(line) is not None

    def handle(self, line: str, sequence_id: int) -> Quote:
        raise NotImplementedError

    def start_quote(
        self,
        date_str,
        time_str,
        author,
        message,
        sequence_id,
        quote_type,
        raw,
        attachment=None,
    ):
        """Make a quote from a line. Its message may not be finished on this line"""
        timestamp = self.parse_timestamp(date_str, time_str)

        if author == "You" or author == "you":
            author = self.you

        return Quote(
            self.channel,
            sequence_id,
            author,
            message,
            timestamp,
            quote_type,
            self.source,
            raw,
            attachment,
        )

    def parse_timestamp(self, date_part, time_part):
        """Parse timestamp from a date part and a time part of varying formatting"""
        split_date = date_part.split("/")
        split_time = time_part.replace(".", ":").split(":")

        if len(split_date[2]) == 1:
            split_date[2] = "200%s" % split_date[2]
        elif len(split_date[2]) == 2:
            split_date[2] = "20%s" % split_date[2]

        day = int(split_date[1 if self.date_order == DateOrder.american else 0])
        month = int(split_date[0 if self.date_order == DateOrder.american else 1])
        year = int(split_date[2])
        hours = int(split_time[0])
        minutes = int(split_time[1] if len(split_time) > 1 else 0)
        seconds = int(split_time[2] if len(split_time) > 2 else 0)

        local_dt = datetime(
            year, month, day, hours, minutes, seconds, tzinfo=self.tzinfo
        )
        return local_dt.astimezone(timezone.utc)

    def read_attachment(self, filename):
        """Read media attachments from files in the attachment directory"""
        if self.attachment_dir is not None:
            path = os.path.join(self.attachment_dir, filename)

            if os.path.isfile(path):
                with open(path, "rb") as f:
                    return Attachment(filename, f.read())

        return Attachment(filename, None)


class MessageMatchHandler(MatchHandler):
    pattern = re.compile(fr"^{TIMESTAMP_PATTERN} (.+?): (.*)$")

    def handle(self, line: str, sequence_id: int):
        match = self.pattern.match(line)
        return self.start_quote(
            match[1],
            match[2],
            match[3],
            match[4],
            sequence_id,
            QuoteType.message,
            line,
        )


class AttachmentMatchHandler(MatchHandler):
    pattern = re.compile(fr"^{TIMESTAMP_PATTERN} (.+?): (<attached: (.+)>)$")

    def handle(self, line: str, sequence_id: int):
        match = self.pattern.match(line)
        attachment = self.read_attachment(match[5])
        return self.start_quote(
            match[1],
            match[2],
            match[3],
            match[4],
            sequence_id,
            QuoteType.attachment,
            line,
            attachment,
        )


class AttachmentOmittedMatchHandler(MatchHandler):
    """At some point, likely in 2020, exporting chats "without media" causes media messages to be exported as e.g. "video omitted"."""

    pattern = re.compile(
        fr"^{TIMESTAMP_PATTERN} (.+?): ((GIF|image|audio|video|sticker|Contact card|document) omitted)$"
    )

    def handle(self, line: str, sequence_id: int):
        match = self.pattern.match(line)
        return self.start_quote(
            match[1],
            match[2],
            match[3],
            match[4],
            sequence_id,
            QuoteType.attachment,
            line,
        )


class NamedAttachmentOmittedMatchHandler(MatchHandler):
    """
    For some omitted attachments, the filename and number of pages will be displayed as well.
    In this case, we will attempt to read the attachment even though the log claims it was omitted.
    """

    pattern = re.compile(
        fr"^{TIMESTAMP_PATTERN} (.+?): ((.+?)( • \d+ pages)? document omitted)$"
    )

    def handle(self, line: str, sequence_id: int):
        match = self.pattern.match(line)
        attachment = self.read_attachment(match[5])
        return self.start_quote(
            match[1],
            match[2],
            match[3],
            match[4],
            sequence_id,
            QuoteType.attachment,
            line,
            attachment,
        )


class SubjectMatchHandler(MatchHandler):
    pattern = re.compile(
        fr'^{TIMESTAMP_PATTERN} (.+) changed the subject from .* to (?:"|“)(.*)(?:"|”)$'
    )

    def handle(self, line: str, sequence_id: int):
        match = self.pattern.match(line)
        return self.start_quote(
            match[1],
            match[2],
            match[3],
            match[4],
            sequence_id,
            QuoteType.subject,
            line,
        )


class IconMatchHandler(MatchHandler):
    pattern = re.compile(fr"^{TIMESTAMP_PATTERN} (.+) (changed this group\'s icon)$")

    def handle(self, line: str, sequence_id: int):
        match = self.pattern.match(line)
        return self.start_quote(
            match[1],
            match[2],
            match[3],
            match[4],
            sequence_id,
            QuoteType.subject,
            line,
        )


class JoinMatchHandler(MatchHandler):
    pattern = re.compile(fr"^{TIMESTAMP_PATTERN} .+ added (.+)$")

    def handle(self, line: str, sequence_id: int):
        match = self.pattern.match(line)
        return self.start_quote(
            match[1], match[2], match[3], "", sequence_id, QuoteType.join, line
        )


class LeaveMatchHandler(MatchHandler):
    pattern = re.compile(fr"^{TIMESTAMP_PATTERN} (.+) left$")

    def handle(self, line: str, sequence_id: int):
        match = self.pattern.match(line)
        return self.start_quote(
            match[1], match[2], match[3], "", sequence_id, QuoteType.leave, line
        )


class KickMatchHandler(MatchHandler):
    pattern = re.compile(fr"^{TIMESTAMP_PATTERN} (.+) removed (.+)$")

    def handle(self, line: str, sequence_id: int):
        match = self.pattern.match(line)
        return self.start_quote(
            match[1],
            match[2],
            match[3],
            match[4],
            sequence_id,
            QuoteType.kick,
            line,
        )


class SystemMatchHandler(MatchHandler):
    pattern = re.compile(fr"^{TIMESTAMP_PATTERN} (.+)$")

    def handle(self, line: str, sequence_id: int):
        match = self.pattern.match(line)
        return self.start_quote(
            match[1],
            match[2],
            "",
            match[3],
            sequence_id,
            QuoteType.system,
            line,
        )
