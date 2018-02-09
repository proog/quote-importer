'''Transform logs into structured data'''
import argparse
import os.path
from models import QuoteType
from writers.mysqldb import MySqlDb
from writers.sqlitedb import SqliteDb
from writers.jsonfile import JsonFile
from writers.mongodb import MongoDb
from readers.irssi import IrssiLogReader
from readers.whatsapp import WhatsAppLogReader, DateOrder
from readers.nda import NdaLogReader

def main():
    '''Entry point for the application'''
    args = parse_args()
    channel = args.channel
    filename = args.filename
    skip_lines = args.skip_lines
    dry_run = args.dry_run
    source = os.path.basename(filename)

    if args.writer == 'mysql':
        writer = MySqlDb(host='127.0.0.1', user='root', database='quotes')
    elif args.writer == 'json':
        writer = JsonFile('quotes.json')
    elif args.writer == 'mongo':
        writer = MongoDb('localhost', 27017, 'quotes')
    else:
        writer = SqliteDb('quotes.db')

    writer.initialize()
    start_sequence_id = writer.max_sequence_id(channel) + 1
    reader = create_reader(args, source, start_sequence_id)

    print('Starting at sequence id %i for %s' % (start_sequence_id, channel))

    with open(filename, encoding='utf-8', errors='replace') as stream:
        quotes = list(reader.read(stream, skip_lines))

    print('Read %i messages' % count(quotes, QuoteType.message))
    print('Read %i subject changes' % count(quotes, QuoteType.subject))
    print('Read %i joins' % count(quotes, QuoteType.join))
    print('Read %i leaves' % count(quotes, QuoteType.leave))
    print('Read %i kicks' % count(quotes, QuoteType.kick))
    print('Read %i bans' % count(quotes, QuoteType.ban))
    print('Read %i nick changes' % count(quotes, QuoteType.nick))
    print('Read %i system notices' % count(quotes, QuoteType.system))
    print('Read %i total' % len(quotes))

    if not dry_run:
        writer.insert_all(quotes)
    writer.close()

def create_reader(args, source, start_sequence_id):
    '''Creates an appropriate reader using the command line args and a start sequence id'''
    log_type = args.type
    channel = args.channel
    utc_offset = args.utc_offset

    if log_type == 'irssi':
        return IrssiLogReader(channel, start_sequence_id, utc_offset, args.you, source)
    elif log_type == 'whatsapp':
        date_order = DateOrder.american if args.dates == 'american' else DateOrder.standard
        return WhatsAppLogReader(channel, start_sequence_id, utc_offset, date_order, args.you, source)
    elif log_type == 'nda':
        return NdaLogReader(channel, start_sequence_id, args.you, source)

    raise Exception('Invalid log type')

def count(quotes, quote_type):
    '''Counts the number of quotes of a given type'''
    return sum(1 for x in quotes if x.quote_type == quote_type)

def parse_args():
    '''Parse arguments from the command line'''
    parser = argparse.ArgumentParser()
    parser.add_argument('--writer', choices=['sqlite', 'mysql', 'json', 'mongo'], default='sqlite')
    parser.add_argument('--utc-offset', type=int, default=0)
    parser.add_argument('--dates', choices=['standard','american'], default='standard')
    parser.add_argument('--you', default='You')
    parser.add_argument('--skip-lines', type=int, default=0)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('type', choices=['irssi', 'whatsapp', 'nda'])
    parser.add_argument('channel')
    parser.add_argument('filename')
    return parser.parse_args()

if __name__ == '__main__':
    main()
