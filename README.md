# quote-importer

Parses chat logs into structured data.

## Supported log formats

- irssi
- WhatsApp (iOS and Android exports)
- [nda](https://github.com/proog/nda)

### WhatsApp media

WhatsApp media attachments (like images) are supported. Export your chat with the "attach media" option and quote-importer will attempt to read attachments from the same folder as the log file itself.

## Supported storage systems

- SQLite
- MySQL
- PostgreSQL
- MongoDB (without attachments due to document size constraints)
- JSON file (slow)

## Usage

First install Python 3 and [pipenv](https://docs.pipenv.org/), then run

    pipenv install --dev --three
    pipenv shell

then in the virtualenv shell, run something like

    python -m quoteimporter [OPTIONS] LOG_TYPE CHANNEL_NAME LOG_FILENAME

### Arguments

- `LOG_TYPE` Input format; can be `irssi`, `whatsapp` or `nda`
- `CHANNEL_NAME` Channel or group name, e.g. `#mychannel`
- `LOG_FILENAME` Path to the log file to read.

### Options

- `--writer {sqlite, mysql, json, mongo, none}` (default: `none`, i.e. a no-op/dry run) Output format; most credentials currently hardcoded in `app.py`
- `--utc-offset [number]` (default: `0`) UTC offset in hours to assume when reading logs
- `--you [string]` (default: `You`) irssi and WhatsApp refer to the author of the logs by "you", which is not helpful; this option substitutes "you" when reading logs
- `--dates {standard,american}` (default: `standard`) Date format to assume when reading WhatsApp logs; WhatsApp uses either day/month/year (standard) or month/day/year (American) for its dates, depending on device
- `--skip-lines [number]` (default: `0`) Skip processing lines of the file
- `--no-attachments` (default: `false`, i.e. read attachments from the log file folder) Don't read WhatsApp media attachments; the messages will still be read
- `--database [string]` (default: `quotes`) Database name if using the MySQL, PostgreSQL or MongoDB writers
- `--mysql-user [string]` (default: `root`) User if using the MySQL writer
- `--mysql-password [string]` (default: no password) Password if using the MySQL writer
- `--postgres-user [string]` (default: `postgres`) User if using the PostgreSQL writer
- `--postgres-password [string]` (default: no password) Password if using the PostgreSQL writer

### Testing

Run `pytest` in the virtualenv.
