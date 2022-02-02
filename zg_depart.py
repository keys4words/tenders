import requests, random, os, logging, time, re, sqlite3
from dateutil import relativedelta as dr
from bs4 import BeautifulSoup
from openpyxl import Workbook
from datetime import datetime
import yagmail
import pprint

from config.conf_113 import from_email, password, to_emails, bcc
from config.conf_104 import to_emails2
from config.conf_129 import to_emails3


BASE_URL = 'https://zakupki.gov.ru'
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'db', 'zg_department.db')

FILE_WITH_INNS = os.path.join(BASE_DIR, 'inn', 'zg_113.txt')
FILE_WITH_INNS_104 = os.path.join(BASE_DIR, 'inn', 'zg_104.txt')
FILE_WITH_INNS_129 = os.path.join(BASE_DIR, 'inn', 'zg_129.txt')

FILE_WITH_KW_113 = os.path.join(BASE_DIR, 'keywords', 'zg_113.txt')
FILE_WITH_KW_104 = os.path.join(BASE_DIR, 'keywords', 'zg_104.txt')
FILE_WITH_KW_129 = os.path.join(BASE_DIR, 'keywords', 'zg_129.txt')

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
        cur.execute("INSERT INTO tenders (number, name, url, customer, customer_url, price, release_date, refreshing_date, ending_date) VALUES(?,?,?,?,?,?,?,?,?);", (number, name, url, customer, customer_url, price, release_date, refreshing_date, ending_date))


def set_logger():
    root_logger = logging.getLogger('zg_tenders')
    log_file = os.path.join(BASE_DIR, 'logs', 'zg_tenders.log')
    handler = logging.FileHandler(log_file, 'a', 'utf-8')
    formatter = logging.Formatter(
        '%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)


def get_inns(filename):
    inns = dict()
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            if ':' in line:
                customer = line.split(':')[0]
                customer = (customer.strip()).replace(' ', '+')
                minus_words = [el.strip() for el in (line.split(':')[1]).split(',')]
                minus_words = [el.replace(' ', '+') for el in minus_words]
                inns[customer] = minus_words
            else:
                inns[line.strip()] = []
        return inns


def get_html(url, params=None):
    resp = requests.get(url=url, headers=HEADERS, params=params)
    return resp


def is_next_page(url):
    resp = requests.get(url=url, headers=HEADERS)
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, 'html.parser')
        return soup.find('a', class_='paginator-button paginator-button-next')


def url_updater(page_num, inn, minus_words):
    page_num += 1
    if len(minus_words) == 0:
        updated_url = f'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString={inn}&morphology=on&search-filter=%D0%94%D0%B0%D1%82%D0%B5+%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D1%8F&pageNumber={page_num}&sortDirection=false&recordsPerPage=_50&showLotsInfoHidden=false&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&priceFromGeneral=50000&currencyIdGeneral=-1'
    elif 'обороны' in inn:
        filter_by_close_tender = 'placingWayList=ZA44%2CZAP44%2CZAE44&'
        excluding_words_list = '%7C'.join(minus_words)
        updated_url = f'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString={inn}&morphology=on&pageNumber={page_num}&sortDirection=false&recordsPerPage=_50&showLotsInfoHidden=false&exclTextHidden={excluding_words_list}%7C&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&priceContractAdvantages44IdNameHidden=%7B%7D&priceContractAdvantages94IdNameHidden=%7B%7D&priceFromGeneral=50000&currencyIdGeneral=-1&selectedSubjectsIdNameHidden=%7B%7D&OrderPlacementSmallBusinessSubject=on&OrderPlacementRnpData=on&OrderPlacementExecutionRequirement=on&orderPlacement94_0=0&orderPlacement94_1=0&orderPlacement94_2=0&{filter_by_close_tender}contractPriceCurrencyId=-1&budgetLevelIdNameHidden=%7B%7D&nonBudgetTypesIdNameHidden=%7B%7D'
    elif 'пенсион' in inn:
        filter_by_customer_region = 'delKladrIds=5277335%2C5277327&delKladrIdsCodes=77000000000%2C50000000000&'
        excluding_words_list = '%7C'.join(minus_words)
        updated_url = f'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString={inn}&morphology=on&pageNumber={page_num}&sortDirection=false&recordsPerPage=_50&showLotsInfoHidden=false&exclTextHidden={excluding_words_list}%7C&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&priceContractAdvantages44IdNameHidden=%7B%7D&priceContractAdvantages94IdNameHidden=%7B%7D&priceFromGeneral=50000&currencyIdGeneral=-1&selectedSubjectsIdNameHidden=%7B%7D&OrderPlacementSmallBusinessSubject=on&OrderPlacementRnpData=on&OrderPlacementExecutionRequirement=on&orderPlacement94_0=0&orderPlacement94_1=0&orderPlacement94_2=0&{filter_by_customer_region}contractPriceCurrencyId=-1&budgetLevelIdNameHidden=%7B%7D&nonBudgetTypesIdNameHidden=%7B%7D'
    else:
        excluding_words_list = '%7C'.join(minus_words)
        updated_url = f'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString={inn}&morphology=on&pageNumber={page_num}&sortDirection=false&recordsPerPage=_50&showLotsInfoHidden=false&exclTextHidden={excluding_words_list}%7C&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&priceContractAdvantages44IdNameHidden=%7B%7D&priceContractAdvantages94IdNameHidden=%7B%7D&priceFromGeneral=50000&currencyIdGeneral=-1&selectedSubjectsIdNameHidden=%7B%7D&OrderPlacementSmallBusinessSubject=on&OrderPlacementRnpData=on&OrderPlacementExecutionRequirement=on&orderPlacement94_0=0&orderPlacement94_1=0&orderPlacement94_2=0&contractPriceCurrencyId=-1&budgetLevelIdNameHidden=%7B%7D&nonBudgetTypesIdNameHidden=%7B%7D'

    return updated_url


def parse_page(url):
    root_logger = logging.getLogger('zg_tenders')
    res = dict()
    resp = requests.get(url=url, headers=HEADERS)
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, 'html.parser')
        if soup.find_all('div', class_='search-registry-entry-block box-shadow-search-input'):
            elements = soup.find_all('div', class_='search-registry-entry-block box-shadow-search-input')
            for el in elements:
                number = el.find(
                    'div', class_='registry-entry__header-mid__number').a
                tender_url = number.get('href')
                if 'https' not in tender_url:
                    tender_url = BASE_URL + tender_url
                number = number.text.strip().replace('\n', '').replace('№ ', '')
                if el.find(text=re.compile("Окончание подачи заявок")):
                    ending_date = el.find(text=re.compile(
                    "Окончание подачи заявок")).parent.find_next_sibling()
                    ending_date = ending_date.text
                    ending_date = datetime.strptime(ending_date, '%d.%m.%Y')
                    if ending_date < datetime.now()-dr.relativedelta(months=6):
                        # print(number ks+ ' -> ' + ending_date.strftime('%d.%m.%Y'))
                        continue
                    else:
                        ending_date = ending_date.strftime('%d.%m.%Y')
                else:
                    ending_date = ''
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
            root_logger.info(f'Parsed {str(len(elements))} tenders for customer')
        else:
            root_logger.warning(f'0 active tenders for customer')
    else:
        root_logger.warning(f'page {url} is not available')
    return res


def parsing_new(inns):
    for inn, minus_words in inns.items():
        page_num = 0
        url = url_updater(page_num, inn, minus_words)
        while is_next_page(url):
            res.update(parse_page(url))
            page_num += 1
            url = url_updater(page_num, inn, minus_words)
        else:
            res.update(parse_page(url))



def parsing(inns):
    root_logger = logging.getLogger('zg_tenders')
    for inn, minus_words in inns.items():
        page_num = 1
        if len(minus_words) == 0:
            url = f'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString={inn}&morphology=on&search-filter=%D0%94%D0%B0%D1%82%D0%B5+%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D1%8F&pageNumber={page_num}&sortDirection=false&recordsPerPage=_50&showLotsInfoHidden=false&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&priceFromGeneral=50000&currencyIdGeneral=-1'
        elif 'министерство обороны' in inn:
            filter_by_close_tender = 'placingWayList=ZA44%2CZAP44%2CZAE44&'
            excluding_words_list = '%7C'.join(minus_words)
            url = f'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString={inn}&morphology=on&pageNumber={page_num}&sortDirection=false&recordsPerPage=_50&showLotsInfoHidden=false&exclTextHidden={excluding_words_list}%7C&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&priceContractAdvantages44IdNameHidden=%7B%7D&priceContractAdvantages94IdNameHidden=%7B%7D&priceFromGeneral=50000&currencyIdGeneral=-1&selectedSubjectsIdNameHidden=%7B%7D&OrderPlacementSmallBusinessSubject=on&OrderPlacementRnpData=on&OrderPlacementExecutionRequirement=on&orderPlacement94_0=0&orderPlacement94_1=0&orderPlacement94_2=0&{filter_by_close_tender}contractPriceCurrencyId=-1&budgetLevelIdNameHidden=%7B%7D&nonBudgetTypesIdNameHidden=%7B%7D'
        else:
            excluding_words_list = '%7C'.join(minus_words)
            url = f'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString={inn}&morphology=on&pageNumber={page_num}&sortDirection=false&recordsPerPage=_50&showLotsInfoHidden=false&exclTextHidden={excluding_words_list}%7C&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&priceContractAdvantages44IdNameHidden=%7B%7D&priceContractAdvantages94IdNameHidden=%7B%7D&priceFromGeneral=50000&currencyIdGeneral=-1&selectedSubjectsIdNameHidden=%7B%7D&OrderPlacementSmallBusinessSubject=on&OrderPlacementRnpData=on&OrderPlacementExecutionRequirement=on&orderPlacement94_0=0&orderPlacement94_1=0&orderPlacement94_2=0&contractPriceCurrencyId=-1&budgetLevelIdNameHidden=%7B%7D&nonBudgetTypesIdNameHidden=%7B%7D'
            # print(len(url))


        _html = get_html(url)
        if _html.status_code == 200:
            soup = BeautifulSoup(_html.text, 'html.parser')
            pages = soup.find('div', class_='paginator-block').find_all('li', class_='page') 
            if len(pages) > 0:
                root_logger.warning(f'############ Content of {url} has {len(pages)}')

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
                    if el.find(text=re.compile("Окончание подачи заявок")):
                        ending_date = el.find(text=re.compile(
                        "Окончание подачи заявок")).parent.find_next_sibling()
                        ending_date = ending_date.text
                    else:
                        ending_date = ''
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
    headers = ['Ссылка на тендер', 'Окончание подачи заявок', 'Номер', '', 'Заказчик', 'Объект закупки', 'Начальная цена', 'Размещено', 'Обновлено']
    ws.append(headers)
    for tender_number, tender_info in res.items():
        ws.append([tender_info['url'], tender_info['ending_date'], tender_number, '', tender_info['customer'], tender_info['name'], tender_info['price'], tender_info['release_date'], tender_info['refreshing_date'] ])

    ws.column_dimensions['A'].width = 25
    ws.column_dimensions['B'].width = 16
    ws.column_dimensions['C'].width = 24
    ws.column_dimensions['E'].width = 80
    ws.column_dimensions['F'].width = 80
    ws.column_dimensions['G'].width = 16

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
set_logger()

# # iteration for 129
res = dict()
parsing_new(get_inns(FILE_WITH_INNS_129))
sending_email(save_results(res=res, fileprefix='_zg_129'), '129 zakupki-gov by INN', to_emails=to_emails)

# # interation for 113
res = dict()
parsing_new(get_inns(FILE_WITH_INNS))
sending_email(save_results(res=res, fileprefix='_zg_113'), '113 zakupki-gov by INN', to_emails=to_emails)

# iteration for 104
res = dict()
parsing_new(get_inns(FILE_WITH_INNS_104))
sending_email(save_results(res=res, fileprefix='_zg_104'), '104 zakupki-gov by INN', to_emails=to_emails)

# # interation for 113
res = dict()
parsing_new(get_inns(FILE_WITH_KW_113))
sending_email(save_results(res=res, fileprefix='_zg_113'), '113 zakupki-gov by words', to_emails=to_emails)

# iteration for 104
res = dict()
parsing_new(get_inns(FILE_WITH_KW_104))
sending_email(save_results(res=res, fileprefix='_zg_104'), '104 zakupki-gov by words', to_emails=to_emails)

# iteration for 129 
res = dict()
parsing_new(get_inns(FILE_WITH_KW_129))
sending_email(save_results(res=res, fileprefix='_zg_129'), '129 zakupki-gov by words', to_emails=to_emails)

root_logger = logging.getLogger('zg_tenders')
root_logger.info('='*46)
# create_db()
# Get-ChildItem | Where-Object {$_.Name -match '^[0-9]{2}-02-2021_.*'} | foreach {Remove-Item -Path $_.FullName }