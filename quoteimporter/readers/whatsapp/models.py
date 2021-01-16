class DateOrder:
    """Whether to use the D/M/Y or M/D/Y when parsing dates"""

    standard = "standard"
    american = "american"


class WhatsAppOptions:
    def __init__(
        self,
        channel: str,
        utc_offset: int = 0,
        date_order: str = DateOrder.standard,
        you: str = "You",
        source: str = "whatsapp",
        attachment_dir: str = None,
    ):
        self.channel = channel
        self.utc_offset = utc_offset
        self.date_order = date_order
        self.you = you
        self.source = source
        self.attachment_dir = attachment_dir
