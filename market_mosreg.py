from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from openpyxl import Workbook
import random, os, logging, time
from datetime import datetime
import yagmail
from config import from_email, password, to_emails, cc, bcc


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FILE_WITH_KEYWORDS = os.path.join(BASE_DIR, 'keywords', 'mm_keywords.txt')
BASE_URL = 'https://market.mosreg.ru/Trade'


def set_logger():
    root_logger = logging.getLogger('mm')
    handler = logging.FileHandler('logs\\mm.log', 'w', 'utf-8')
    formatter = logging.Formatter(
        '%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)


def get_keywords(filename):
    keywords = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            keywords.append(line.strip())
        return keywords


def parse_page(keyword, driver):
    # print(keyword)
    root_logger = logging.getLogger('mm')

    # insert keyword 
    searchbox = driver.find_elements_by_xpath('//input[@data-bind="value: pageVM.filterTradeName"]')[0]
    searchbox.send_keys(keyword)

    # click search button
    searchBtn = driver.find_element_by_xpath('//button[@data-bind="click: pageVM.searchData"]')
    WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.XPATH, '//button[@data-bind="click: pageVM.searchData"]')))
    searchBtn.click()

    # set 100 results on page mode
    time.sleep(1)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    WebDriverWait(driver, 2).until(EC.presence_of_element_located(
        (By.XPATH, '//div[@class="pagination__select"]//span[@class="select2-selection__arrow"]')))
    qtyOnPage = driver.find_element_by_xpath(
        '//div[@class="pagination__select"]//span[@class="select2-selection__arrow"]')
    WebDriverWait(driver, 6).until(EC.element_to_be_clickable(
        (By.XPATH, '//div[@class="pagination__select"]//span[@class="select2-selection__arrow"]')))
    qtyOnPage.click()
    selectHundred = driver.find_element_by_xpath(
        '//ul[@id="select2-selectPagination-results"]/li[5]')
    selectHundred.click()

    delay = random.randint(6, 15)
    try:
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, '//div[@data-bind="foreach: pageVM.listTradesTest"]/div')))
    #     # print('\t row - ok', end='')

        elements = driver.find_elements_by_xpath('//div[@data-bind="foreach: pageVM.listTradesTest"]/div')
        # print('\t elements - ok', end='')
        for el in elements:
            WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, './/div[@class="blockResult__rightContent-suggestion"]')))
            WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, './/a[@class="blockResult__leftContent-linkString"]')))
            try:
                WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, './/span[@data-bind="text: Id"]')))
                number = el.find_element_by_xpath('.//span[@data-bind="text: Id"]')
                number = number.text
                name = el.find_element_by_xpath('.//a[@class="blockResult__leftContent-linkString"]')
                url = name.get_attribute('href')
                name = name.text
                start = el.find_element_by_xpath('.//span[contains(@data-bind, "dateString: PublicationDate, datePattern:")]')
                start = start.text
                end = el.find_element_by_xpath('.//span[@data-bind="text: FillingApplicationEndDate"]')
                end = end.text
                price = el.find_element_by_xpath('.//p[contains(@data-bind, "number: InitialPrice")]')
                price = price.text
                customer_card = el.find_element_by_xpath('.//a[contains(@data-bind, "Customer/ViewCustomerInfoById")]')
                customer_card = customer_card.get_attribute('href')
            except StaleElementReferenceException:
                print('Stale Exception!!!')
            
            if number in res:
                res[number]['start']  = start
                res[number]['end']  = end
            res[number] = {'name': name,
                           'url': url,
                           'start': start,
                           'end': end,
                           'price': price,
                           'customer_card': customer_card }
            
        root_logger.info(f'parsed {len(elements)} tenders with keyword: {keyword}')
        searchbox.clear()
    except TimeoutException:
        root_logger.warning(f'timeout with keyword: {keyword}')
        # print('something goes wrong')
        searchbox.clear()


def parsing(keywords, driver):
    for keyword in keywords:
        parse_page(keyword=keyword, driver=driver)


def save_results(res):
    wb = Workbook()
    ws = wb.active
    headers = ['Номер', 'Наименование', 'Ссылка', 'Начало приема заявок',
               'Окончание приема заявок', 'Цена', 'Карточка Заказчика']
    ws.append(headers)
    for tender_number, tender_info in res.items():
        ws.append([tender_number, tender_info['name'], tender_info['url'], tender_info['start'], tender_info['end'], tender_info['price'], tender_info['customer_card']])

    ws.column_dimensions['B'].width = 100
    ws.column_dimensions['D'].width = 30
    ws.column_dimensions['E'].width = 30
    ws.column_dimensions['F'].width = 40
    name = os.path.abspath(os.path.dirname(__file__))
    name = os.path.join(name, 'out', datetime.now().strftime("%d-%m-%Y_%H-%M"))
    results_file_name = name + '_mm.xlsx'
    wb.save(results_file_name)
    root_logger = logging.getLogger('mm')
    root_logger.info(f'File {results_file_name} was saved')
    return results_file_name


def sending_email(filename):
    body = "Below you find file with actual tenders from Market Mosreg"
    contents = [
        body,
        filename
    ]

    yagmail.register(from_email, password)
    yag = yagmail.SMTP(from_email)
    yag.send(
        to=to_emails,
        subject="market.mosreg.ru",
        cc=cc,
        bcc=bcc,
        contents=contents,
        # attachments=filename,
    )
    root_logger = logging.getLogger('mm')
    root_logger.info(
        f'File was sended to {to_emails}, copy: {cc}, blind copy: {bcc}')


driver = webdriver.Chrome()
driver.maximize_window()
driver.get(BASE_URL)

res = dict()

set_logger()
parsing(get_keywords(FILE_WITH_KEYWORDS), driver)
sending_email(save_results(res))

root_logger = logging.getLogger('mm')
root_logger.info('='*46)
    
driver.quit()
