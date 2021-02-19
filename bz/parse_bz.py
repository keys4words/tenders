import random, os, logging, time

from requests_html import HTMLSession
from selenium import webdriver


#create the session

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FILE_WITH_KEYWORDS = os.path.join(BASE_DIR, 'keywords', 'bz_keywords.txt')
TEST = os.path.join(BASE_DIR, 'keywords', 'test.txt')
FILE_WITH_REGIONS = os.path.join(BASE_DIR, 'keywords', 'bz_regions.txt')
BASE_URL = 'https://agregatoreat.ru/purchases/new'
DB_PATH = os.path.join(BASE_DIR, 'db', 'bz.db')


driver = webdriver.Chrome()
driver.maximize_window()
driver.get(BASE_URL)



def get_keywords(filename):
    keywords = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            keywords.append(line.strip())
        return keywords

for key in get_keywords(FILE_WITH_KEYWORDS):
    

WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="filterField-0-input"]')))
searchbox = driver.find_element_by_xpath('//input[@id="filterField-0-input"]')
searchbox.send_keys(keyword)

searchBtn = driver.find_element_by_xpath('//button[@id="applyFilterButton"]')
searchBtn.click()

session = HTMLSession()


r = session.get(BASE_URL)
r.html.render(sleep=1, keep_page=True, scrolldown=1)

#take the rendered html and find the element that we are interested in
search_box = r.find('input#filterField-0-input').
videos = r.html.find('#video-title')

#loop through those elements extracting the text and link
for item in videos:
    video = {
        'title': item.text,
        'link': item.absolute_links
    }
    print(video)