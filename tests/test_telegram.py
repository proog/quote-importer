import io
import json
import os
import shutil

import pytest
from quoteimporter.models import QuoteType
from quoteimporter.readers.telegram.models import TelegramOptions
from quoteimporter.readers.telegram.reader import TelegramLogReader


def format_json(messages):
    return io.StringIO(
        json.dumps({"messages": messages if isinstance(messages, list) else [messages]})
    )


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
        (
            {
                "type": "message",
                "date": "2021-01-25T03:12:32",
                "from": "Test Testy",
                "file": "files/audio.mp3",
                "media_type": "audio_file",
                "text": "this one is 4 U Cass",
            },
            "Test Testy",
            "this one is 4 U Cass",
            "audio.mp3",
        ),
        (
            {
                "type": "message",
                "date": "2021-01-25T03:12:32",
                "from": "Test Testy",
                "file": "voice_messages/voice.ogg",
                "media_type": "voice_message",
                "text": "this one is 4 U Cass",
            },
            "Test Testy",
            "this one is 4 U Cass",
            "voice.ogg",
        ),
    ],
)
def test_attachment(raw, author, message, filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    export_dir = os.path.join(current_dir, "test_files")
    file_dir = os.path.join(export_dir, os.path.dirname(raw["file"]))
    content = bytes([0x1, 0x2, 0x3])

    os.makedirs(file_dir, exist_ok=True)
    with open(os.path.join(file_dir, filename), "wb") as f:
        f.write(content)

    lines = format_json(raw)
    reader = TelegramLogReader(TelegramOptions("", export_dir=export_dir))
    quote = next(reader.read(lines))

    shutil.rmtree(export_dir)

    assert quote.quote_type == QuoteType.attachment
    assert quote.author == author
    assert quote.message == message
    assert quote.attachment.name == filename
    assert quote.attachment.content == content


def test_join():
    lines = format_json(
        {
            "type": "service",
            "date": "2021-01-08T07:10:07",
            "action": "join_group_by_link",
            "actor": "Test Testy",
        }
    )
    reader = TelegramLogReader(TelegramOptions(""))
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.join
    assert quote.author == "Test Testy"
    assert quote.message == "join_group_by_link"


@pytest.mark.parametrize(
    "raws, author, message",
    [
        (
            [
                {
                    "id": 1234,
                    "type": "message",
                    "date": "2021-01-08T07:10:07",
                    "from": "Pinned Message Author",
                    "text": "pinned message content",
                },
                {
                    "id": 1235,
                    "type": "service",
                    "date": "2021-01-08T07:10:07",
                    "action": "pin_message",
                    "actor": "Pinned Message Pinner",
                    "message_id": 1234,
                },
            ],
            "Pinned Message Pinner",
            "Pinned Message Author: pinned message content",
        ),
        (
            [
                {
                    "id": 1235,
                    "type": "service",
                    "date": "2021-01-08T07:10:07",
                    "action": "pin_message",
                    "actor": "Pinned Message Pinner",
                    "message_id": 1234,
                },
            ],
            "Pinned Message Pinner",
            "",
        ),
    ],
)
def test_pin_message(raws, author, message):
    lines = format_json(raws)
    reader = TelegramLogReader(TelegramOptions(""))
    quote = list(reader.read(lines))[-1]
    assert quote.quote_type == QuoteType.subject
    assert quote.author == author
    assert quote.message == message


def test_poll():
    raw = {
        "type": "message",
        "date": "2021-01-08T08:31:12",
        "from": "Test Testy",
        "poll": {
            "question": "is this cool",
            "closed": False,
            "total_voters": 3,
            "answers": [
                {"text": "yes", "voters": 0, "chosen": False},
                {"text": "yes?", "voters": 0, "chosen": False},
                {"text": "yes??", "voters": 0, "chosen": False},
                {"text": "fuck the dodgers!!!", "voters": 0, "chosen": False},
            ],
        },
        "text": "",
    }
    lines = format_json(raw)
    reader = TelegramLogReader(TelegramOptions(""))
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.message
    assert quote.author == "Test Testy"
    assert quote.message == json.dumps(raw["poll"])


def test_invite():
    lines = format_json(
        {
            "type": "service",
            "date": "2021-01-08T07:45:26",
            "actor": "Test Testy",
            "action": "invite_members",
            "members": ["Someone else", "Someone else 2"],
        }
    )
    reader = TelegramLogReader(TelegramOptions(""))
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.system
    assert quote.author == "Test Testy"
    assert quote.message == "Invited Someone else, Someone else 2"


@pytest.mark.parametrize(
    "action",
    ["edit_group_title", "migrate_from_group"],
)
def test_subject(action):
    lines = format_json(
        {
            "type": "service",
            "date": "2021-01-08T07:45:26",
            "actor": "Test Testy",
            "action": action,
            "title": "New title",
        }
    )
    reader = TelegramLogReader(TelegramOptions(""))
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.subject
    assert quote.author == "Test Testy"
    assert quote.message == "New title"
