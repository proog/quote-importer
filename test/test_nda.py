import unittest
import io
from readers.nda import NdaLogReader
from models import QuoteType

class TestNdaLogReader(unittest.TestCase):
    def test_message(self):
        lines = io.StringIO('2017-07-22 20:56:39.123456 :Cassie!~abc@sdf.dkf.com PRIVMSG #chan :what the fuck\r\n')
        reader = NdaLogReader('#chan', 0, '')
        quote = next(reader.read(lines))
        self.assertEqual(quote.author, 'Cassie')
        self.assertEqual(quote.message, 'what the fuck')
        self.assertEqual(quote.quote_type, QuoteType.message)
        self.assertEqual(quote.timestamp.year, 2017)
        self.assertEqual(quote.timestamp.month, 7)
        self.assertEqual(quote.timestamp.day, 22)
        self.assertEqual(quote.timestamp.hour, 20)
        self.assertEqual(quote.timestamp.minute, 56)
        self.assertEqual(quote.timestamp.second, 39)

    def test_nda_message(self):
        lines = io.StringIO('2016-02-03 00:02:46.188104 Sending ^^ Sonic the Hedgehog (@sonic_hedgehog): Happy Hedgehog Day! https://t.co/AHkbFg74oo to #chan')
        reader = NdaLogReader('#chan', 0, 'nda')
        quote = next(reader.read(lines))
        self.assertEqual(quote.author, 'nda')
        self.assertEqual(quote.message, '^^ Sonic the Hedgehog (@sonic_hedgehog): Happy Hedgehog Day! https://t.co/AHkbFg74oo')
        self.assertEqual(quote.quote_type, QuoteType.message)
        self.assertEqual(quote.timestamp.year, 2016)
        self.assertEqual(quote.timestamp.month, 2)
        self.assertEqual(quote.timestamp.day, 3)
        self.assertEqual(quote.timestamp.hour, 0)
        self.assertEqual(quote.timestamp.minute, 2)
        self.assertEqual(quote.timestamp.second, 46)

    def test_message_for_different_channel(self):
        lines = io.StringIO('2017-07-22 20:56:39.123456 :Cassie!~abc@sdf.dkf.com PRIVMSG #chan :what the fuck\r\n')
        reader = NdaLogReader('#notchan', 0, '')
        quotes = list(reader.read(lines))
        self.assertFalse(quotes)

    def test_nda_message_for_different_channel(self):
        lines = io.StringIO('2016-02-03 00:02:46.188104 Sending ^^ Sonic the Hedgehog (@sonic_hedgehog): Happy Hedgehog Day! https://t.co/AHkbFg74oo to #chan')
        reader = NdaLogReader('#notchan', 0, '')
        quotes = list(reader.read(lines))
        self.assertFalse(quotes)

