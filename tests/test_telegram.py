import io
import json

import pytest
from quoteimporter.models import QuoteType
from quoteimporter.readers.telegram.models import TelegramOptions
from quoteimporter.readers.telegram.reader import TelegramLogReader


def format_json(message: dict):
    return io.StringIO(json.dumps({"messages": [message]}))


@pytest.mark.parametrize(
    "raw, author, message",
    [
        (
            {
                "type": "message",
                "date": "2021-01-08T07:10:07",
                "from": "Test Testy",
                "text": "do care",
            },
            "Test Testy",
            "do care",
        ),
        (
            {
                "type": "message",
                "date": "2021-01-08T07:10:07",
                "from": "Test Testy",
                "text": [
                    "before text ",
                    {"type": "link", "text": "https://example.com"},
                    " between text ",
                    {"type": "mention", "text": "@someone"},
                    " \n\n",
                    {"type": "link", "text": "https://example.com"},
                ],
            },
            "Test Testy",
            "before text https://example.com between text @someone \n\nhttps://example.com",
        ),
    ],
)
def test_message(raw, author, message):
    lines = format_json(raw)
    reader = TelegramLogReader(TelegramOptions(""))
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.message
    assert quote.author == author
    assert quote.message == message


@pytest.mark.parametrize(
    "raw, author, message, filename",
    [
        (
            {
                "type": "message",
                "date": "2021-01-25T03:12:32",
                "from": "Test Testy",
                "file": "video_files/video_57@25-01-2021_03-12-32.mp4",
                "media_type": "video_file",
                "text": "this one is 4 U Cass",
            },
            "Test Testy",
            "this one is 4 U Cass",
            "video_57@25-01-2021_03-12-32.mp4",
        ),
        (
            {
                "type": "message",
                "date": "2021-01-25T03:12:32",
                "from": "Test Testy",
                "file": "stickers/AnimatedSticker (6).tgs",
                "media_type": "sticker",
                "sticker_emoji": "❤️",
                "text": "this one is 4 U Cass",
            },
            "Test Testy",
            "❤️",
            "AnimatedSticker (6).tgs",
        ),
        (
            {
                "type": "message",
                "date": "2021-01-25T03:12:32",
                "from": "Test Testy",
                "file": "video_files/RoadRovers.gif.mp4",
                "media_type": "animation",
                "text": "",
            },
            "Test Testy",
            "",
            "RoadRovers.gif.mp4",
        ),
    ],
)
def test_attachment(raw, author, message, filename):
    lines = format_json(raw)
    reader = TelegramLogReader(TelegramOptions(""))
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.attachment
    assert quote.author == author
    assert quote.message == message
    assert quote.attachment.name == filename
