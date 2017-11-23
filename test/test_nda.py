import io
from readers.nda import NdaLogReader
from models import QuoteType

def test_message():
    lines = io.StringIO('2017-07-22 20:56:39.123456 :Cassie!~abc@sdf.dkf.com PRIVMSG #chan :what the fuck\r\n')
    reader = NdaLogReader('#chan', 0, '')
    quote = next(reader.read(lines))
    assert quote.author == 'Cassie'
    assert quote.message == 'what the fuck'
    assert quote.quote_type == QuoteType.message
    assert quote.timestamp.year == 2017
    assert quote.timestamp.month == 7
    assert quote.timestamp.day == 22
    assert quote.timestamp.hour == 20
    assert quote.timestamp.minute == 56
    assert quote.timestamp.second == 39

def test_nda_message():
    lines = io.StringIO('2016-02-03 00:02:46.188104 Sending ^^ Sonic the Hedgehog (@sonic_hedgehog): Happy Hedgehog Day! https://t.co/AHkbFg74oo to #chan')
    reader = NdaLogReader('#chan', 0, 'nda')
    quote = next(reader.read(lines))
    assert quote.author == 'nda'
    assert quote.message == '^^ Sonic the Hedgehog (@sonic_hedgehog): Happy Hedgehog Day! https://t.co/AHkbFg74oo'
    assert quote.quote_type == QuoteType.message
    assert quote.timestamp.year == 2016
    assert quote.timestamp.month == 2
    assert quote.timestamp.day == 3
    assert quote.timestamp.hour == 0
    assert quote.timestamp.minute == 2
    assert quote.timestamp.second == 46

def test_message_for_different_channel():
    lines = io.StringIO('2017-07-22 20:56:39.123456 :Cassie!~abc@sdf.dkf.com PRIVMSG #chan :what the fuck\r\n')
    reader = NdaLogReader('#notchan', 0, '')
    quotes = list(reader.read(lines))
    assert not quotes

def test_nda_message_for_different_channel():
    lines = io.StringIO('2016-02-03 00:02:46.188104 Sending ^^ Sonic the Hedgehog (@sonic_hedgehog): Happy Hedgehog Day! https://t.co/AHkbFg74oo to #chan')
    reader = NdaLogReader('#notchan', 0, '')
    quotes = list(reader.read(lines))
    assert not quotes
