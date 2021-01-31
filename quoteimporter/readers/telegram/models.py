class TelegramOptions:
    def __init__(
        self,
        channel: str,
        source: str = "telegram",
        export_dir: str = None,
    ):
        self.channel = channel
        self.source = source
        self.export_dir = export_dir
