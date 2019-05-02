"""Read HexChat logs"""
import re
from datetime import datetime, timezone, timedelta
from quoteimporter.models import Quote, QuoteType


class HexChatLogReader:
    """Read a HexChat log file"""

    """Regular message"""
    message_re = re.compile(r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) <(.+)>\t(.*)$")

    topic_re = re.compile(
        r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) \*\t(.+) has changed the topic to: (.*)$"
    )
    log_open_re = re.compile(
        r"^\*\*\*\* BEGIN LOGGING AT .{3} (\w{3} \d{2} \d{2}:\d{2}:\d{2} \d{4})$"
    )
    log_close_re = re.compile(
        r"^\*\*\*\* ENDING LOGGING AT .{3} (\w{3} \d{2} \d{2}:\d{2}:\d{2} \d{4})$"
    )
    join_re = re.compile(
        r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) \*\t(.+) \(.+\) has joined .+$"
    )
    leave_re = re.compile(
        r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) \*\t(.+) \(.+\) has left \S+(?: \(\"?(.*?)\"?\))?$"
    )
    quit_re = re.compile(
        r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) \*\t(.+) has quit \((.*)\)$"
    )
    kick_re = re.compile(
        r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) \*\t(.+) has kicked (.+) from .+ \(.*\)$"
    )
    ban_re = re.compile(
        r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) \*\t(.+) sets ban on (\S+)!.+$"
    )
    me_re = re.compile(r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) \*\t(.+?) (.*)$")

    """Misc system messages that resemble /me messages but are not"""
    system_res = [
        re.compile(r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) \*\t(.+) (sets mode .+)$"),
        re.compile(
            r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) \*\t(.+) (gives channel operator status to .+)$"
        ),
        re.compile(
            r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) \*\t(.+) (gives channel half-operator status to .+)$"
        ),
        re.compile(
            r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) \*\t(.+) (removes channel operator status from .+)$"
        ),
        re.compile(
            r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) \*\t(.+) (removes channel half-operator status from .+)$"
        ),
        re.compile(r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) \*\t(.+) (removes ban on .+)$"),
        re.compile(r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) \*\t(.+) (gives voice to .+)$"),
        re.compile(
            r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) \*\t(.+) (removes voice from .+)$"
        ),
    ]

    nick_re = re.compile(
        r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) \*\t(.+) is now known as (.+)$"
    )
    you_nick_re = re.compile(
        r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) \*\t(You) are now known as (.+)$"
    )

    """ChanServ notices"""
    chanserv_re = re.compile(
        r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) -(ChanServ)-\t\[.+?\] (.+)$"
    )

    ignored_res = [
        re.compile(r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) \*\tNow talking on .+$"),
        re.compile(r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) \*\tTopic for .+ is: .*$"),
        re.compile(r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) \*\tTopic for .+ set by .+$"),
        re.compile(r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) \*\tDisconnected \(.+\).$"),
    ]

    def __init__(self, channel, utc_offset, you, source="hexchat"):
        self.channel = channel
        self.tzinfo = timezone(timedelta(hours=utc_offset))
        self.you = you
        self.source = source
        self.current_date = datetime.fromtimestamp(0, tz=self.tzinfo)

    def read(self, iterable, skip=0):
        """Transform lines from iterable into quotes"""
        self.current_date = datetime.fromtimestamp(0, tz=self.tzinfo)
        sequence_id = 1
        skipped = 0

        for line in iterable:
            line = line.rstrip("\r\n")

            if skipped < skip:
                skipped += 1
                continue

            if not any(line):
                continue

            match = self.message_re.match(line)
            if match is not None:
                yield self.make_quote(
                    match.group(1),
                    match.group(2),
                    match.group(3),
                    sequence_id,
                    QuoteType.message,
                    line,
                )
                sequence_id += 1
                continue

            match = self.topic_re.match(line)
            if match is not None:
                yield self.make_quote(
                    match.group(1),
                    match.group(2),
                    match.group(3),
                    sequence_id,
                    QuoteType.subject,
                    line,
                )
                sequence_id += 1
                continue

            match = self.join_re.match(line)
            if match is not None:
                yield self.make_quote(
                    match.group(1),
                    match.group(2),
                    "",
                    sequence_id,
                    QuoteType.join,
                    line,
                )
                sequence_id += 1
                continue

            match = self.leave_re.match(line)
            if match is not None:
                yield self.make_quote(
                    match.group(1),
                    match.group(2),
                    match.group(3),
                    sequence_id,
                    QuoteType.leave,
                    line,
                )
                sequence_id += 1
                continue

            match = self.quit_re.match(line)
            if match is not None:
                yield self.make_quote(
                    match.group(1),
                    match.group(2),
                    match.group(3),
                    sequence_id,
                    QuoteType.leave,
                    line,
                )
                sequence_id += 1
                continue

            match = self.kick_re.match(line)
            if match is not None:
                yield self.make_quote(
                    match.group(1),
                    match.group(3),
                    match.group(2),
                    sequence_id,
                    QuoteType.kick,
                    line,
                )
                sequence_id += 1
                continue

            match = self.ban_re.match(line)
            if match is not None:
                yield self.make_quote(
                    match.group(1),
                    match.group(3),
                    match.group(2),
                    sequence_id,
                    QuoteType.ban,
                    line,
                )
                sequence_id += 1
                continue

            match = self.nick_re.match(line)
            if match is not None:
                yield self.make_quote(
                    match.group(1),
                    match.group(2),
                    match.group(3),
                    sequence_id,
                    QuoteType.nick,
                    line,
                )
                sequence_id += 1
                continue

            match = self.you_nick_re.match(line)
            if match is not None:
                yield self.make_quote(
                    match.group(1),
                    self.you,
                    match.group(3),
                    sequence_id,
                    QuoteType.nick,
                    line,
                )
                sequence_id += 1
                continue

            match = self.chanserv_re.match(line)
            if match is not None:
                yield self.make_quote(
                    match.group(1),
                    match.group(2),
                    match.group(3),
                    sequence_id,
                    QuoteType.system,
                    line,
                )
                sequence_id += 1
                continue

            system_matches = (sre.match(line) for sre in self.system_res)
            match = next((m for m in system_matches if m), None)
            if match is not None:
                yield self.make_quote(
                    match.group(1),
                    "",
                    match.group(2),
                    sequence_id,
                    QuoteType.system,
                    line,
                )
                sequence_id += 1
                continue

            # handle before /me because they use the same syntax
            if any(ire.match(line) for ire in self.ignored_res):
                continue

            match = self.me_re.match(line)
            if match is not None:
                yield self.make_quote(
                    match.group(1),
                    match.group(2),
                    match.group(3),
                    sequence_id,
                    QuoteType.message,
                    line,
                )
                sequence_id += 1
                continue

            match = self.log_open_re.match(line)
            if match is not None:
                self.current_date = self.parse_timestamp(match.group(1))
                continue

            match = self.log_close_re.match(line)
            if match is not None:
                self.current_date = self.parse_timestamp(match.group(1))
                continue

            print("Unknown %s" % line)

    def make_quote(self, datetime_str, author, message, sequence_id, quote_type, raw):
        """Make a quote from a line"""
        self.current_date = self.parse_timestamp(datetime_str)

        return Quote(
            self.channel,
            sequence_id,
            author,
            message or "",
            self.current_date,
            quote_type,
            self.source,
            raw,
        )

    def parse_timestamp(self, datetime_str):
        """Parse a datetime. Datetime is in the format Jun 07 21:49:12 2012 (year optional)."""
        datetime_str = datetime_str.lower()

        # replace international month names
        for (i18n, en) in i18n_months.items():
            datetime_str = datetime_str.replace(i18n, en)

        # append year if missing
        if len(datetime_str.split()) < 4:
            datetime_str = "%s %i" % (datetime_str, self.current_date.year)

        naive = datetime.strptime(datetime_str, "%b %d %H:%M:%S %Y")
        local = datetime(
            naive.year,
            naive.month,
            naive.day,
            naive.hour,
            naive.minute,
            naive.second,
            tzinfo=self.tzinfo,
        )
        utc = local.astimezone(timezone.utc)

        # hexchat doesn't mention date changes, so handle new year's eve by adjusting the year
        # this allows for inaccuracy of up to a day without permanently screwing up the year
        if utc.date() < self.current_date.date():
            print("went from {0} to {1}".format(self.current_date, utc))
            utc = utc.replace(year=self.current_date.year + 1)

        return utc


i18n_months = {"maj": "may", "okt": "oct"}

