'''Read NDA logs'''
import re
from datetime import datetime, timezone, timedelta
from models import Quote, QuoteType

class NdaLogReader:
    '''Read an NDA log file'''

    message_re = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d{6} :(.+)!.+ PRIVMSG (.+) :(.*)$')
    join_re = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d{6} :(.+)!.+ JOIN .+$')
    leave_re = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d{6} :(.+)!.+ PART (.+)( :(.*))?$')
    quit_re = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d{6} :(.+)!.+ QUIT :(.*)$')
    kick_re = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d{6} :(.+)!.+ KICK (.+) (.+) :.+$')
    nick_re = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d{6} :(.+)!.+ NICK :(.+)$')
    topic_re = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d{6} :(.+)!.+ TOPIC (.+) :(.+)$')
    ban_re = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d{6} :(.+)!.+ MODE (.+) \S*\+b\S* (\S+)!.+$')
    ban2_re = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d{6} :(.+)!.+ MODE (.+) \S*\+b\S* (\S+) \S+!.+$')
    nda_message_re = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d{6} Sending (.*) to (.+)$')
    nda_nick_re = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d{6} Sending NICK (.+)$')
    nda_quit_re = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d{6} Sending QUIT :(.+)$')

    ignored = [
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} Connecting to .+$',
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} Disconnecting from .+$',
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} ERROR .*$',
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} Error received from the server.*$',
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} No PING received from the server.*$',
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} IRC error.*$',
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} OS error.*$',
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} Unknown error.*$',
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} An error occurred while disconnecting.*$',
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} Traceback.*$',
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} redis message: .*$',
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} PING :.+$',
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} :.+ PONG .+ :.+$',
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} Sending PING :.+$',
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} Sending PONG :.+$',
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} Sending JOIN .+$',
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} Sending ISON .+$',
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} :.+ \d{3} .+$',  # server connect info
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} :.+ 303 .+ :.*$',  # ison reply
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} :.+ NOTICE .+ :.+$',  # server notice
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} :.+ MODE .+$',  # non-ban mode
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} $'  # empty
    ]
    ignored_re = re.compile('(' + ')|('.join(ignored) + ')')

    def __init__(self, channel, start_sequence_id, you, source='nda'):
        self.channel = channel
        self.start_sequence_id = start_sequence_id
        self.you = you
        self.source = source

    def read(self, iterable, skip=0):
        '''Transform lines from iterable into quotes'''
        sequence_id = self.start_sequence_id
        skipped = 0

        for line in iterable:
            line = line.rstrip('\r\n')

            if skipped < skip:
                skipped += 1
                continue

            match = self.message_re.match(line)
            if match is not None:
                # only match if the message matches the channel we're reading
                if match.group(3) == self.channel:
                    yield self.make_quote(match.group(1), match.group(2), match.group(4), sequence_id, QuoteType.message, line)
                    sequence_id += 1
                continue

            match = self.join_re.match(line)
            if match is not None:
                yield self.make_quote(match.group(1), match.group(2), '', sequence_id, QuoteType.join, line)
                sequence_id += 1
                continue

            match = self.leave_re.match(line)
            if match is not None:
                if match.group(3) == self.channel:
                    yield self.make_quote(match.group(1), match.group(2), match.group(5), sequence_id, QuoteType.leave, line)
                    sequence_id += 1
                continue

            match = self.quit_re.match(line)
            if match is not None:
                yield self.make_quote(match.group(1), match.group(2), match.group(3), sequence_id, QuoteType.leave, line)
                sequence_id += 1
                continue

            match = self.kick_re.match(line)
            if match is not None:
                if match.group(3) == self.channel:
                    yield self.make_quote(match.group(1), match.group(2), match.group(4), sequence_id, QuoteType.kick, line)
                    sequence_id += 1
                continue

            match = self.nick_re.match(line)
            if match is not None:
                yield self.make_quote(match.group(1), match.group(2), match.group(3), sequence_id, QuoteType.nick, line)
                sequence_id += 1
                continue

            match = self.topic_re.match(line)
            if match is not None:
                if match.group(3) == self.channel:
                    yield self.make_quote(match.group(1), match.group(2), match.group(4), sequence_id, QuoteType.subject, line)
                    sequence_id += 1
                continue

            match = self.ban_re.match(line)
            if match is not None:
                if match.group(3) == self.channel:
                    yield self.make_quote(match.group(1), match.group(2), match.group(4), sequence_id, QuoteType.ban, line)
                    sequence_id += 1
                continue

            match = self.ban2_re.match(line)
            if match is not None:
                if match.group(3) == self.channel:
                    yield self.make_quote(match.group(1), match.group(2), match.group(4), sequence_id, QuoteType.ban, line)
                    sequence_id += 1
                continue

            match = self.nda_message_re.match(line)
            if match is not None:
                if match.group(3) == self.channel:
                    yield self.make_quote(match.group(1), self.you, match.group(2), sequence_id, QuoteType.message, line)
                    sequence_id += 1
                continue

            match = self.nda_nick_re.match(line)
            if match is not None:
                yield self.make_quote(match.group(1), self.you, match.group(2), sequence_id, QuoteType.nick, line)
                sequence_id += 1
                continue

            match = self.nda_quit_re.match(line)
            if match is not None:
                yield self.make_quote(match.group(1), self.you, match.group(2), sequence_id, QuoteType.leave, line)
                sequence_id += 1
                continue

            # handle known unusable lines; this is done last because some of them are pretty general
            if self.ignored_re.match(line) is not None:
                continue

            print('Unknown: %s' % line)

    def make_quote(self, datetime_str, author, message, sequence_id, quote_type, raw):
        '''Make a quote from a line'''

        if author is None:
            author = ''
        if message is None:
            message = ''

        timestamp = self.parse_timestamp(datetime_str)
        return Quote(self.channel, sequence_id, author, message, timestamp, quote_type, self.source, raw)

    def parse_timestamp(self, datetime_str):
        '''Parse a timestamp from a string like "2015-11-19 12:34:56"'''
        (date_str, time_str) = datetime_str.split()
        (year, month, day) = [int(x) for x in date_str.split('-')]
        (hours, minutes, seconds) = [int(x) for x in time_str.split(':')]

        # nda always logs in utc
        return datetime(year, month, day, hours, minutes, seconds, tzinfo=timezone.utc)
