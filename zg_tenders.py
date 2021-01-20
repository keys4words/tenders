import requests, random, os, logging, time, re, sqlite3
from bs4 import BeautifulSoup
from openpyxl import Workbook
from datetime import datetime
import yagmail

from config.conf_113 import from_email, password, to_emails, bcc
from config.conf_104 import to_emails2
from config.conf_129 import to_emails3


BASE_URL = 'https://zakupki.gov.ru'
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = 'db\\zg_department.db'

FILE_WITH_INNS = os.path.join(BASE_DIR, 'inn', 'zg_113.txt')
FILE_WITH_INNS_104 = os.path.join(BASE_DIR, 'inn', 'zg_104.txt')
FILE_WITH_INNS_129 = os.path.join(BASE_DIR, 'inn', 'zg_129.txt')

# FILE_WITH_KW = os.path.join(BASE_DIR, 'keywords', 'zg_113.txt')

HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36', 'accept': '*/*'}


def create_db():
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS tenders(
            number TEXT,
            name TEXT,
            url TEXT,
            customer TEXT,
            customer_url TEXT,
            price TEXT,
            release_date TEXT,
            refreshing_date TEXT,
            ending_date TEXT
        )""")


def inDataBase(number):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute(f"SELECT * FROM tenders WHERE number=='{number}'")
        return cur.fetchone()

def save_tender(number, name, url, customer, customer_url, price, release_date, refreshing_date, ending_date):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute(f"INSERT INTO tenders (number, name, url, customer, customer_url, price, release_date, refreshing_date, ending_date) VALUES('{number}', '{name}', '{url}', '{customer}', '{customer_url}', '{price}', '{release_date}', '{refreshing_date}', '{ending_date}');")


def set_logger():
    root_logger = logging.getLogger('zg_tenders')
    handler = logging.FileHandler('logs\\zg_tenders.log', 'a', 'utf-8')
    formatter = logging.Formatter(
        '%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)


def get_inns(filename):
    inns = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            inns.append(line.strip())
        return inns


def get_html(url, params=None):
    resp = requests.get(url=url, headers=HEADERS, params=params)
    return resp


def parsing(inns):
    root_logger = logging.getLogger('zg_tenders')
    for inn in inns:
        page_num = 1
        url = f'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString={inn}&morphology=on&search-filter=%D0%94%D0%B0%D1%82%D0%B5+%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D1%8F&pageNumber={page_num}&sortDirection=false&recordsPerPage=_50&showLotsInfoHidden=false&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&currencyIdGeneral=-1'

        _html = get_html(url)
        if _html.status_code == 200:
            soup = BeautifulSoup(_html.text, 'html.parser')
            if soup.find_all(
                    'div', class_='search-registry-entry-block box-shadow-search-input'):
                elements = soup.find_all(
                    'div', class_='search-registry-entry-block box-shadow-search-input')
                for el in elements:
                    number = el.find(
                        'div', class_='registry-entry__header-mid__number').a
                    tender_url = number.get('href')
                    if 'https' not in tender_url:
                        tender_url = BASE_URL + tender_url
                    number = number.text.strip().replace('\n', '').replace('№ ', '')
                    name = el.find(text=re.compile("Объект закупки")
                                   ).parent.find_next_sibling()
                    name = name.text.strip().replace('\n', '')
                    # print(f'inn#{inn} number is {number}')
                    try:
                        customer = el.find(text=re.compile(
                            "Заказчик")).parent.find_next_sibling().a
                        if customer:
                            customer_url = customer.get('href')
                            if 'https' not in customer_url:
                                customer_url = BASE_URL + customer_url
                            customer = customer.text.strip().replace('\n', '')
                            last_customer = customer
                            last_customer_url = customer_url
                    except AttributeError:
                        try:
                            customer = last_customer
                            customer_url = last_customer_url
                        except UnboundLocalError:
                            customer = ''
                            customer_url = ''

                    price = el.find('div', class_="price-block__value")
                    price = price.text.strip().replace('\n', '').replace('\xa0', '')
                    release_date = el.find(text=re.compile(
                        "Размещено")).parent.find_next_sibling()
                    release_date = release_date.text
                    refreshing_date = el.find(text=re.compile(
                        "Обновлено")).parent.find_next_sibling()
                    refreshing_date = refreshing_date.text
                    ending_date = el.find(text=re.compile(
                        "Окончание подачи заявок")).parent.find_next_sibling()
                    ending_date = ending_date.text
                    if not inDataBase(number):
                        save_tender(
                            number=number,
                            name=name,
                            url=tender_url,
                            customer=customer,
                            customer_url=customer_url,
                            price=price,
                            release_date=release_date,
                            refreshing_date=refreshing_date,
                            ending_date=ending_date
                            )
                        res[number] = {
                            'name': name,
                            'url': tender_url,
                            'customer': customer,
                            'customer_url': customer_url,
                            'price': price,
                            'release_date': release_date,
                            'refreshing_date': refreshing_date,
                            'ending_date': ending_date
                        }
                    else:
                        pass
                root_logger.info(
                    f'Parsed {str(len(elements))} tenders for customer with INN #{inn}')
            else:
                root_logger.warning(
                    f'0 active tenders for customer with INN #{inn}')
                continue
        else:
            root_logger.warning(f'page {url} is not available')
            continue
    root_logger.info('='*36)


def save_results(res, fileprefix):
    wb = Workbook()
    ws = wb.active
    headers = ['Размещено', 'Обновлено', 'Окончание подачи заявок', 'Номер', 'Объект закупки', 'Ссылка на тендер', 'Заказчик',
               'Начальная цена' ]
    ws.append(headers)
    for tender_number, tender_info in res.items():
        ws.append([tender_info['release_date'], tender_info['refreshing_date'], tender_info['ending_date'], tender_number, tender_info['name'], tender_info['url'], tender_info['customer'],
                   tender_info['price'] ])

    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 20
    ws.column_dimensions['D'].width = 30
    ws.column_dimensions['E'].width = 100
    ws.column_dimensions['G'].width = 80
    ws.column_dimensions['H'].width = 20

    name = os.path.abspath(os.path.dirname(__file__))
    name = os.path.join(name, 'out', datetime.now().strftime("%d-%m-%Y_%H-%M"))

    results_file_name = name + fileprefix + '.xlsx'
    wb.save(results_file_name)
    root_logger = logging.getLogger('zg_tenders')
    root_logger.info(f'File {results_file_name} was successfully saved')
    return results_file_name

def sending_email(filename, subject, to_emails):
    body = "Below you find file with tenders from zakupki.gov"
    contents = [
        body,
        filename
    ]

    yagmail.register(from_email, password)
    yag = yagmail.SMTP(from_email)
    yag.send(
        to=to_emails,
        subject=subject,
        bcc=bcc,
        contents=contents,
    )
    root_logger = logging.getLogger('zg_tenders')
    root_logger.info(f'File was sended to {to_emails}, blind copy: {bcc}')


# main thread
# interation for 113
res = dict()

set_logger()
parsing(get_inns(FILE_WITH_INNS))
# print(res)
sending_email(save_results(res=res, fileprefix='_zg_113'), 'zakupki-gov by INN', to_emails=to_emails)

# iteration for 104
res = dict()
parsing(get_inns(FILE_WITH_INNS_104))
sending_email(save_results(res=res, fileprefix='_zg_104'), 'zakupki-gov by INN', to_emails=to_emails2)

# iteration for 129
res = dict()
parsing(get_inns(FILE_WITH_INNS_129))
sending_email(save_results(res=res, fileprefix='_zg_129'), 'zakupki-gov by INN', to_emails=to_emails3)

root_logger = logging.getLogger('zg_tenders')
root_logger.info('='*46)
# create_db()