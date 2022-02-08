import sqlite3
import random, os, logging, time
import base64
from datetime import datetime
from pprint import pprint
from pymongo import MongoClient

from config.conf_bz import sendgrid_api, TO_EMAIL, FROM_EMAIL
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (Mail, Attachment, FileContent, FileName, FileType, Disposition, ContentId)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException, ElementNotInteractableException
from openpyxl import Workbook
import yagmail
import keyring
from config.conf_zg import from_email, password, to_emails, cc, bcc


# client = MongoClient("mongodb://localhost:27017")
# db = client["tenders"]
# bz = db.bz

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'db', 'bz.db')
FILE_WITH_KEYWORDS = os.path.join(BASE_DIR, 'keywords', 'bz.txt')
TEST = os.path.join(BASE_DIR, 'keywords', 'test.txt')
FILE_WITH_REGIONS = os.path.join(BASE_DIR, 'keywords', 'bz_regions.txt')
BASE_URL = 'https://agregatoreat.ru/purchases/new'


# old db
def create_db():
    with sqlite3.connect(DB_PATH) as con:
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
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute(f"SELECT * FROM tenders WHERE number=='{number}'")
        return cur.fetchone()
    # return bz.find_one({
    # "number": number
# })

def save_tender(number, name, timer, customer, price, info):
    new_tender = {
        "number": number,
        "name": name,
        'timer': timer,
        'customer': customer,
        'price': price,
        'info': info
    }
    
    # bz.insert_one(new_tender)
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute(f"INSERT INTO tenders (number, name, timer, customer, price, info) VALUES('{number}', '{name}', '{timer}', '{customer}', '{price}', '{info}');")


def set_logger():
    root_logger = logging.getLogger('bz')
    log_file = os.path.join(BASE_DIR, 'logs', 'bz.log')
    handler = logging.FileHandler(log_file, 'a', 'utf-8')
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


# def page_has_pagination(keyword=keyword, driver=driver):
#     return driver.find_element_by_xpath('//')


def parse_page(keyword, driver):
    delay = random.randint(8, 15)
    WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="filterField-2-input"]')))
    searchbox = driver.find_element_by_xpath('//input[@id="filterField-2-input"]')
    searchbox.send_keys(keyword)

    searchBtn = driver.find_element_by_xpath('//button[@id="applyFilterButton"]')
    searchBtn.click()

    time.sleep(random.randint(1, 3))
    article = driver.find_element_by_tag_name('article')
    isTenders = article.get_attribute("class")

    root_logger = logging.getLogger('bz')
    
    if isTenders != 'not-found':
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, '//article[@class="card p-grid"]')))
        elements = driver.find_elements_by_xpath('//article[@class="card p-grid"]')
        tenders_on_page = len(elements)
        for el in elements:
            driver.execute_script("window.scrollTo(0, 200);")
            # time.sleep(1)
            try:
                number = el.find_element_by_xpath('.//h3[@id="tradeNumber"]/a')
                number = number.text
            except StaleElementReferenceException:
                WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, './/h3[@id="tradeNumber"]/a')))
                number = el.find_element_by_xpath('.//h3[@id="tradeNumber"]/a')
                number = number.text
            try:
                name = el.find_element_by_xpath('.//p[@id="subject"]')
                name = name.text
            except StaleElementReferenceException:
                name = el.find_element_by_xpath('.//p[@id="subject"]')
                name = name.text
            try:
                timer = el.find_element_by_xpath('.//span[@id="timer"]')
                timer = (timer.text).replace('\n', '')
            except StaleElementReferenceException:
                timer = el.find_element_by_xpath('.//span[@id="timer"]')
                timer = (timer.text).replace('\n', '')
                
            customer = el.find_element_by_xpath('.//span[@id="organizerInfoNameLink"]')
            customer = customer.text
            price = el.find_element_by_xpath('.//h1[@id="purchasePrice"]')
            price = price.text
            price = price.replace(' ', '')

            info = el.find_element_by_xpath('.//a[@id="tradeInfoLink"]')
            info = info.get_attribute('href')

            if not isInDataBase(number):
                        save_tender(number=number
                            ,name=name
                            ,timer=timer
                            ,customer=customer
                            ,price=price
                            ,info=info
                            )
                        res[number] = {
                            'name': name,
                            'timer': timer,
                            'customer': customer,
                            'price': price,
                            'info': info
                        }

        root_logger.info(f'{keyword}: parsing -> {tenders_on_page}')
        searchbox.clear()
    else:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        root_logger.warning(f'{keyword}: parsing -> timeout')
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
        

def parsing(keywords, driver):
    for keyword in keywords:
        driver.execute_script("window.scrollTo(0, 0);")
        parse_page(keyword=keyword, driver=driver)

        # TODO: download all row html code with data
        # source = driver.page_source()

        # recursion parsing
        # window_before = driver.window_handles[0]
        # while page_has_pagination(keyword=keyword, driver=driver):
        #     parse_page(keyword=keyword, driver=driver)
        #     driver.find_element_by_xpath("//a[@href='http://www.cdot.in/home.htm']").click()
        #     window_after = driver.window_handles[1]
        #     driver.switch_to_window(window_after)
        #     parse_page(keyword=keyword, driver=driver)

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

def sending_email_smartgrid(filename):
    encoded = base64.b64encode(data).decode()
    message = Mail(
    from_email=FROM_EMAIL,
    to_emails=TO_EMAIL,
    subject='Your File is Ready',
    html_content='<strong>Attached is Your Scraped File</strong>')
    attachment = Attachment()
    attachment.file_content = FileContent(encoded)
    attachment.file_type = FileType('text/csv')
    attachment.file_name = FileName('scraped.csv')
    attachment.disposition = Disposition('attachment')
    attachment.content_id = ContentId('Example Content ID')
    message.attachment = attachment
    try:
        sg = SendGridAPIClient(sendgrid_api)
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
         print(e)

        
############################################################
res = dict()

chrome_options = Options()
# chrome_options.binary_location = os.environ.get('GOOGLE_CHROME_BIN')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-sh-usage')


user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')
chrome_options.add_argument('--ignore-certificate-errors')
# driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=chrome_options)
driver = webdriver.Chrome(options=chrome_options)
driver.maximize_window()
with driver:
    wait = WebDriverWait(driver, 10)
    driver.get(BASE_URL)

    set_logger()

    # parsing(get_keywords(TEST), driver)
    parsing(get_keywords(FILE_WITH_KEYWORDS), driver)

    root_logger = logging.getLogger('bz')
    if len(res)>= 1:
        # pprint(res)
        sending_email(save_results(res))
    else:
        root_logger.info('There is NO tenders')
    root_logger.info('='*36)

driver.quit()
# create_db()
