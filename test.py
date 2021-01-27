import requests, random, os, logging, time, re, sqlite3
from bs4 import BeautifulSoup


HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36', 'accept': '*/*'}
page_num = 0
URL = f'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString=%D1%83%D1%84%D1%81%D0%B8%D0%BD&morphology=on&search-filter=%D0%94%D0%B0%D1%82%D0%B5+%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D1%8F&pageNumber={page_num}&sortDirection=false&recordsPerPage=_50&showLotsInfoHidden=false&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&currencyIdGeneral=-1'
URL2 = 'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString=7701903677&morphology=on&search-filter=%D0%94%D0%B0%D1%82%D0%B5+%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D1%8F&pageNumber=1&sortDirection=false&recordsPerPage=_50&showLotsInfoHidden=false&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&currencyIdGeneral=-1'


def parse_page(url):
    resp = requests.get(url=url, headers=HEADERS)
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, 'html.parser')
        if soup.find_all('div', class_='search-registry-entry-block box-shadow-search-input'):
            elements = soup.find_all('div', class_='search-registry-entry-block box-shadow-search-input')
            qty = len(elements)
            return qty
    return None


def is_next_page(url):
    resp = requests.get(url=url, headers=HEADERS)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            return soup.find('a', class_='paginator-button paginator-button-next')


def url_updater():
    page_num += 1
    return f'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString=%D1%83%D1%84%D1%81%D0%B8%D0%BD&morphology=on&search-filter=%D0%94%D0%B0%D1%82%D0%B5+%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D1%8F&pageNumber={page_num}&sortDirection=false&recordsPerPage=_50&showLotsInfoHidden=false&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&currencyIdGeneral=-1'


def parsing():
    print(parse_page(initial_url))
    while is_next_page(initial_url):
        print(parse_page(url_updater()))


print(qty)