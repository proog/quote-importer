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
    quotes = read_quotes(args)
    print_stats(quotes)

    if not args.dry_run and len(quotes) > 0:
        write_quotes(args, quotes)

def read_quotes(args):
    '''Creates an appropriate reader using the command line args'''
    source = os.path.basename(args.filename)

    if args.type == 'irssi':
        reader = IrssiLogReader(args.channel, args.utc_offset, args.you, source)
    elif args.type == 'whatsapp':
        date_order = DateOrder.american if args.dates == 'american' else DateOrder.standard
        reader = WhatsAppLogReader(args.channel, args.utc_offset, date_order, args.you, source)
    elif args.type == 'nda':
        reader = NdaLogReader(args.channel, args.you, source)
    else:
        raise Exception('Invalid log type')

    with open(args.filename, encoding='utf-8', errors='replace') as stream:
        return list(reader.read(stream, args.skip_lines))

def write_quotes(args, quotes):
    '''Initializes a writer and writes the quotes to it'''
    if args.writer == 'mysql':
        writer = MySqlDb(host='127.0.0.1', user='root', database='quotes')
    elif args.writer == 'json':
        writer = JsonFile('quotes.json')
    elif args.writer == 'mongo':
        writer = MongoDb('localhost', 27017, 'quotes')
    else:
        writer = SqliteDb('quotes.db')

    writer.initialize()

    max_existing_sequence_id = writer.max_sequence_id(args.channel)
    shift(quotes, max_existing_sequence_id)

    print('Starting at sequence id %i for %s' % (quotes[0].sequence_id, args.channel))

    writer.insert_all(quotes)
    writer.close()

def count(quotes, quote_type):
    '''Counts the number of quotes of a given type'''
    return sum(1 for x in quotes if x.quote_type == quote_type)

def shift(quotes, amount):
    '''Shifts the sequence id of each quote by a given amount. Sequence ids start at 1.'''
    for quote in quotes:
        quote.sequence_id += amount

def print_stats(quotes):
    '''Prints stats about the quotes read'''
    print('Read %i messages' % count(quotes, QuoteType.message))
    print('Read %i subject changes' % count(quotes, QuoteType.subject))
    print('Read %i joins' % count(quotes, QuoteType.join))
    print('Read %i leaves' % count(quotes, QuoteType.leave))
    print('Read %i kicks' % count(quotes, QuoteType.kick))
    print('Read %i bans' % count(quotes, QuoteType.ban))
    print('Read %i nick changes' % count(quotes, QuoteType.nick))
    print('Read %i system notices' % count(quotes, QuoteType.system))
    print('Read %i total' % len(quotes))

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
