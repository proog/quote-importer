import io
from quoteimporter import shift
from quoteimporter.readers.irssi import IrssiLogReader


def test_shift():
    lines = io.StringIO(
        "20:56 <&Cassie> what the fuck\n"
        + "20:56 -!- Duo is now known as udo\n"
        + "20:58 <&ashin> also swear words"
    )
    reader = IrssiLogReader("", 0, "")
    quotes = list(reader.read(lines))

    assert quotes[0].sequence_id == 1
    assert quotes[1].sequence_id == 2
    assert quotes[2].sequence_id == 3

    max_existing_sequence_id = 122
    shift(quotes, max_existing_sequence_id)

    assert quotes[0].sequence_id == 123
    assert quotes[1].sequence_id == 124
    assert quotes[2].sequence_id == 125
