'''Read and write quotes to a JSON file'''
import json
import os

class JsonFile:
    '''Wrap export to a JSON file'''

    def __init__(self, filename):
        self.filename = filename

    def max_sequence_id(self, channel):
        '''Gets the largest sequence id with the given channel, or 0'''
        file = open(self.filename)
        json_quotes = json.load(file)
        file.close()
        max_id = 0

        for quote in json_quotes:
            seq_id = quote['sequence_id']

            if quote['channel'] == channel and seq_id > max_id:
                max_id = seq_id

        return max_id

    def insert_all(self, quotes):
        '''Write all given quotes to the file'''
        file = open(self.filename)
        json_quotes = json.load(file)
        file.close()

        for quote in quotes:
            json_quote = {
                'channel': quote.channel,
                'sequence_id': quote.sequence_id,
                'author': quote.author,
                'message': quote.message,
                'timestamp': quote.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'source': quote.source,
                'type': quote.quote_type,
                'raw': quote.raw
            }
            json_quotes.append(json_quote)

        file = open(self.filename, mode='w')
        json.dump(json_quotes, file)
        file.close()
        print('Inserted %i' % len(quotes))

    def initialize(self):
        '''Create an empty JSON array in the file if it is empty'''
        if os.path.exists(self.filename) and os.path.getsize(self.filename) > 0:
            return

        file = open(self.filename, mode='w')
        file.write('[]')
        file.close()

    def close(self):
        pass
