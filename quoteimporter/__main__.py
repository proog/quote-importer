import argparse
from . import print_stats, read_quotes, write_quotes


def parse_args():
    """Parse arguments from the command line"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--writer",
        choices=["sqlite", "mysql", "json", "mongo", "postgres", "none"],
        default="none",
    )
    parser.add_argument("--utc-offset", type=int, default=0)
    parser.add_argument("--dates", choices=["standard", "american"], default="standard")
    parser.add_argument("--you", default="You")
    parser.add_argument("--skip-lines", type=int, default=0)
    parser.add_argument("--no-attachments", action="store_true")
    parser.add_argument("--database", default="quotes")
    parser.add_argument("--mysql-user", default="root")
    parser.add_argument("--mysql-password")
    parser.add_argument("--postgres-user", default="postgres")
    parser.add_argument("--postgres-password")
    parser.add_argument("type", choices=["irssi", "whatsapp", "hexchat", "nda"])
    parser.add_argument("channel")
    parser.add_argument("filename")
    return parser.parse_args()


args = parse_args()
quotes = read_quotes(args)
print_stats(quotes)

if len(quotes) > 0:
    write_quotes(args, quotes)
