"""Transform logs into structured data"""
import os.path

from .models import QuoteType
from .readers.hexchat import HexChatLogReader
from .readers.irssi import IrssiLogReader
from .readers.nda import NdaLogReader
from .readers.telegram.models import TelegramOptions
from .readers.telegram.reader import TelegramLogReader
from .readers.whatsapp.models import DateOrder, WhatsAppOptions
from .readers.whatsapp.reader import WhatsAppLogReader
from .writers.dryrun import DryRun
from .writers.jsonfile import JsonFile
from .writers.mongodb import MongoDb
from .writers.mysqldb import MySqlDb
from .writers.postgresdb import PostgresDb
from .writers.sqlitedb import SqliteDb


def read_quotes(args):
    """Creates an appropriate reader using the command line args"""
    source = os.path.basename(args.filename)

    if args.type == "irssi":
        reader = IrssiLogReader(args.channel, args.utc_offset, args.you, source)
    elif args.type == "whatsapp":
        date_order = (
            DateOrder.american if args.dates == "american" else DateOrder.standard
        )
        attachment_dir = None if args.no_attachments else os.path.dirname(args.filename)
        options = WhatsAppOptions(
            args.channel, args.utc_offset, date_order, args.you, source, attachment_dir
        )
        reader = WhatsAppLogReader(options)
    elif args.type == "hexchat":
        reader = HexChatLogReader(args.channel, args.utc_offset, args.you, source)
    elif args.type == "nda":
        reader = NdaLogReader(args.channel, args.you, source)
    elif args.type == "telegram":
        options = TelegramOptions(args.channel, source, os.path.dirname(args.filename))
        reader = TelegramLogReader(options)
    else:
        raise Exception("Invalid log type")

    with open(args.filename, encoding="utf-8", errors="replace") as stream:
        return list(reader.read(stream, args.skip_lines))


def write_quotes(args, quotes):
    """Initializes a writer and writes the quotes to it"""
    if args.writer == "mysql":
        writer = MySqlDb(
            host="127.0.0.1",
            user=args.mysql_user,
            password=args.mysql_password,
            database=args.database,
        )
    elif args.writer == "postgres":
        writer = PostgresDb(
            host="127.0.0.1",
            user=args.postgres_user,
            password=args.postgres_password,
            dbname=args.database,
        )
    elif args.writer == "json":
        writer = JsonFile("quotes.json")
    elif args.writer == "mongo":
        writer = MongoDb("localhost", 27017, args.database)
    elif args.writer == "sqlite":
        writer = SqliteDb("quotes.db")
    else:
        writer = DryRun()

    writer.initialize()

    max_existing_sequence_id = writer.max_sequence_id(args.channel)
    shift(quotes, max_existing_sequence_id)

    print("Starting at sequence id %i for %s" % (quotes[0].sequence_id, args.channel))

    writer.insert_all(quotes)
    writer.close()


def count(quotes, quote_type):
    """Counts the number of quotes of a given type"""
    return sum(1 for x in quotes if x.quote_type == quote_type)


def shift(quotes, amount):
    """Shifts the sequence id of each quote by a given amount. Sequence ids start at 1."""
    for quote in quotes:
        quote.sequence_id += amount


def print_stats(quotes):
    """Prints stats about the quotes read"""
    print("Read %i messages" % count(quotes, QuoteType.message))
    print("Read %i subject changes" % count(quotes, QuoteType.subject))
    print("Read %i joins" % count(quotes, QuoteType.join))
    print("Read %i leaves" % count(quotes, QuoteType.leave))
    print("Read %i kicks" % count(quotes, QuoteType.kick))
    print("Read %i bans" % count(quotes, QuoteType.ban))
    print("Read %i nick changes" % count(quotes, QuoteType.nick))
    print("Read %i system notices" % count(quotes, QuoteType.system))
    print("Read %i attachments" % count(quotes, QuoteType.attachment))
    print("Read %i total" % len(quotes))
