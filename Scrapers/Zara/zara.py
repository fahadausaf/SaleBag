"""
    Author: Tauqeer Sajid
    Date created: 18/12/2021
    Desc: This Module contains scraper code for www.zara.com/uk
"""

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from bs4 import BeautifulSoup as bs
import pandas as pd
import requests
import cchardet
import random
import json
import time
import os


def get_random_useragent() -> str:
    """
    This method returns a random app name from the "new_agent.json" as user-agent
    :return: (str)
    """

    with open(r'user_agents.txt', 'r') as f:
        user_agents = f.read()

    user_agents = user_agents.split('\n')
    rand_index = random.randint(0, len(user_agents) - 1)
    return user_agents[rand_index]


class ZARA:

    def __init__(self):
        self.main_url = "https://www.zara.com/uk/"
        self.options = Options()
        self.options.headless = True

        self.desired = DesiredCapabilities.FIREFOX
        self.profile = None
        self.driver = None

        self.data = []
        self.category_name = ""
        self.sub_category_name = ""
        self.output_file_path = "data/output.json"
        self.webdriver_path = "firefox_driver/geckodriver"

    def parse(self):
        """
            This method is for parsing the categories and sub-categories links firefox webdriver is used to handle
             dynamics content.
            Categories links will send to parse listings to get product links.
        """

        try:
            retry = 0
            while retry < 5:
                try:
                    self.profile = webdriver.FirefoxProfile()
                    self.profile.set_preference("dom.webdriver.enabled", False)
                    self.profile.set_preference('useAutomationExtension', False)
                    self.profile.set_preference("general.useragent.override", get_random_useragent())
                    self.profile.update_preferences()
                    self.driver = webdriver.Firefox(self.profile, executable_path=self.webdriver_path,
                                                    options=self.options,
                                                    desired_capabilities=self.desired)
                    self.driver.maximize_window()
                    self.driver.get(self.main_url)
                    time.sleep(5)
                    self.driver.find_element_by_xpath('//*[@id="onetrust-accept-btn-handler"]').click()
                    time.sleep(2)
                    self.driver.find_element_by_xpath('/html/body/div[2]/div[1]/div[1]/div/div/header/div/div[1]/button').click()

                    break
                except:
                    self.driver.quit()
                    retry += 1
        except:
            print("brwoser suppor errror")
            return
 
        xpath = "/html/body/div[2]/div[1]/div[1]/div/div/aside/div/nav/div/ul/li[{0}]/a"
        for index in range(1, 4):
            time.sleep(2)
            self.driver.find_element_by_xpath(xpath.format(index)).click()
            self.get_categories(self.driver.page_source, index - 1)

        indexes = [4, 8]
        xpath = "/html/body/div[2]/div[1]/div[1]/div/div/aside/div/nav/div/ul/li[{0}]/a"
        for index in indexes:
            try:
                if index == 4:
                    self.driver.find_element_by_xpath(xpath.format(index)).click()
                    time.sleep(0.10)
                else:
                    self.driver.find_element_by_xpath(
                        '/html/body/div[2]/div[1]/div[1]/div/div/header/div/div[1]/button').click()
                attribute = self.driver.find_element_by_xpath(xpath.format(index))
                self.category_name = attribute.text
                self.sub_category_name = ""
                link = attribute.get_attribute('href')
                print('Scraping started for category "{0}" link "{1}"'.format(self.category_name, link))
                self.get_product_listings(link)
                print('Scraping completed for category "{0}" link "{1}"'.format(self.category_name, link))
                self.save_data()
            except:
                pass

        self.driver.quit()
        print('Data saved in', self.output_file_path)

    def get_categories(self, page_source, index):
        soup = bs(page_source, 'html.parser')
        category = soup.findAll('li', class_='layout-categories-category--level-1')[index]
        self.category_name = category.find('a').text
        sub_categories = category.find('ul', class_='layout-categories-category__subcategory')

        for sub_category in sub_categories.findAll('a', class_='layout-categories-category__link'):
            try:
                categories_except = ['ZARA ORIGINS', 'HOME', 'GIFT CARD']
                if sub_category.text not in categories_except:
                    self.sub_category_name = sub_category.text
                    link = sub_category['href']
                    print('Scraping started for category "{0}" sub category "{1}" link "{2}"'.format(self.category_name,
                                                                                                     self.sub_category_name,
                                                                                                     link))
                    self.get_product_listings(link)
                    self.save_data()
                    print(
                        'Scraping completed for category "{0}" sub category "{1}" link "{2}"'.format(self.category_name,
                                                                                                     self.sub_category_name,
                                                                                                     link))
            except:
                pass

    def get_product_listings(self, link):
        """
            This method parse the product listings and get the links and pass links to get_product function
            for getting product information.
        """

        products_links = []
        products_links_len = 0

        page_number = 1
        while True:
            soup = self.get_request(link + "?page={0}".format(page_number))
            try:
                products_links.extend([a_tag['href'] for a_tag in
                                       soup.findAll('a', class_='product-link product-grid-product__link link')])
                page_number += 1
            except:
                break

            if len(products_links) > products_links_len:
                products_links_len = len(products_links)
            else:
                break

        products_links = list(set(products_links))

        for product_link in products_links:
            try:
                self.get_product(product_link)
            except:
                try:
                    self.get_carousel_items(product_link)
                except:
                    pass

    def get_carousel_items(self, link):
        soup = self.get_request(link)
        a_tags = soup.find('ul', class_="carousel__items").findAll('a',
                                                                   class_="product-link product-secondary-product__link link")

        for a_tag in a_tags:
            try:
                self.get_product(a_tag['href'])
            except:
                pass

    def get_product(self, link):
        """
            This method parse the product information
        """

        soup = self.get_request(link)

        json_info = json.loads(str(soup.find('script', type="application/ld+json")).split('>')[1].split('<')[0])[0]
        try:
            name = soup.find('h1', class_='product-detail-info__name').text
        except:
            name = ""

        try:
            description = soup.find('div', class_='expandable-text__inner-content').text
        except:
            description = ""

        try:
            color = soup.find('p', class_='product-detail-selected-color product-detail-info__color').text
        except:
            color = ""

        try:
            images = [img['srcset'].split(',')[-1].split(' ')[1] for img in
                      soup.find('ul', class_='product-detail-images__images').findAll('source', sizes="40vw")]
        except:
            images = []

        try:
            price = soup.find('span', class_='price__amount-current').text
        except:
            price = ""

        try:
            size = [size for size in soup.find('ul', class_='product-detail-size-selector__size-list').text.split(' ')
                    if size != ""]
        except:
            size = []

        self.data.append({
            "name": name,
            "description": description,
            "category": self.category_name,
            "sub_category": self.sub_category_name,
            "color": color,
            "images": images,
            "price": price,
            "size": size,
            "sku": json_info['sku'],
            "url": json_info['offers']['url']
        })

    def get_request(self, url):
        """
            This method get the page html with random user agents and used BeautifulSoup library to parse html
        """

        session = requests.Session()
        session.headers.update({'User-Agent': get_random_useragent()})

        response = session.get(url)
        soup = bs(response.text, 'html.parser')

        time.sleep(1)

        return soup

    def save_data(self):
        """
            This method save the product information in data/output.json file
        """

        df = pd.DataFrame(self.data)

        if os.path.isfile(self.output_file_path):
            # if exist open read it
            df_load = pd.read_json(self.output_file_path)
            # add data that you want to save
            df_load = pd.concat([df_load, df], axis=0)

            # save it to json file
            df_load.to_json(self.output_file_path, orient='records')
        else:
            df.to_json(self.output_file_path, orient='records')

        self.data = []


zara = ZARA()
print("parsing started")
zara.parse()
print("parsing ended")
