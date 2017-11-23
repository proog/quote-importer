import io
import pytest
from readers.whatsapp import WhatsAppLogReader, DateOrder
from models import QuoteType

@pytest.mark.parametrize('day, expected', [('5', 5), ('05', 5), ('31', 31)])
def test_dayofmonth_format(day, expected):
    lines = io.StringIO('%s/05/2017, 20:56:32 - Cassie: what the fuck' % day)
    reader = WhatsAppLogReader('', 0, 0, DateOrder.standard, '')
    quote = next(reader.read(lines))
    assert quote.timestamp.day == expected

@pytest.mark.parametrize('month, expected', [('5', 5), ('05', 5), ('12', 12)])
def test_month_format(month, expected):
    lines = io.StringIO('31/%s/2017, 20:56:32 - Cassie: what the fuck' % month)
    reader = WhatsAppLogReader('', 0, 0, DateOrder.standard, '')
    quote = next(reader.read(lines))
    assert quote.timestamp.month == expected

@pytest.mark.parametrize('year, expected', [('7', 2007), ('07', 2007), ('2007', 2007), ('3007', 3007)])
def test_year_format(year, expected):
    lines = io.StringIO('31/05/%s, 20:56:32 - Cassie: what the fuck' % year)
    reader = WhatsAppLogReader('', 0, 0, DateOrder.standard, '')
    quote = next(reader.read(lines))
    assert quote.timestamp.year == expected

@pytest.mark.parametrize('order, first, second', [
    (DateOrder.standard, 5, 10),
    (DateOrder.american, 10, 5)
])
def test_date_order(order, first, second):
    lines = io.StringIO('%s/%s/2017, 20:56:32 - Cassie: what the fuck' % (first, second))
    reader = WhatsAppLogReader('', 0, 0, order, '')
    quote = next(reader.read(lines))

    assert quote.timestamp.day == 5
    assert quote.timestamp.month == 10

@pytest.mark.parametrize('separator', [':', '.'])
def test_time_separator(separator):
    lines = io.StringIO('31/05/2017, 20{0}56{0}32 - Cassie: what the fuck'.format(separator))
    reader = WhatsAppLogReader('', 0, 0, DateOrder.standard, '')
    quote = next(reader.read(lines))

    assert quote.timestamp.hour == 20
    assert quote.timestamp.minute == 56
    assert quote.timestamp.second == 32

@pytest.mark.parametrize('offset_hours, expected_utc_hour', [
    (0, 20),
    (1, 19),
    (11, 9),
    (-1, 21),
    (-11, 7)
])
def test_utc_offset(offset_hours, expected_utc_hour):
    lines = io.StringIO('31/05/2017, 20:56:32 - Cassie: what the fuck')
    reader = WhatsAppLogReader('', 0, offset_hours, DateOrder.standard, '')
    quote = next(reader.read(lines))
    assert quote.timestamp.hour == expected_utc_hour

@pytest.mark.parametrize('separator', [': ', ' - '])
def test_time_author_separator(separator):
    lines = io.StringIO('31/05/2017, 20:56:32%sCassie: what the fuck' % separator)
    reader = WhatsAppLogReader('', 0, 0, DateOrder.standard, '')
    quote = next(reader.read(lines))

    assert quote.timestamp.hour == 20
    assert quote.timestamp.minute == 56
    assert quote.timestamp.second == 32
    assert quote.author == 'Cassie'

@pytest.mark.parametrize('message', [
    'what the fuck',
    'what\n the fuck',
    'what\r\n the fuck',
    'what\r\n the\n fuck'
])
def test_message(message):
    lines = io.StringIO('31/05/2017, 20:56:32 - Cassie: %s' % message)
    reader = WhatsAppLogReader('', 0, 0, DateOrder.standard, '')
    quote = next(reader.read(lines))
    assert quote.quote_type == QuoteType.message
    assert quote.message == message.replace('\r\n', '\n')

@pytest.mark.parametrize('message', [
    'what the fuck',
    'what\n the fuck',
    'what\r\n the fuck',
    'what\r\n the\n fuck'
])
def test_message_split(message):
    lines = io.StringIO(
        '31/05/2017, 20:56:32 - Cassie: %s\n' % message +
        '01/06/2017, 13:24:01 - Matt: also swear words')
    reader = WhatsAppLogReader('', 0, 0, DateOrder.standard, '')
    quotes = list(reader.read(lines))

    assert len(quotes) == 2
    assert quotes[0].message == message.replace('\r\n', '\n')
    assert quotes[1].timestamp.day == 1
    assert quotes[1].timestamp.month == 6
    assert quotes[1].timestamp.year == 2017

@pytest.mark.parametrize('message', [
    'should be ok',
    'should: be ok',
    'should be :ok',
    'should: : be :ok'
])
def test_message_with_colons(message):
    lines = io.StringIO('31/05/2017, 20:56:32 - Cassie: %s' % message)
    reader = WhatsAppLogReader('', 0, 0, DateOrder.standard, '')
    quote = next(reader.read(lines))
    assert quote.message == message

@pytest.mark.parametrize('you', ['You', 'you'])
def test_you(you):
    lines = io.StringIO('31/05/2017, 20:56:32 - %s changed the subject from "a" to "b"' % you)
    reader = WhatsAppLogReader('', 0, 0, DateOrder.standard, 'Cassie')
    quote = next(reader.read(lines))
    assert quote.author == 'Cassie'

def test_skip():
    lines = io.StringIO('31/05/2017, 20:56:32 - Cassie: what the fuck\n' +
                        '01/06/2017, 13:24:01 - Matt: also swear words\n' +
                        'and another line\n' +
                        '01/06/2017, 13:24:01 - Matt: something else')
    reader = WhatsAppLogReader('', 0, 0, DateOrder.standard, '')
    quotes = list(reader.read(lines, 3))
    assert len(quotes) == 1
    assert quotes[0].message == 'something else'
