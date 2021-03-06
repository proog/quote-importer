"""Read and write quotes to the database"""
import sqlite3


class SqliteDb:
    """Wrap SQLite database access"""

    def __init__(self, *args, **kwargs):
        self.cnx = sqlite3.connect(*args, **kwargs)

    def max_sequence_id(self, channel):
        """Gets the largest sequence id with the given channel, or 0"""
        sql = "SELECT MAX(sequence_id) FROM quotes WHERE channel = ?"
        cursor = self.cnx.cursor()
        cursor.execute(sql, (channel,))
        (seq_id,) = cursor.fetchone()
        cursor.close()
        return seq_id if seq_id is not None else 0

    def insert_all(self, quotes):
        """Insert all given quotes"""
        sql = """INSERT INTO quotes
            (author, channel, message, sequence_id, source, timestamp, type, raw, attachment_name, attachment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        cursor = self.cnx.cursor()

        data = (make_row(quote) for quote in quotes)
        cursor.executemany(sql, data)
        print("Inserted %i" % len(quotes))

        self.cnx.commit()
        cursor.close()

    def initialize(self):
        """Create quotes table if it doesn't already exist"""
        sql_table = """
            CREATE TABLE IF NOT EXISTS `quotes` (
                `id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                `channel`	TEXT NOT NULL,
                `sequence_id`	INTEGER NOT NULL,
                `author`	TEXT DEFAULT NULL,
                `message`	TEXT DEFAULT NULL,
                `timestamp`	TEXT NOT NULL,
                `source`	TEXT DEFAULT NULL,
                `type`	TEXT NOT NULL,
                `raw`	TEXT DEFAULT NULL,
                `attachment_name` TEXT DEFAULT NULL,
                `attachment`  BLOB DEFAULT NULL
            )"""
        sql_index = """
            CREATE UNIQUE INDEX IF NOT EXISTS `IX_quotes_channel_sequence_id` ON `quotes` (
                `channel`,
                `sequence_id`
            )"""
        cursor = self.cnx.cursor()
        cursor.execute(sql_table)
        cursor.execute(sql_index)
        self.cnx.commit()
        cursor.close()

    def close(self):
        """Close the database connection"""
        self.cnx.close()


def make_row(quote):
    return (
        quote.author,
        quote.channel,
        quote.message,
        quote.sequence_id,
        quote.source,
        quote.timestamp,
        quote.quote_type,
        quote.raw,
        quote.attachment.name if quote.attachment is not None else None,
        quote.attachment.content if quote.attachment is not None else None,
    )
