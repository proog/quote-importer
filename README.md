# quote-importer
Parses chat logs into structured data.

## Supported log formats

 - irssi
 - WhatsApp (iOS and Android, text only)
 - [nda](https://github.com/proog/nda)

## Supported storage systems

 - SQLite
 - MySQL
 - MongoDB
 - JSON file (slow)

## Usage
First install Python 3 and [pipenv](https://docs.pipenv.org/), then run

    pipenv install --dev --three
    pipenv shell

then in the virtualenv shell, run something like

    python app.py [options] irssi '#mychannel' irssi.log

### Options

 - `--writer {sqlite, mysql, json, mongo}` (default: `sqlite`) Output format; credentials currently hardcoded in `app.py`
 - `--utc-offset [number]` (default: `0`) UTC offset in hours to assume when reading logs
 - `--you [string]` (default: `You`) irssi and WhatsApp refer to the author of the logs by "you", which is not helpful; this option substitutes "you" when reading logs
 - `--dates {standard,american}` (default: `standard`) Date format to assume when reading WhatsApp logs; WhatsApp uses either day/month/year (standard) or month/day/year (American) for its dates, depending on device
 - `--skip-lines [number]` (default: `0`) Skip processing lines of the file
 - `--dry-run` Do not persist data
 
### Testing
Run `pytest` in the virtualenv.
