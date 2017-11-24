'''Read and write quotes to the database'''
import mysql.connector

class MySqlDb:
    '''Wrap MySQL database access'''

    def __init__(self, *args, **kwargs):
        self.cnx = mysql.connector.connect(*args, **kwargs)

        # force utf8mb4 like this because the charset argument for connect() doesn't work
        cursor = self.cnx.cursor()
        cursor.execute('SET NAMES utf8mb4')
        cursor.close()

    def max_sequence_id(self, channel):
        '''Gets the largest sequence id with the given channel, or 0'''
        sql = 'SELECT MAX(sequence_id) FROM quotes WHERE channel = %s'
        cursor = self.cnx.cursor()
        cursor.execute(sql, (channel, ))
        (seq_id,) = cursor.fetchone()
        cursor.close()
        return seq_id if seq_id is not None else 0

    def insert_all(self, quotes):
        '''Insert all given quotes in chunks'''
        sql = '''INSERT INTO quotes
            (author, channel, message, sequence_id, source, timestamp, type, raw)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'''
        cursor = self.cnx.cursor()
        chunked_quotes = chunk(quotes, 10000)
        count = 0

        for q_chunk in chunked_quotes:
            data = [(x.author, x.channel, x.message, x.sequence_id,
                     x.source, x.timestamp, x.quote_type, x.raw) for x in q_chunk]
            cursor.executemany(sql, data)
            count += len(q_chunk)
            print('Inserted %i' % count)

        self.cnx.commit()
        cursor.close()

    def initialize(self):
        '''Create quotes table if it doesn't already exist'''
        sql = '''
            CREATE TABLE IF NOT EXISTS `quotes` (
                `id` int(11) NOT NULL AUTO_INCREMENT,
                `channel` varchar(127) NOT NULL,
                `sequence_id` int(11) NOT NULL,
                `author` longtext DEFAULT NULL,
                `message` longtext DEFAULT NULL,
                `timestamp` datetime(6) NOT NULL,
                `source` longtext DEFAULT NULL,
                `type` varchar(127) NOT NULL,
                `raw` longtext DEFAULT NULL,
                PRIMARY KEY (`id`),
                UNIQUE KEY `IX_quotes_channel_sequence_id` (`channel`,`sequence_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4'''
        cursor = self.cnx.cursor()
        cursor.execute(sql)
        self.cnx.commit()
        cursor.close()

    def close(self):
        '''Close the database connection'''
        self.cnx.close()

def chunk(items, chunk_size):
    '''Split items into n chunks'''
    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]
