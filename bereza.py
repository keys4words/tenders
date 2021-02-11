import sqlite3
import random, os, logging, time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException, ElementNotInteractableException
from openpyxl import Workbook
import yagmail
import keyring
from config.conf_zg import from_email, password, to_emails, cc, bcc


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FILE_WITH_KEYWORDS = os.path.join(BASE_DIR, 'keywords', 'bz_keywords.txt')
FILE_WITH_REGIONS = os.path.join(BASE_DIR, 'keywords', 'bz_regions.txt')
BASE_URL = 'https://agregatoreat.ru/purchases/new'


def create_db():
    with sqlite3.connect('bz.db') as con:
        cur = con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS tenders(
            number TEXT,
            name TEXT,
            timer TEXT,
            customer TEXT,
            price TEXT,
            info TEXT
        )""")

def isInDataBase(number):
    with sqlite3.connect('bz.db') as con:
        cur = con.cursor()
        cur.execute(f"SELECT * FROM tenders WHERE number=='{number}'")
        return cur.fetchone()

def save_tender(number, name, timer, customer, price, info):
    with sqlite3.connect('bz.db') as con:
        cur = con.cursor()
        cur.execute(f"INSERT INTO tenders (number, name, timer, customer, price, info) VALUES('{number}', '{name}', '{timer}', '{customer}', '{price}', '{info}');")


def set_logger():
    root_logger = logging.getLogger('bz')
    handler = logging.FileHandler('logs\\bz.log', 'a', 'utf-8')
    formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)


def get_keywords(filename):
    keywords = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            keywords.append(line.strip())
        return keywords


def page_has_pagination(keyword=keyword, driver=driver):
    retun driver.find_element_by_xpath('//')


def parse_page(keyword, driver):
    delay = random.randint(8, 15)
    WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="filterField-0-input"]')))
    searchbox = driver.find_element_by_xpath('//input[@id="filterField-0-input"]')
    searchbox.send_keys(keyword)

    searchBtn = driver.find_element_by_xpath('//button[@id="applyFilterButton"]')
    searchBtn.click()

    root_logger = logging.getLogger('bz')
    try:
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, '//article[@class="card p-grid"]')))
        # EC.element_to_be_clickable()
        # print('\t row - ok', end='')
        elements = driver.find_elements_by_xpath('//article[@class="card p-grid"]')
        # print('\t elements - ok', end='')
        for el in elements:
            WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, './/h3[@id="tradeNumber"]/a')))
            # WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, './/div[@id="timer"]')))
            try:
                number = el.find_element_by_xpath('.//h3[@id="tradeNumber"]/a')
                number = number.text
            except StaleElementReferenceException:
                number = '#'
                continue
            
            # WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, './/div[@class="cl-black fs12 weight-500 lh20 td-underline wwrap-bw"]')))
            # name = el.find_element_by_xpath('.//div[@class="cl-black fs12 weight-500 lh20 td-underline wwrap-bw"]')
            # name = name.text
            # timer = el.find_element_by_xpath('.//div[@id="timer"]')
            # timer = (timer.text).replace('\n', '')
            # customer = el.find_element_by_xpath('.//div[@class="cl-black fs12 weight-500 lh20 td-underline"]')
            # customer = customer.text
            # price = el.find_element_by_xpath('.//div[@class="cl-green weight-400 fs10"]/span')
            # price = price.text
            # info = el.find_element_by_xpath('.//a[@class="brdr-l-1 cl-green brdr-cl-gray3 px15 py5 flex wrap no-underline"]')
            # info = info.get_attribute('href')

            # if not isInDataBase(number):
            #             save_tender(number=number
            #                 ,name=name
            #                 ,timer=timer
            #                 ,customer=customer
            #                 ,price=price
            #                 ,info=info
            #                 )
            #             res[number] = {
            #                 'name': name,
            #                 'timer': timer,
            #                 'customer': customer,
            #                 'price': price,
            #                 'info': info
            #             }
            print(number)
        
        root_logger.info(f'parsing OK with keyword: {keyword}')
        searchbox.clear()
    except TimeoutException:
        root_logger.warning(f'timeout with keyword: {keyword}')
        searchbox.clear()

def save_results(res):
    wb = Workbook()
    ws = wb.active
    headers = ['Номер','Наименование', 'Время до окончания подачи предложений', 'Заказчик', 'Стартовая цена', 'Информация о закупке']
    ws.append(headers)
    for tender_number, tender_info in res.items():
        ws.append([tender_number, tender_info['name'], tender_info['timer'], tender_info['customer'], tender_info['price'], tender_info['info']])
    
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 100
    ws.column_dimensions['D'].width = 60
    ws.column_dimensions['E'].width = 20

    name = os.path.join(BASE_DIR, 'out', datetime.now().strftime("%d-%m-%Y_%H-%M"))
    results_file_name = name + '_bz.xlsx'
    wb.save(results_file_name)
    root_logger = logging.getLogger('bz')
    root_logger.info(f'File {results_file_name} was successfully saved')
    return results_file_name
        

def parsing(keywords):
    # btn_all_filters = driver.find_element_by_xpath('//button[@data-v-7755f139][2]')
    # btn_all_filters.click()

    # WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.XPATH, '//label[contains(text(), "Субъект РФ")]/following-sibling::div')))
    # regions = get_keywords(FILE_WITH_REGIONS)
    # print(regions)
    # for index, region in enumerate(regions):
    #     regions_dropdown = driver.find_element_by_xpath('//label[contains(text(), "Субъект РФ")]/following-sibling::div')
    #     regions_dropdown_arrow = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//label[contains(text(), "Субъект РФ")]/following-sibling::div/div[1]')))

    #     # print(regions_dropdown.get_attribute('class'))
    #     regions_dropdown.send_keys(region)
    #     time.sleep(random.randint(2, 3))

    #     if index%4 == 0:
    #         driver.execute_script('window.scrollBy(0, 20)', '')
        
    #     options_elements = driver.find_elements_by_xpath('//label[contains(text(), "Субъект РФ")]/following-sibling::div/div[3]/ul/li')[:-2]
    #     for el in options_elements:
    #         try:
    #             el.click()
    #         except ElementClickInterceptedException:
    #             driver.execute_script('window.scrollBy(0, 20)', '')
    #             el.click()
    #         except ElementNotInteractableException:
    #             WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
    #                 (By.XPATH, el))).click()
                # el.click()

    for keyword in keywords:
        parse_page(keyword=keyword, driver=driver)

        # recursion parsing
        # window_before = driver.window_handles[0]
        # while page_has_pagination(keyword=keyword, driver=driver):
        #     parse_page(keyword=keyword, driver=driver)
        #     driver.find_element_by_xpath("//a[@href='http://www.cdot.in/home.htm']").click()
        #     window_after = driver.window_handles[1]
        #     driver.switch_to_window(window_after)
        #     parse_page(keyword=keyword, driver=driver)

        # if driver.find_element_by_xpath('//a[@class="ui-paginator-next ui-paginator-element ui-state-default ui-corner-all"]'):
        #     counter = 1
        #     while counter < len(pagination):
        #         new_url = BASE_URL + '/page/' + str(counter+1)
        #         driver.get(new_url)
        #         parse_page(keyword=keyword, driver=driver)
        #         counter += 1
    root_logger = logging.getLogger('bz')
    root_logger.info(f'Parsed ' + str(len(res)) + ' tenders')


def sending_email(filename):
    body = "Below you find file with actual tenders from Berezka platform"
    contents = [
        body,
        filename
    ]

    yagmail.register(from_email, password)
    # keyring.set_keyring(keyring.backend.Win32CryptoKeyring())
    yag = yagmail.SMTP(from_email)
    yag.send(
        to=to_emails,
        subject="Berezka Tenders",
        cc=cc,
        bcc=bcc,
        contents=contents,
        # attachments=filename,
    )
    root_logger = logging.getLogger('bz')
    root_logger.info(f'File was sended to {to_emails}, copy: {cc}, blind copy: {bcc}')


############################################################
res = dict()

driver = webdriver.Chrome()
driver.maximize_window()
driver.get(BASE_URL)

set_logger()

parsing(get_keywords(FILE_WITH_KEYWORDS))

root_logger = logging.getLogger('bz')
# if len(res)>= 1:
#     sending_email(save_results(res))
# else:
#     root_logger.info('There is NO tenders')
# root_logger.info('='*36)


driver.quit()
# create_db()
