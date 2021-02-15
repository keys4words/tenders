from selenium import webdriver
from zg.utils.GetElemWrapper import GetElemWrapper
import zg.utils.utils as utils


class ZakupkiGov():

    def __init__(self):
        self.keywords = StreamInOut().get_keywords()

    def test(self):
        baseUrl = 'https://zakupki.gov.ru'
        driver = webdriver.Chrome()
        driver.maximize_window()
        driver.get(baseUrl)

        elements = driver.find_elements_by_xpath('//article[@class="card p-grid"]')
