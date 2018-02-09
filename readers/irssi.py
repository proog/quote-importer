'''Read irssi logs'''
import re
from datetime import datetime, timezone, timedelta
from models import Quote, QuoteType

class IrssiLogReader:
    '''Read an irssi log file'''

    '''Regular message''' # pylint: disable=W0105
    message_re = re.compile(r'^(\d{2}:\d{2}) <(.+?)> (.*)$')

    '''Glitched out line with the message interleaved with itself'''
    message_glitch_re = re.compile(r'^(\d{2}:\d{2}) \d{2}:\d{2} <(.+?)> (.*)<.+?> .*$')

    topic_re = re.compile(r'^(\d{2}:\d{2}) (.+) changed the topic of .+ to: (.*)$')
    log_open_re = re.compile(r'^--- Log opened .{3} (\w{3}) (\d{2}) .{8} (\d{4})$')
    log_close_re = re.compile(r'^--- Log closed .{3} (\w{3}) (\d{2}) .{8} (\d{4})$')
    date_re = re.compile(r'^--- Day changed .{3} (\w{3}) (\d{2}) (\d{4})$')
    join_re = re.compile(r'^(\d{2}:\d{2}) -!- (.+) \[.+\] has joined .+$')
    leave_re = re.compile(r'^(\d{2}:\d{2}) -!- (.+) \[.+\] has left .+ \[(.*)\]$')
    quit_re = re.compile(r'^(\d{2}:\d{2}) -!- (.+) \[.+\] has quit \[(.*)\]$')
    kick_re = re.compile(r'^(\d{2}:\d{2}) -!- (.+) was kicked from .+ by (.+) \[.*\]$')

    '''Mode +b nick!*@*'''
    ban_re = re.compile(r'^(\d{2}:\d{2}) -!- mode\/.+ \[.*\+b\S* (\S+)!.+\] by (.+)$')

    '''Mode +b nick *!*@*'''
    ban2_re = re.compile(r'^(\d{2}:\d{2}) -!- mode\/.+ \[.*\+b\S* (\S+) \S+!.+\] by (.+)$')

    '''/me command: "* nick message"'''
    me_re = re.compile(r'^(\d{2}:\d{2})  \* (.+?) (.*)$')

    nick_re = re.compile(r'^(\d{2}:\d{2}) -!- (.+) is now known as (.+)$')
    you_nick_re = re.compile(r'^(\d{2}:\d{2}) -!- (You)\'re now known as (.+)$')

    '''Channel invites, which are usually followed by a join'''
    invite_re = re.compile(r'^(\d{2}:\d{2}) .+ (.+) (invited .+ into the channel)\.$')
    invite2_re = re.compile(r'^(\d{2}:\d{2}) .+ \*\*\* (.+) (invited .+ into the channel)$')

    '''ChanServ notices'''
    chanserv_re = re.compile(r'^(\d{2}:\d{2}) -(ChanServ):.+?- (.+)$')

    '''Some sort of channel notice from a real user. Match after chanserv_re because it's less specific'''
    chan_message_re = re.compile(r'^(\d{2}:\d{2}) -(.+?):.+?- (.*)$')

    '''Recognizable, but unspecific system messages with a timestamp and no author'''
    system_re = re.compile(r'^(\d{2}:\d{2}) -!- (.*)$')

    def __init__(self, channel, utc_offset, you, source='irssi'):
        self.channel = channel
        self.tzinfo = timezone(timedelta(hours=utc_offset))
        self.you = you
        self.source = source

    def read(self, iterable, skip=0):
        '''Transform lines from iterable into quotes'''
        sequence_id = 1
        date = datetime.utcfromtimestamp(0)
        skipped = 0

        for line in iterable:
            line = line.rstrip('\r\n')

            if skipped < skip:
                skipped += 1
                continue

            match = self.message_re.match(line)
            if match is not None:
                yield self.make_quote(date, match.group(1), match.group(2), match.group(3), sequence_id, QuoteType.message, line)
                sequence_id += 1
                continue

            match = self.message_glitch_re.match(line)
            if match is not None:
                yield self.make_quote(date, match.group(1), match.group(2), match.group(3), sequence_id, QuoteType.message, line)
                sequence_id += 1
                continue

            match = self.topic_re.match(line)
            if match is not None:
                yield self.make_quote(date, match.group(1), match.group(2), match.group(3), sequence_id, QuoteType.subject, line)
                sequence_id += 1
                continue

            match = self.join_re.match(line)
            if match is not None:
                yield self.make_quote(date, match.group(1), match.group(2), '', sequence_id, QuoteType.join, line)
                sequence_id += 1
                continue

            match = self.leave_re.match(line)
            if match is not None:
                yield self.make_quote(date, match.group(1), match.group(2), match.group(3), sequence_id, QuoteType.leave, line)
                sequence_id += 1
                continue

            match = self.quit_re.match(line)
            if match is not None:
                yield self.make_quote(date, match.group(1), match.group(2), match.group(3), sequence_id, QuoteType.leave, line)
                sequence_id += 1
                continue

            match = self.kick_re.match(line)
            if match is not None:
                yield self.make_quote(date, match.group(1), match.group(3), match.group(2), sequence_id, QuoteType.kick, line)
                sequence_id += 1
                continue

            match = self.ban_re.match(line)
            if match is not None:
                yield self.make_quote(date, match.group(1), match.group(3), match.group(2), sequence_id, QuoteType.ban, line)
                sequence_id += 1
                continue

            match = self.ban2_re.match(line)
            if match is not None:
                yield self.make_quote(date, match.group(1), match.group(3), match.group(2), sequence_id, QuoteType.ban, line)
                sequence_id += 1
                continue

            match = self.me_re.match(line)
            if match is not None:
                yield self.make_quote(date, match.group(1), match.group(2), match.group(3), sequence_id, QuoteType.message, line)
                sequence_id += 1
                continue

            match = self.nick_re.match(line)
            if match is not None:
                yield self.make_quote(date, match.group(1), match.group(2), match.group(3), sequence_id, QuoteType.nick, line)
                sequence_id += 1
                continue

            match = self.you_nick_re.match(line)
            if match is not None:
                yield self.make_quote(date, match.group(1), self.you, match.group(3), sequence_id, QuoteType.nick, line)
                sequence_id += 1
                continue

            match = self.invite_re.match(line)
            if match is not None:
                yield self.make_quote(date, match.group(1), match.group(2), match.group(3), sequence_id, QuoteType.system, line)
                sequence_id += 1
                continue

            match = self.invite2_re.match(line)
            if match is not None:
                yield self.make_quote(date, match.group(1), match.group(2), match.group(3), sequence_id, QuoteType.system, line)
                sequence_id += 1
                continue

            match = self.chanserv_re.match(line)
            if match is not None:
                yield self.make_quote(date, match.group(1), match.group(2), match.group(3), sequence_id, QuoteType.system, line)
                sequence_id += 1
                continue

            match = self.chan_message_re.match(line)
            if match is not None:
                yield self.make_quote(date, match.group(1), match.group(2), match.group(3), sequence_id, QuoteType.message, line)
                sequence_id += 1
                continue

            match = self.system_re.match(line)
            if match is not None:
                yield self.make_quote(date, match.group(1), '', match.group(2), sequence_id, QuoteType.system, line)
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

    def make_quote(self, date, time_str, author, message, sequence_id, quote_type, raw):
        '''Make a quote from a line'''
        (hours, minutes) = [int(x) for x in time_str.split(':')]

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
