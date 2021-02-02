import requests, random, os, logging, time, re, sqlite3
from bs4 import BeautifulSoup
from pprint import pprint


HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36', 'accept': '*/*'}
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
URL2 = 'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString=7701903677&morphology=on&search-filter=%D0%94%D0%B0%D1%82%D0%B5+%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D1%8F&pageNumber=1&sortDirection=false&recordsPerPage=_50&showLotsInfoHidden=false&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&currencyIdGeneral=-1'


def get_inns(filename):
    inns = dict()
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            if ':' in line:
                customer = line.split(':')[0]
                minus_words = [el.strip() for el in (line.split(':')[1]).split(',')]
                minus_words = [el.replace(' ', '+') for el in minus_words]
                inns[customer] = minus_words
            else:
                inns[line.strip()] = []
        return inns


def parse_page(url):
    print('parse page:', url)
    resp = requests.get(url=url, headers=HEADERS)
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, 'html.parser')
        if soup.find_all('div', class_='search-registry-entry-block box-shadow-search-input'):
            elements = soup.find_all('div', class_='search-registry-entry-block box-shadow-search-input')
            qty = len(elements)
            # print('qty =', qty)
            return qty
    return 0


def is_next_page(url):
    resp = requests.get(url=url, headers=HEADERS)
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, 'html.parser')
        return soup.find('a', class_='paginator-button paginator-button-next')


def url_updater(page_num, inn, minus_words):
    # keyword = '5032292612'
    # minus_words = ['питания', 'яйца']
    excluding_words_list = '%7C'.join(minus_words)
    page_num += 1
    updated_url = f'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString={inn}&morphology=on&search-filter=%D0%94%D0%B0%D1%82%D0%B5+%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D1%8F&pageNumber={page_num}&sortDirection=false&recordsPerPage=_50&showLotsInfoHidden=false&exclTextHidden={excluding_words_list}&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&priceFromGeneral=50000&currencyIdGeneral=-1'
    return updated_url


def parsing():
    FILE_WITH_INNS_TEST = os.path.join(BASE_DIR, 'inn', 'zg_104_test.txt')
    for inn, minus_words in (get_inns(FILE_WITH_INNS_TEST)).items():
        page_num = 0
        qty = 0
        url = url_updater(page_num, inn, minus_words)
        while is_next_page(url):
            qty += parse_page(url)
            page_num += 1
            url = url_updater(page_num, inn, minus_words)
        else:
            qty += parse_page(url)
        print(inn, qty)

############################

print(parsing())