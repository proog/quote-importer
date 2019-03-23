"""Read and write quotes to the database"""
import psycopg2


class PostgresDb:
    """Wrap PostgreSQL database access"""

    def __init__(self, *args, **kwargs):
        self.cnx = psycopg2.connect(*args, **kwargs)

    def max_sequence_id(self, channel):
        """Gets the largest sequence id with the given channel, or 0"""
        sql = "SELECT MAX(sequence_id) FROM quotes WHERE channel = %s"
        cursor = self.cnx.cursor()
        cursor.execute(sql, (channel,))
        (seq_id,) = cursor.fetchone()
        cursor.close()
        return seq_id if seq_id is not None else 0

    def insert_all(self, quotes):
        """Insert all given quotes in chunks"""
        sql = """INSERT INTO quotes
            (author, channel, message, sequence_id, source, timestamp, type, raw, attachment_name, attachment)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor = self.cnx.cursor()
        chunked_quotes = chunk(quotes, 10000)
        count = 0

        for q_chunk in chunked_quotes:
            data = (make_row(quote) for quote in q_chunk)
            cursor.executemany(sql, data)
            count += len(q_chunk)
            print("Inserted %i" % count)

        self.cnx.commit()
        cursor.close()

    def initialize(self):
        """Create quotes table if it doesn't already exist"""
        sql = """
            CREATE TABLE IF NOT EXISTS quotes (
                id serial NOT NULL PRIMARY KEY,
                channel varchar NOT NULL,
                sequence_id int NOT NULL,
                author varchar DEFAULT NULL,
                message text DEFAULT NULL,
                timestamp timestamp NOT NULL,
                source varchar DEFAULT NULL,
                type varchar NOT NULL,
                raw text DEFAULT NULL,
                attachment_name varchar DEFAULT NULL,
                attachment bytea DEFAULT NULL,
                UNIQUE (channel,sequence_id)
            )"""
        cursor = self.cnx.cursor()
        cursor.execute(sql)
        self.cnx.commit()
        cursor.close()

    def close(self):
        """Close the database connection"""
        self.cnx.close()


def chunk(items, chunk_size):
    """Split items into n chunks"""
    for i in range(0, len(items), chunk_size):
        yield items[i : i + chunk_size]


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
