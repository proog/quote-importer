"""Read and write quotes to the database"""
import pymongo


class MongoDb:
    """Wrap MongoDB database access"""

    def __init__(self, host, port, database):
        self.client = pymongo.MongoClient(host, port)
        self.quotes = self.client[database]["quotes"]

    def max_sequence_id(self, channel):
        """Gets the largest sequence id with the given channel, or 0"""
        aggregation = self.quotes.aggregate(
            [
                {"$match": {"channel": channel}},
                {"$group": {"_id": None, "max_sequence_id": {"$max": "$sequence_id"}}},
            ]
        )

        for result in aggregation:
            return result["max_sequence_id"]
        return 0

    def insert_all(self, quotes):
        """Insert all given quotes in chunks"""
        chunked_quotes = chunk(quotes, 10000)
        count = 0

        for q_chunk in chunked_quotes:
            data = (
                {
                    "channel": x.channel,
                    "sequence_id": x.sequence_id,
                    "author": x.author,
                    "message": x.message,
                    "timestamp": x.timestamp,
                    "source": x.source,
                    "quote_type": x.quote_type,
                    "raw": x.raw,
                }
                for x in q_chunk
            )
            self.quotes.insert_many(data)
            count += len(q_chunk)
            print("Inserted %i" % count)

    def initialize(self):
        """Create quotes collection if it doesn't already exist"""
        self.quotes.create_index(
            [("channel", pymongo.ASCENDING), ("sequence_id", pymongo.ASCENDING)],
            unique=True,
        )

    def close(self):
        """Close the database connection"""
        self.client.close()


def chunk(items, chunk_size):
    """Split items into n chunks"""
    for i in range(0, len(items), chunk_size):
        yield items[i : i + chunk_size]
