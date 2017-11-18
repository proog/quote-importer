import unittest
import io
from readers.irssi import IrssiLogReader
from models import QuoteType

class TestIrssiLogReader(unittest.TestCase):
    def test_utc_offset(self):
        cases = [
            (0, 20),
            (1, 19),
            (11, 9),
            (-1, 21),
            (-11, 7)
        ]
        for (offset_hours, expected_utc_hour) in cases:
            lines = io.StringIO('20:56 <&Cassie> what the fuck')
            reader = IrssiLogReader('', 0, offset_hours, '')
            quote = next(reader.read(lines))
            self.assertEqual(quote.timestamp.hour, expected_utc_hour)

    def test_nick(self):
        cases = ['Duo', 'You', 'you']
        for nick in cases:
            lines = io.StringIO('20:56 -!- %s is now known as udo' % nick)
            reader = IrssiLogReader('', 0, 0, 'Skanker')
            quote = next(reader.read(lines))
            self.assertEqual(quote.quote_type, QuoteType.nick)
            self.assertEqual(quote.author, nick)
            self.assertEqual(quote.message, 'udo')

    def test_you_nick(self):
        lines = io.StringIO('20:56 -!- You\'re now known as udo')
        reader = IrssiLogReader('', 0, 0, 'Duo')
        quote = next(reader.read(lines))
        self.assertEqual(quote.quote_type, QuoteType.nick)
        self.assertEqual(quote.author, 'Duo')
        self.assertEqual(quote.message, 'udo')

    def test_ban(self):
        cases = [
            ('+b anyname!*@*', 'anyname'),
            ('-o+b noskillbassist *!*@*.hsd1.ca.comcast.net', 'noskillbassist'),
            ('-o+b Calum *!*moo@*.34329884.17AA9C3B.IP', 'Calum'),
            ('+ic-S+b +v!*@*', '+v')
        ]
        for (mode, author) in cases:
            lines = io.StringIO('20:56 -!- mode/#garachat [%s] by Ebichu' % mode)
            reader = IrssiLogReader('', 0, 0, '')
            quote = next(reader.read(lines))
            self.assertEqual(quote.quote_type, QuoteType.ban)
            self.assertEqual(quote.author, author)

    def test_message(self):
        lines = io.StringIO('20:56 <&Cassie> what the fuck')
        reader = IrssiLogReader('', 0, 0, '')
        quote = next(reader.read(lines))
        self.assertEqual(quote.quote_type, QuoteType.message)
        self.assertEqual(quote.author, '&Cassie')
        self.assertEqual(quote.message, 'what the fuck')

    def test_message_glitch(self):
        lines = io.StringIO('20:56 20:56 <&Cassie> what the fuck<&Cassie> what the fuck')
        reader = IrssiLogReader('', 0, 0, '')
        quote = next(reader.read(lines))
        self.assertEqual(quote.quote_type, QuoteType.message)
        self.assertEqual(quote.author, '&Cassie')
        self.assertEqual(quote.message, 'what the fuck')
