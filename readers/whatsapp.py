'''Read WhatsApp logs'''
import re
from datetime import datetime, timedelta, timezone
from models import Quote, QuoteType

class WhatsAppLogReader:
    '''Read a WhatsApp log file'''

    '''
    Matches all combinations of:
    - 1 and 2 digit day of month
    - 1 and 2 digit month
    - 1, 2 and 4 digit year
    - time with and without seconds
    - time units separated by colon or dot
    - time and author separated by colon-space or space-dash-space
    Remember to check the length of the year and time when parsing!
    '''
    message_re = re.compile(r'^(\d{1,2}\/\d{1,2}\/\d{1,4}), (\d{2}.\d{2}(?:.\d{2})?)(?::| -) (.+?): (.*)$')

    subject_re = re.compile(r'^(\d{1,2}\/\d{1,2}\/\d{1,4}), (\d{2}.\d{2}(?:.\d{2})?)(?::| -) (.+) changed the subject from .* to (?:"|“)(.*)(?:"|”)$')
    icon_re = re.compile(r'^(\d{1,2}\/\d{1,2}\/\d{1,4}), (\d{2}.\d{2}(?:.\d{2})?)(?::| -) (.+) (changed this group\'s icon)$')
    join_re = re.compile(r'^(\d{1,2}\/\d{1,2}\/\d{1,4}), (\d{2}.\d{2}(?:.\d{2})?)(?::| -) .+ added (.+)$')
    leave_re = re.compile(r'^(\d{1,2}\/\d{1,2}\/\d{1,4}), (\d{2}.\d{2}(?:.\d{2})?)(?::| -) (.+) left$')
    kick_re = re.compile(r'^(\d{1,2}\/\d{1,2}\/\d{1,4}), (\d{2}.\d{2}(?:.\d{2})?)(?::| -) .+ removed (.+)$')
    system_re = re.compile(r'^(\d{1,2}\/\d{1,2}\/\d{1,4}), (\d{2}.\d{2}(?:.\d{2})?)(?::| -) ()(.+)$')

    def __init__(self, channel, start_sequence_id, utc_offset, date_order, you, source='whatsapp'):
        self.channel = channel
        self.start_sequence_id = start_sequence_id
        self.tzinfo = timezone(timedelta(hours=utc_offset))
        self.date_order = date_order
        self.you = you
        self.source = source

    def read(self, iterable, skip=0):
        '''Transform lines from iterable into quotes'''
        sequence_id = self.start_sequence_id
        current = None
        skipped = 0

        for line in iterable:
            line = line.rstrip('\r\n')

            if skipped < skip:
                skipped += 1
                continue

            match = self.message_re.match(line)
            if match is not None:
                if current is not None:
                    yield current

                current = self.start_quote(match, sequence_id, QuoteType.message)
                sequence_id += 1
                continue

            match = self.subject_re.match(line)
            if match is not None:
                if current is not None:
                    yield current

                current = self.start_quote(match, sequence_id, QuoteType.subject)
                sequence_id += 1
                continue

            match = self.icon_re.match(line)
            if match is not None:
                if current is not None:
                    yield current

                current = self.start_quote(match, sequence_id, QuoteType.subject)
                sequence_id += 1
                continue

            match = self.join_re.match(line)
            if match is not None:
                if current is not None:
                    yield current

                current = self.start_quote(match, sequence_id, QuoteType.join)
                sequence_id += 1
                continue

            match = self.leave_re.match(line)
            if match is not None:
                if current is not None:
                    yield current

                current = self.start_quote(match, sequence_id, QuoteType.leave)
                sequence_id += 1
                continue

            match = self.kick_re.match(line)
            if match is not None:
                if current is not None:
                    yield current

                current = self.start_quote(match, sequence_id, QuoteType.kick)
                sequence_id += 1
                continue

            match = self.system_re.match(line)
            if match is not None:
                if current is not None:
                    yield current

                current = self.start_quote(match, sequence_id, QuoteType.system)
                sequence_id += 1
                continue

            if current is not None:
                current.message += '\n' + line # append to unfinished quote
                current.raw += '\n' + line
                continue

            print('Unknown %s' % line)

        if current is not None:
            yield current

    def start_quote(self, match, sequence_id, quote_type):
        '''Make a quote from a line. Its message may not be finished on this line'''
        groups = match.groups()
        timestamp = self.parse_timestamp(groups[0], groups[1])
        author = groups[2]
        message = groups[3] if len(groups) >= 4 else ''
        raw = match.string

        if author == 'You' or author == 'you':
            author = self.you

        return Quote(self.channel, sequence_id, author, message, timestamp, quote_type, self.source, raw)

    def parse_timestamp(self, date_part, time_part):
        '''Parse timestamp from a date part and a time part of varying formatting'''
        split_date = date_part.split('/')
        split_time = time_part.replace('.', ':').split(':')

        if len(split_date[2]) == 1:
            split_date[2] = '200%s' % split_date[2]
        elif len(split_date[2]) == 2:
            split_date[2] = '20%s' % split_date[2]

        day = int(split_date[1 if self.date_order == DateOrder.american else 0])
        month = int(split_date[0 if self.date_order == DateOrder.american else 1])
        year = int(split_date[2])
        hours = int(split_time[0])
        minutes = int(split_time[1] if len(split_time) > 1 else 0)
        seconds = int(split_time[2] if len(split_time) > 2 else 0)

        local_dt = datetime(year, month, day, hours, minutes, seconds, tzinfo=self.tzinfo)
        return local_dt.astimezone(timezone.utc)

class DateOrder():
    '''Whether to use the D/M/Y or M/D/Y when parsing dates'''
    standard = 'standard'
    american = 'american'
