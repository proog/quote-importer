"""Quote models"""


class Quote:
    """A quote"""

    def __init__(
        self,
        channel,
        sequence_id,
        author,
        message,
        timestamp,
        quote_type,
        source,
        raw,
        attachment=None,
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

    def __init__(self, name, content):
        self.name = name
        self.content = content
