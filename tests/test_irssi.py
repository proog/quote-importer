import io
import pytest
from readers.irssi import IrssiLogReader
from models import QuoteType

@pytest.mark.parametrize('offset_hours, expected_utc_hour', [
    (0, 20),
    (1, 19),
    (11, 9),
    (-1, 21),
    (-11, 7)
])
def test_utc_offset(offset_hours, expected_utc_hour):
    lines = io.StringIO('20:56 <&Cassie> what the fuck')
    reader = IrssiLogReader('', 0, offset_hours, '')
    quote = next(reader.read(lines))
    assert quote.timestamp.hour == expected_utc_hour

@pytest.mark.parametrize('nick', ['Duo', 'You', 'you'])
def test_nick(nick):
    lines = io.StringIO('20:56 -!- %s is now known as udo' % nick)
    reader = IrssiLogReader('', 0, 0, 'Skanker')
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.nick
    assert quote.author == nick
    assert quote.message == 'udo'

def test_you_nick():
    lines = io.StringIO('20:56 -!- You\'re now known as udo')
    reader = IrssiLogReader('', 0, 0, 'Duo')
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.nick
    assert quote.author == 'Duo'
    assert quote.message == 'udo'

@pytest.mark.parametrize('mode, author', [
    ('+b anyname!*@*', 'anyname'),
    ('-o+b noskillbassist *!*@*.hsd1.ca.comcast.net', 'noskillbassist'),
    ('-o+b Calum *!*moo@*.34329884.17AA9C3B.IP', 'Calum'),
    ('+ic-S+b +v!*@*', '+v')
])
def test_ban(mode, author):
    lines = io.StringIO('20:56 -!- mode/#garachat [%s] by Ebichu' % mode)
    reader = IrssiLogReader('', 0, 0, '')
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.ban
    assert quote.author == author

def test_message():
    lines = io.StringIO('20:56 <&Cassie> what the fuck')
    reader = IrssiLogReader('', 0, 0, '')
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.message
    assert quote.author == '&Cassie'
    assert quote.message == 'what the fuck'

def test_message_glitch():
    lines = io.StringIO('20:56 20:56 <&Cassie> what the fuck<&Cassie> what the fuck')
    reader = IrssiLogReader('', 0, 0, '')
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.message
    assert quote.author == '&Cassie'
    assert quote.message == 'what the fuck'

def test_skip():
    lines = io.StringIO('20:56 <&Cassie> what the fuck\n' +
                        '20:56 -!- Duo is now known as udo\n' +
                        '20:58 <&ashin> also swear words')
    reader = IrssiLogReader('', 0, 0, '')
    quotes = list(reader.read(lines, 2))
    assert len(quotes) == 1
    assert quotes[0].message == 'also swear words'
