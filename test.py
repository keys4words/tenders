import requests, random, os, logging, time, re, sqlite3
from bs4 import BeautifulSoup


HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36', 'accept': '*/*'}
URL = 'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString=%D1%83%D1%84%D1%81%D0%B8%D0%BD&morphology=on&search-filter=%D0%94%D0%B0%D1%82%D0%B5+%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D1%8F&pageNumber=1&sortDirection=false&recordsPerPage=_50&showLotsInfoHidden=false&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&currencyIdGeneral=-1'
URL2 = 'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString=7701903677&morphology=on&search-filter=%D0%94%D0%B0%D1%82%D0%B5+%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D1%8F&pageNumber=1&sortDirection=false&recordsPerPage=_50&showLotsInfoHidden=false&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&currencyIdGeneral=-1'

def get_html(url, params=None):
    resp = requests.get(url=url, headers=HEADERS, params=params)
    return resp


_html = get_html(URL)
if _html.status_code == 200:
    soup = BeautifulSoup(_html.text, 'html.parser')
    pages = len(soup.find('div', class_='paginator-block').find_all('li', class_='page'))
    print(pages)