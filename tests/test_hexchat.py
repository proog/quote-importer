import io
import pytest
from quoteimporter.readers.hexchat import HexChatLogReader
from quoteimporter.models import QuoteType


@pytest.mark.parametrize("nick", ["Duo", "You", "you"])
def test_nick(nick):
    lines = io.StringIO("okt 09 19:54:29 *	%s is now known as udo" % nick)
    reader = HexChatLogReader("", 0, 0, "Skanker")
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.nick
    assert quote.author == nick
    assert quote.message == "udo"


def test_you_nick():
    lines = io.StringIO("okt 09 19:54:29 *	You are now known as udo")
    reader = HexChatLogReader("", 0, "Duo")
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.nick
    assert quote.author == "Duo"
    assert quote.message == "udo"


def test_join():
    lines = io.StringIO("sep 20 18:11:08 *	WASD (~wasd@foo.bar) has joined #chan")
    reader = HexChatLogReader("", 0, "")
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.join
    assert quote.author == "WASD"
    assert quote.message == ""


@pytest.mark.parametrize(
    "raw, author, message",
    [
        ("sep 03 00:21:41 *	Ivan (Ivan@foo.bar) has left #chan", "Ivan", ""),
        ('aug 28 13:14:55 *	lod (Seth@foo.bar) has left #chan ("bye")', "lod", "bye"),
    ],
)
def test_leave(raw, author, message):
    lines = io.StringIO(raw)
    reader = HexChatLogReader("", 0, "")
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.leave
    assert quote.author == author
    assert quote.message == message


@pytest.mark.parametrize(
    "raw, author, message",
    [
        (
            "sep 03 00:21:41 *	Ivan has quit (Ping timeout: 121 seconds)",
            "Ivan",
            "Ping timeout: 121 seconds",
        ),
        ("aug 28 13:14:55 *	lod has quit (Quit: bye)", "lod", "Quit: bye"),
    ],
)
def test_quit(raw, author, message):
    lines = io.StringIO(raw)
    reader = HexChatLogReader("", 0, "")
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.leave
    assert quote.author == author
    assert quote.message == message


@pytest.mark.parametrize(
    "raw, author, message",
    [("aug 25 11:59:43 <~garamond>	do care", "~garamond", "do care")],
)
def test_message(raw, author, message):
    lines = io.StringIO(raw)
    reader = HexChatLogReader("", 0, "")
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.message
    assert quote.author == author
    assert quote.message == message


@pytest.mark.parametrize(
    "raw, month, day, hour, minute, second",
    [
        ("aug 25 11:59:43 <~a>	hi", 8, 25, 11, 59, 43),
        ("okt 04 19:03:25 <~a>	hi", 10, 4, 19, 3, 25),
    ],
)
def test_timestamp(raw, month, day, hour, minute, second):
    prefix = "**** BEGIN LOGGING AT Thu Jun 20 16:09:14 2012"
    lines = io.StringIO("%s\n%s" % (prefix, raw))
    reader = HexChatLogReader("", 0, "")
    quote = next(reader.read(lines))
    assert quote.timestamp.year == 2012
    assert quote.timestamp.month == month
    assert quote.timestamp.day == day
    assert quote.timestamp.hour == hour
    assert quote.timestamp.minute == minute
    assert quote.timestamp.second == second


def test_timestamp_across_newyears():
    lines = io.StringIO(
        "**** BEGIN LOGGING AT Thu dec 31 00:00:00 2012\n"
        "dec 31 00:00:00 <nick>	twelve\n"
        "jan 01 00:00:00 <nick>	thirteen\n"
        "jan 02 00:00:00 <nick>	thirteen2\n"
        "jan 01 00:00:00 <nick>	fourteen"
    )
    reader = HexChatLogReader("", 0, "")
    (twelve, thirteen, thirteen2, fourteen) = reader.read(lines)

    assert twelve.timestamp.year == 2012
    assert thirteen.timestamp.year == 2013
    assert thirteen2.timestamp.year == 2013
    assert fourteen.timestamp.year == 2014


@pytest.mark.parametrize(
    "offset_hours, expected_utc_hour", [(0, 20), (1, 19), (11, 9), (-1, 21), (-11, 7)]
)
def test_utc_offset(offset_hours, expected_utc_hour):
    lines = io.StringIO("aug 25 20:56:43 <~garamond>	do care")
    reader = HexChatLogReader("", offset_hours, "")
    quote = next(reader.read(lines))
    assert quote.timestamp.hour == expected_utc_hour
