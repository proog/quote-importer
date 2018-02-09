import io
import pytest
from readers.nda import NdaLogReader
from models import QuoteType

def test_message():
    lines = io.StringIO('2017-07-22 20:56:39.123456 :Cassie!~abc@sdf.dkf.com PRIVMSG #chan :what the fuck\r\n')
    reader = NdaLogReader('#chan', '')
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
    reader = NdaLogReader('#chan', 'nda')
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
    reader = NdaLogReader('#notchan', '')
    quotes = list(reader.read(lines))
    assert not quotes

def test_nda_message_for_different_channel():
    lines = io.StringIO('2016-02-03 00:02:46.188104 Sending ^^ Sonic the Hedgehog (@sonic_hedgehog): Happy Hedgehog Day! https://t.co/AHkbFg74oo to #chan')
    reader = NdaLogReader('#notchan', '')
    quotes = list(reader.read(lines))
    assert not quotes

def test_join():
    lines = io.StringIO('2017-07-22 20:56:39.123456 :Cassie!~abc@sdf.dkf.com JOIN #chan')
    reader = NdaLogReader('#chan', '')
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.join
    assert quote.author == 'Cassie'

def test_join_different_channel():
    lines = io.StringIO('2017-07-22 20:56:39.123456 :Cassie!~abc@sdf.dkf.com JOIN #chan')
    reader = NdaLogReader('#notchan', '')
    assert not list(reader.read(lines))

def test_nda_nick():
    lines = io.StringIO(
        '2017-07-22 20:56:39.123456 Sending hi to #chan\n' +
        '2017-07-22 20:56:39.123456 Sending NICK nda_\n' +
        '2017-07-22 20:56:39.123456 Sending hi 2 to #chan\n' +
        '2017-07-22 20:56:39.123456 Sending NICK nda_\n' +
        '2017-07-22 20:56:39.123456 Sending hi 3 to #chan')
    reader = NdaLogReader('#chan', 'nda')
    quotes = list(reader.read(lines))
    assert len(quotes) == 4
    assert quotes[0].quote_type == QuoteType.message
    assert quotes[0].author == 'nda'
    assert quotes[1].quote_type == QuoteType.nick
    assert quotes[1].author == 'nda'
    assert quotes[1].message == 'nda_'
    assert quotes[2].quote_type == QuoteType.message
    assert quotes[2].author == 'nda_'
    # nda nick didn't change, so no nick type quote here
    assert quotes[3].quote_type == QuoteType.message
    assert quotes[3].author == 'nda_'

@pytest.mark.parametrize('mode, message', [
    ('+b anyname!*@*', 'anyname'),
    ('-o+b noskillbassist *!*@*.hsd1.ca.comcast.net', 'noskillbassist'),
    ('-o+b Calum *!*moo@*.34329884.17AA9C3B.IP', 'Calum'),
    ('+ic-S+b +v!*@*', '+v')
])
def test_ban(mode, message):
    lines = io.StringIO('2017-07-22 20:56:39.123456 :Cassie!~abc@sdf.dkf.com MODE #chan %s' % mode)
    reader = NdaLogReader('#chan', '')
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.ban
    assert quote.author == 'Cassie'
    assert quote.message == message

def test_ban_different_channel():
    lines = io.StringIO('2017-07-22 20:56:39.123456 :Cassie!~abc@sdf.dkf.com MODE #chan +b anyname!*@*')
    reader = NdaLogReader('#notchan', '')
    assert not list(reader.read(lines))

def test_kick():
    lines = io.StringIO('2017-07-22 20:56:39.123456 :Cassie!~abc@sdf.dkf.com KICK #chan anyname :fuck off')
    reader = NdaLogReader('#chan', '')
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.kick
    assert quote.author == 'Cassie'
    assert quote.message == 'anyname'

def test_kick_different_channel():
    lines = io.StringIO('2017-07-22 20:56:39.123456 :Cassie!~abc@sdf.dkf.com KICK #chan anyname :fuck off')
    reader = NdaLogReader('#notchan', '')
    assert not list(reader.read(lines))
