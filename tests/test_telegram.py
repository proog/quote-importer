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
                "from": "~garamond",
                "text": "do care",
            },
            "~garamond",
            "do care",
        )
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
                "from": "Josh Waugh",
                "file": "video_files/video_57@25-01-2021_03-12-32.mp4",
                "media_type": "video_file",
                "text": "this one is 4 U Cass",
            },
            "Josh Waugh",
            "this one is 4 U Cass",
            "video_57@25-01-2021_03-12-32.mp4",
        )
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
