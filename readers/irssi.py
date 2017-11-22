'''Read irssi logs'''
import re
from datetime import datetime, timezone, timedelta
from models import Quote, QuoteType

class IrssiLogReader:
    '''Read an irssi log file'''

    '''Regular message''' # pylint: disable=W0105
    message_re = re.compile(r'^(\d{2}):(\d{2}) <(.+)> (.*)$')

    '''Glitched out line with the message interleaved with itself'''
    message_glitch_re = re.compile(r'^(\d{2}):(\d{2}) \d{2}:\d{2} <(.+)> (.*)<.+> .*$')

    topic_re = re.compile(r'^(\d{2}):(\d{2}) (.+) changed the topic of .+ to: (.*)$')
    log_open_re = re.compile(r'^--- Log opened .{3} (\w{3}) (\d{2}) .{8} (\d{4})$')
    log_close_re = re.compile(r'^--- Log closed .{3} (\w{3}) (\d{2}) .{8} (\d{4})$')
    date_re = re.compile(r'^--- Day changed .{3} (\w{3}) (\d{2}) (\d{4})$')
    join_re = re.compile(r'^(\d{2}):(\d{2}) -!- (.+) \[.+\] has joined .+$')
    leave_re = re.compile(r'^(\d{2}):(\d{2}) -!- (.+) \[.+\] has left .+ \[(.*)\]$')
    quit_re = re.compile(r'^(\d{2}):(\d{2}) -!- (.+) \[.+\] has quit \[(.*)\]$')
    kick_re = re.compile(r'^(\d{2}):(\d{2}) -!- (.+) was kicked from .+ by .+ \[.*\]$')

    '''Mode +b nick!*@*'''
    ban_re = re.compile(r'^(\d{2}):(\d{2}) -!- mode\/.+ \[.*\+b\S* (\S+)!.+\] by .+$')

    '''Mode +b nick *!*@*'''
    ban2_re = re.compile(r'^(\d{2}):(\d{2}) -!- mode\/.+ \[.*\+b\S* (\S+) \S+!.+\] by .+$')

    '''/me command: "* nick message"'''
    me_re = re.compile(r'^(\d{2}):(\d{2})  \* (.+) (.*)$')

    nick_re = re.compile(r'^(\d{2}):(\d{2}) -!- (.+) is now known as (.+)$')
    you_nick_re = re.compile(r'^(\d{2}):(\d{2}) -!- (You)\'re now known as (.+)$')

    '''Channel invites, which are usually followed by a join'''
    invite_re = re.compile(r'^(\d{2}):(\d{2}) .+ (.+) (invited .+ into the channel)\.$')
    invite2_re = re.compile(r'^(\d{2}):(\d{2}) .+ \*\*\* (.+) (invited .+ into the channel)$')

    '''ChanServ notices'''
    chanserv_re = re.compile(r'^(\d{2}):(\d{2}) -(ChanServ):.+- (.+)$')

    '''Some sort of channel notice from a real user. Match after chanserv_re because it's less specific'''
    chan_message_re = re.compile(r'^(\d{2}):(\d{2}) -(.+):.+- (.*)$')

    '''Recognizable, but unspecific system messages with a timestamp and no author'''
    system_re = re.compile(r'^(\d{2}):(\d{2}) -!- ()(.*)$')

    def __init__(self, channel, start_sequence_id, utc_offset, you, source='irssi'):
        self.channel = channel
        self.start_sequence_id = start_sequence_id
        self.tzinfo = timezone(timedelta(hours=utc_offset))
        self.you = you
        self.source = source

    def read(self, iterable, skip=0):
        '''Transform lines from iterable into quotes'''
        sequence_id = self.start_sequence_id
        date = datetime.utcfromtimestamp(0)
        skipped = 0

        for line in iterable:
            line = line.rstrip('\r\n')

            if skipped < skip:
                skipped += 1
                continue

            match = self.message_re.match(line)
            if match is not None:
                yield self.make_quote(match, date, sequence_id, QuoteType.message)
                sequence_id += 1
                continue

            match = self.message_glitch_re.match(line)
            if match is not None:
                yield self.make_quote(match, date, sequence_id, QuoteType.message)
                sequence_id += 1
                continue

            match = self.topic_re.match(line)
            if match is not None:
                yield self.make_quote(match, date, sequence_id, QuoteType.subject)
                sequence_id += 1
                continue

            match = self.join_re.match(line)
            if match is not None:
                yield self.make_quote(match, date, sequence_id, QuoteType.join)
                sequence_id += 1
                continue

            match = self.leave_re.match(line)
            if match is not None:
                yield self.make_quote(match, date, sequence_id, QuoteType.leave)
                sequence_id += 1
                continue

            match = self.quit_re.match(line)
            if match is not None:
                yield self.make_quote(match, date, sequence_id, QuoteType.leave)
                sequence_id += 1
                continue

            match = self.kick_re.match(line)
            if match is not None:
                yield self.make_quote(match, date, sequence_id, QuoteType.kick)
                sequence_id += 1
                continue

            match = self.ban_re.match(line)
            if match is not None:
                yield self.make_quote(match, date, sequence_id, QuoteType.ban)
                sequence_id += 1
                continue

            match = self.ban2_re.match(line)
            if match is not None:
                yield self.make_quote(match, date, sequence_id, QuoteType.ban)
                sequence_id += 1
                continue

            match = self.me_re.match(line)
            if match is not None:
                yield self.make_quote(match, date, sequence_id, QuoteType.message)
                sequence_id += 1
                continue

            match = self.nick_re.match(line)
            if match is not None:
                yield self.make_quote(match, date, sequence_id, QuoteType.nick)
                sequence_id += 1
                continue

            match = self.you_nick_re.match(line)
            if match is not None:
                yield self.make_quote(match, date, sequence_id, QuoteType.nick, True)
                sequence_id += 1
                continue

            match = self.invite_re.match(line)
            if match is not None:
                yield self.make_quote(match, date, sequence_id, QuoteType.system)
                sequence_id += 1
                continue

            match = self.invite2_re.match(line)
            if match is not None:
                yield self.make_quote(match, date, sequence_id, QuoteType.system)
                sequence_id += 1
                continue

            match = self.chanserv_re.match(line)
            if match is not None:
                yield self.make_quote(match, date, sequence_id, QuoteType.system)
                sequence_id += 1
                continue

            match = self.chan_message_re.match(line)
            if match is not None:
                yield self.make_quote(match, date, sequence_id, QuoteType.message)
                sequence_id += 1
                continue

            match = self.system_re.match(line)
            if match is not None:
                yield self.make_quote(match, date, sequence_id, QuoteType.system)
                sequence_id += 1
                continue

            match = self.date_re.match(line)
            if match is not None:
                date = parse_date(match)
                continue

            match = self.log_open_re.match(line)
            if match is not None:
                date = parse_date(match)
                continue

            match = self.log_close_re.match(line)
            if match is not None:
                date = parse_date(match)
                continue

            print('Unknown %s' % line)

    def make_quote(self, match, date, sequence_id, quote_type, is_you=False):
        '''Make a quote from a line'''
        groups = match.groups()
        hours = int(groups[0])
        minutes = int(groups[1])
        author = self.you if is_you else groups[2]
        message = groups[3] if len(groups) >= 4 else ''
        raw = match.string

        local_dt = datetime(date.year, date.month, date.day, hours, minutes, 0, tzinfo=self.tzinfo)
        timestamp = local_dt.astimezone(timezone.utc)

        return Quote(self.channel, sequence_id, author, message, timestamp, quote_type, self.source, raw)

def parse_date(match):
    '''Parse a date for when the date changes. We just use some of its parts, so it can be naive'''
    groups = match.groups()
    month_name = groups[0]
    day = groups[1]
    year = groups[2]
    date_str = "%s %s %s" % (month_name, day, year)
    return datetime.strptime(date_str, '%b %d %Y')
