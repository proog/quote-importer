import io
import os
import shutil

import pytest
from quoteimporter.models import QuoteType
from quoteimporter.readers.whatsapp.handlers import DateOrder
from quoteimporter.readers.whatsapp.models import WhatsAppOptions
from quoteimporter.readers.whatsapp.reader import WhatsAppLogReader


@pytest.mark.parametrize("day, expected", [("5", 5), ("05", 5), ("31", 31)])
def test_dayofmonth_format(day, expected):
    lines = io.StringIO("%s/05/2017, 20:56:32 - Cassie: what the fuck" % day)
    reader = WhatsAppLogReader(WhatsAppOptions(""))
    quote = next(reader.read(lines))
    assert quote.timestamp.day == expected


@pytest.mark.parametrize("month, expected", [("5", 5), ("05", 5), ("12", 12)])
def test_month_format(month, expected):
    lines = io.StringIO("31/%s/2017, 20:56:32 - Cassie: what the fuck" % month)
    reader = WhatsAppLogReader(WhatsAppOptions(""))
    quote = next(reader.read(lines))
    assert quote.timestamp.month == expected


@pytest.mark.parametrize(
    "year, expected", [("7", 2007), ("07", 2007), ("2007", 2007), ("3007", 3007)]
)
def test_year_format(year, expected):
    lines = io.StringIO("31/05/%s, 20:56:32 - Cassie: what the fuck" % year)
    reader = WhatsAppLogReader(WhatsAppOptions(""))
    quote = next(reader.read(lines))
    assert quote.timestamp.year == expected


@pytest.mark.parametrize(
    "order, first, second", [(DateOrder.standard, 5, 10), (DateOrder.american, 10, 5)]
)
def test_date_order(order, first, second):
    lines = io.StringIO(
        "%s/%s/2017, 20:56:32 - Cassie: what the fuck" % (first, second)
    )
    reader = WhatsAppLogReader(WhatsAppOptions("", date_order=order))
    quote = next(reader.read(lines))

    assert quote.timestamp.day == 5
    assert quote.timestamp.month == 10


@pytest.mark.parametrize("separator", [":", "."])
def test_time_separator(separator):
    lines = io.StringIO(
        "31/05/2017, 20{0}56{0}32 - Cassie: what the fuck".format(separator)
    )
    reader = WhatsAppLogReader(WhatsAppOptions(""))
    quote = next(reader.read(lines))

    assert quote.timestamp.hour == 20
    assert quote.timestamp.minute == 56
    assert quote.timestamp.second == 32


@pytest.mark.parametrize(
    "offset_hours, expected_utc_hour", [(0, 20), (1, 19), (11, 9), (-1, 21), (-11, 7)]
)
def test_utc_offset(offset_hours, expected_utc_hour):
    lines = io.StringIO("31/05/2017, 20:56:32 - Cassie: what the fuck")
    reader = WhatsAppLogReader(WhatsAppOptions("", offset_hours))
    quote = next(reader.read(lines))
    assert quote.timestamp.hour == expected_utc_hour


@pytest.mark.parametrize(
    "timestamp_str",
    ["31/05/2017, 20:56:32: ", "31/05/2017, 20:56:32 - ", "[31/05/2017, 20.56.32] "],
)
def test_time_author_separator(timestamp_str):
    lines = io.StringIO("%sCassie: what the fuck" % timestamp_str)
    reader = WhatsAppLogReader(WhatsAppOptions(""))
    quote = next(reader.read(lines))

    assert quote.timestamp.year == 2017
    assert quote.timestamp.month == 5
    assert quote.timestamp.day == 31
    assert quote.timestamp.hour == 20
    assert quote.timestamp.minute == 56
    assert quote.timestamp.second == 32
    assert quote.author == "Cassie"


@pytest.mark.parametrize(
    "message",
    ["what the fuck", "what\n the fuck", "what\r\n the fuck", "what\r\n the\n fuck"],
)
def test_message(message):
    lines = io.StringIO("31/05/2017, 20:56:32 - Cassie: %s" % message)
    reader = WhatsAppLogReader(WhatsAppOptions(""))
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.message
    assert quote.message == message.replace("\r\n", "\n")


@pytest.mark.parametrize(
    "message",
    ["what the fuck", "what\n the fuck", "what\r\n the fuck", "what\r\n the\n fuck"],
)
def test_message_split(message):
    lines = io.StringIO(
        "31/05/2017, 20:56:32 - Cassie: %s\n" % message
        + "01/06/2017, 13:24:01 - Matt: also swear words"
    )
    reader = WhatsAppLogReader(WhatsAppOptions(""))
    quotes = list(reader.read(lines))

    assert len(quotes) == 2
    assert quotes[0].message == message.replace("\r\n", "\n")
    assert quotes[1].timestamp.day == 1
    assert quotes[1].timestamp.month == 6
    assert quotes[1].timestamp.year == 2017


@pytest.mark.parametrize(
    "message", ["should be ok", "should: be ok", "should be :ok", "should: : be :ok"]
)
def test_message_with_colons(message):
    lines = io.StringIO("31/05/2017, 20:56:32 - Cassie: %s" % message)
    reader = WhatsAppLogReader(WhatsAppOptions(""))
    quote = next(reader.read(lines))
    assert quote.message == message


@pytest.mark.parametrize("you", ["You", "you"])
def test_you(you):
    lines = io.StringIO(
        '31/05/2017, 20:56:32 - %s changed the subject from "a" to "b"' % you
    )
    reader = WhatsAppLogReader(WhatsAppOptions("", you="Cassie"))
    quote = next(reader.read(lines))
    assert quote.author == "Cassie"


def test_skip():
    lines = io.StringIO(
        "31/05/2017, 20:56:32 - Cassie: what the fuck\n"
        + "01/06/2017, 13:24:01 - Matt: also swear words\n"
        + "and another line\n"
        + "01/06/2017, 13:24:01 - Matt: something else"
    )
    reader = WhatsAppLogReader(WhatsAppOptions(""))
    quotes = list(reader.read(lines, 3))
    assert len(quotes) == 1
    assert quotes[0].message == "something else"


def test_join():
    lines = io.StringIO("31/05/2017, 20:56:32 - Cassie added Matt")
    reader = WhatsAppLogReader(WhatsAppOptions(""))
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.join
    assert quote.author == "Matt"
    assert quote.message == ""


def test_leave():
    lines = io.StringIO("31/05/2017, 20:56:32 - Matt left")
    reader = WhatsAppLogReader(WhatsAppOptions(""))
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.leave
    assert quote.author == "Matt"
    assert quote.message == ""


def test_kick():
    lines = io.StringIO("31/05/2017, 20:56:32 - Cassie removed Matt")
    reader = WhatsAppLogReader(WhatsAppOptions(""))
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.kick
    assert quote.author == "Cassie"
    assert quote.message == "Matt"


def test_subject():
    lines = io.StringIO(
        '31/05/2017, 20:56:32 - Matt changed the subject from "a" to "b"'
    )
    reader = WhatsAppLogReader(WhatsAppOptions(""))
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.subject
    assert quote.author == "Matt"
    assert quote.message == "b"


def test_icon():
    lines = io.StringIO("31/05/2017, 20:56:32 - Matt changed this group's icon")
    reader = WhatsAppLogReader(WhatsAppOptions(""))
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.subject
    assert quote.author == "Matt"
    assert quote.message == "changed this group's icon"


def test_system():
    lines = io.StringIO(
        "31/05/2017, 20:56:32 - Messages you send to this group are now secured with end-to-end encryption. Tap for more info."
    )
    reader = WhatsAppLogReader(WhatsAppOptions(""))
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.system
    assert quote.author == ""
    assert (
        quote.message
        == "Messages you send to this group are now secured with end-to-end encryption. Tap for more info."
    )


@pytest.mark.parametrize("filename", ["something.jpg", "something else.mp4"])
def test_attachment(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_dir = os.path.join(current_dir, "test_files")
    os.makedirs(file_dir, exist_ok=True)
    content = bytes([0x1, 0x2, 0x3])

    with open(os.path.join(file_dir, filename), "wb") as f:
        f.write(content)

    lines = io.StringIO(
        "\u200e[26/07/2017, 15.11.24] Seth: \u200e<attached: %s>" % filename
    )
    reader = WhatsAppLogReader(WhatsAppOptions("", attachment_dir=file_dir))
    quote = next(reader.read(lines))

    shutil.rmtree(file_dir)

    assert quote.quote_type == QuoteType.attachment
    assert quote.message == "<attached: %s>" % filename
    assert quote.attachment.name == filename
    assert quote.attachment.content == content


def test_attachment_without_attachment_dir():
    lines = io.StringIO(
        "\u200e[26/07/2017, 15.11.24] Seth: \u200e<attached: some file.jpg>"
    )
    reader = WhatsAppLogReader(WhatsAppOptions("", attachment_dir=None))
    quote = next(reader.read(lines))

    assert quote.quote_type == QuoteType.attachment
    assert quote.message == "<attached: some file.jpg>"
    assert quote.attachment.name == "some file.jpg"
    assert quote.attachment.content == None


@pytest.mark.parametrize("message", ["image omitted", "video omitted"])
def test_attachment_omitted(message):
    lines = io.StringIO(f"\u200e[26/07/2017, 15.11.24] Seth: \u200e{message}")
    reader = WhatsAppLogReader(WhatsAppOptions(""))
    quote = next(reader.read(lines))

    assert quote.quote_type == QuoteType.attachment
    assert quote.message == message
    assert quote.attachment == None


@pytest.mark.parametrize(
    "message, filename",
    [
        ("Untitled document.pdf • 6 pages document omitted", "Untitled document.pdf"),
        ("Untitled • 1234 pages document omitted", "Untitled"),
        ("monkey fun.mp3 document omitted", "monkey fun.mp3"),
    ],
)
def test_named_attachment_omitted(message, filename):
    lines = io.StringIO(f"\u200e[26/07/2017, 15.11.24] Seth: \u200e{message}")
    reader = WhatsAppLogReader(WhatsAppOptions(""))
    quote = next(reader.read(lines))

    assert quote.quote_type == QuoteType.attachment
    assert quote.message == message
    assert quote.attachment.name == filename
    assert quote.attachment.content == None
