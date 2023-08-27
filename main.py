<<<<<<< HEAD
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
=======
import pathlib
import mimetypes
import socket
from threading import Thread
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from datetime import datetime
import json

CUR_DIR = pathlib.Path()
JSON_DIR = CUR_DIR.joinpath('storage/data.json')

SOCKET_HOST = socket.gethostname()
SOCKET_PORT = 5000
SOCKET_SIZE = 1024

HTTP_SERVER_IP = '0.0.0.0'
HTTP_SERVER_PORT = 3000


class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        socket_client(data)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fl:
            self.wfile.write(fl.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


def run_http(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = (HTTP_SERVER_IP, HTTP_SERVER_PORT)
    http = server_class(server_address, handler_class)
    logging.info('HTTP server has started to work')
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        logging.info('HTTP server has stoped working')
        http.server_close()


def socket_client(data):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
    client_socket.close()


def save_data(data):
    now = str(datetime.now())
    body = urllib.parse.unquote_plus(data.decode())
    try:
        data_load = {key: value for key, value in [
            el.split('=') for el in body.split('&')]}
        if pathlib.Path.exists(JSON_DIR):
            with open('storage/data.json', 'r') as fd:
                existing_data = json.load(fd)
        else:
            existing_data = {}
        print(existing_data)
        entry = {now: data_load}
        existing_data.update(entry)
        print(existing_data)
        with open('storage/data.json', 'w', encoding='utf-8') as fl:
            json.dump(existing_data, fl, ensure_ascii=False)
    except ValueError as verr:
        logging.error(f"Failed parse data {verr}")
    except OSError as oserr:
        logging.error(f"Failed to save data {oserr}")


def run_socket(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # host_port = host, port
    server_socket.bind((host, port))
    logging.info('Socket server has started to work')
    try:
        while True:
            data, server_address = server_socket.recvfrom(SOCKET_SIZE)
            save_data(data)
    except KeyboardInterrupt:
        logging.info('Socket server has stoped working')
        server_socket.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format="%(threadName)s: %(message)s")

    server_http_thread = Thread(target=run_http)
    server_http_thread.start()

    server_socket_thread = Thread(target=run_socket(
        SOCKET_HOST, SOCKET_PORT))
    server_socket_thread.start()

    server_http_thread.join()
    server_socket_thread.join()
>>>>>>> c2d6c7d94ef7dbb1cd21f35314af60e97296a8a9
