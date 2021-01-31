"""Quote models"""


from datetime import datetime


class QuoteType:
    """The type of a quote"""

    message = "message"
    subject = "subject"
    join = "join"
    leave = "leave"
    kick = "kick"
    ban = "ban"
    nick = "nick"
    system = "system"
    attachment = "attachment"


class Attachment:
    """A binary blob attached to a quote"""

    def __init__(self, name: str, content: bytes):
        self.name = name
        self.content = content


class Quote:
    """A quote"""

    def __init__(
        self,
        channel: str,
        sequence_id: int,
        author: str,
        message: str,
        timestamp: datetime,
        quote_type: QuoteType,
        source: str,
        raw: str,
        attachment: Attachment = None,
    ):
        self.channel = channel
        self.sequence_id = sequence_id
        self.author = author
        self.message = message
        self.timestamp = timestamp
        self.quote_type = quote_type
        self.source = source
        self.raw = raw
        self.attachment = attachment
