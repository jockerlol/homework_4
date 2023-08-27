import aiohttp
import asyncio
import logging
import sys
from datetime import datetime
from calendar import monthrange

STR_DATE_TODAY = datetime.now().strftime('%d.%m.%Y')
MAX_DAYS = 10
URL_WITHOUT_DATE = "https://api.privatbank.ua/p24api/exchange_rates?json&date="
CURRENCIES = ['USD', 'EUR']


def make_date_str_from_args(arg: int) -> str:
    if arg == 0:
        return STR_DATE_TODAY
    day_today = datetime.now().day
    if day_today <= arg:
        year_today = datetime.now().year
        month_today = datetime.now().month
        previous_month = month_today - 1
        days_in_previous_month = monthrange(year_today, previous_month)[1]
        day_for_new_date = (day_today - arg) + days_in_previous_month
        new_date = datetime(year=datetime.now().year,
                            month=previous_month,
                            day=day_for_new_date).strftime('%d.%m.%Y')
        return new_date
    else:
        day_for_new_date = day_today - arg
        new_date = datetime(year=datetime.now().year,
                            month=datetime.now().month,
                            day=day_for_new_date).strftime('%d.%m.%Y')
        return new_date


async def request(url):
    async with aiohttp.ClientSession() as sesion:
        try:
            async with sesion.get(url) as response:
                if response.status == 200:
                    res = await response.json()
                    return res
                logging.error(f"Error status {response.status} for {url}")
                return None
        except aiohttp.ClientConnectionError() as err:
            logging.error(f"Connect error {str(err)}")
            return None


async def get_exchange(date=datetime.now().strftime('%d.%m.%Y')):
    url = URL_WITHOUT_DATE + date
    response_dict = await request(url)
    if response_dict:
        list_exchanges = response_dict.get('exchangeRate')
        currencies_exchange = {}
        for exchange in list_exchanges:
            if exchange.get('currency') in CURRENCIES:
                currency = exchange
                currencies_exchange[str(currency.get('currency'))] = {'sale': currency.get('saleRate'),
                                                                      'purchase': currency.get('purchaseRate')}
        result = {response_dict.get('date'): currencies_exchange}

        return result

    return "Faild to retrieve data"


async def main():
    result = []
    is_args = False
    try:
        args = int(sys.argv[1])
        is_args = True
    except IndexError:
        pass
    except ValueError:
        logging.error(f"Argument '{sys.argv[1]}' is not a number")
    if is_args:
        if args <= MAX_DAYS:
            for arg in range(args):
                date = make_date_str_from_args(arg=arg)
                el = asyncio.create_task(get_exchange(date=date))
                await el
                result.append(el.result())
            return result
        else:
            logging.error(f"Max argument is 10. Yours - '{sys.argv[1]}'")
    task = asyncio.create_task(get_exchange())
    await task
    result.append(task.result())
    return result


if __name__ == '__main__':
    result = asyncio.run(main())
    print(result)