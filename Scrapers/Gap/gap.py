"""
    Author: Tauqeer Sajid
    Date created: 17/12/2021
    Desc: This Module contains scraper code for gap.co.ok
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
import re
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


class GAP:

    def __init__(self):
        self.session = requests.Session()
        self.main_url = "https://www.gap.co.uk"
        self.sub_categories = ['categories', 'teen girl categories', 'toddler girl', 'newborn', 'activewear',
                               'toddler boy', 'gapbody', 'accessories', 'clothing', 'teen guy categories',
                               'baby (0-24m)']

        self.options = Options()
        self.options.headless = True
        self.profile = None
        self.driver = None

        self.desired = DesiredCapabilities.FIREFOX

        self.category_name = ""
        self.sub_cat_name = ""
        self.sub_sub_cat_name = ""
        self.output_file_path = "data/output.json"
        self.webdriver_path = "firefox_driver/geckodriver"
        self.data = []

    def parse(self):
        soup = self.get_request(self.main_url)
        self.get_category_links(soup)

    def get_category_links(self, soup):
        categories = soup.findAll('li', class_="navigation__item")[2:-1]
        for category in categories:
            self.get_category(category)

    def get_category(self, category):
        self.category_name = category.find('div', class_='navigation__category-name').text

        a_tags = category.findAll('a')
        for a_tag in a_tags:
            for sub_category in self.sub_categories:
                if self.category_name.lower() == "sale":
                    self.sub_cat_name = 'Shop All Sale'
                else:
                    self.sub_cat_name = sub_category

                url_format = '/gap/{0}/{1}'.format(self.category_name.lower(), sub_category.replace(' ', '-'))
                try:
                    if url_format in a_tag['href'] or self.category_name.lower() == "sale":
                        url = self.main_url + a_tag['href']
                        self.sub_sub_cat_name = a_tag.text.strip()

                        print("Scraping started for '{0}' sub category '{1}' sub sub category '{2}'".format(
                            self.category_name, self.sub_cat_name, self.sub_sub_cat_name))
                        try:
                            product_listing_links = self.parse_product_listing_page(url)
                        except Exception as Ex:
                            print(Ex)
                            product_listing_links = []

                        start_time = time.time()
                        for link in product_listing_links:
                            self.parse_product_page(link)
                        print("--- %s seconds ---" % (time.time() - start_time))
                        print("Scraping completed for '{0}' sub category '{1}' sub sub category '{2}'".format(
                            self.category_name, self.sub_cat_name, self.sub_sub_cat_name))
                except:
                    pass

            self.save_data()

    def parse_product_listing_page(self, url):
        self.profile = webdriver.FirefoxProfile()
        self.profile.set_preference("dom.webdriver.enabled", False)
        self.profile.set_preference('useAutomationExtension', False)
        self.profile.set_preference("general.useragent.override", get_random_useragent())
        self.profile.update_preferences()
        self.driver = webdriver.Firefox(self.profile, executable_path=self.webdriver_path, options=self.options,
                                        desired_capabilities=self.desired)
        self.driver.maximize_window()

        self.driver.get(url)

        self.scroll_page()

        soup = bs(self.driver.page_source, 'html.parser')
        links = soup.findAll('a', class_='thumb-link')
        product_listing_links = [link['href'] for link in links]

        self.driver.quit()
        return product_listing_links

    def parse_product_page(self, link):
        try:
            soup = self.get_request(link)
            reviews_link = "https://display.powerreviews.com/m/{merchant_id}/l/{locale}/product/{product_id}/reviews?apikey={api_key}&_noconfig=true"
            product_details = dict()
            for script in soup.findAll('script'):
                if "var pdpTealium =" in str(script):
                    regex_pattern = r'(?<=var pdpTealium =)[^;]*'
                    result = re.search(regex_pattern, str(soup))
                    product_info = json.loads(result[0].strip())

            product_details['productID'] = product_info['ID']
            product_details['productName'] = product_info['name']
            product_details['productUrl'] = link
            product_details['price'] = product_info['pricing']["formattedStandard"]
            product_details['discountPrice'] = product_info['pricing']["formattedSale"]
            product_details['isPromo'] = product_info['pricing']['isPromoPrice']
            product_details['description'] = '\n'.join(
                [li.text.replace('\n', '') for div in soup.findAll('div', class_='sds_body-a') for li in
                 div.findAll('li')])
            product_details['imageUrls'] = [image['href'] for image in soup.findAll('a', class_='pdp_thumbnail-link')]
            product_details['category'] = self.category_name
            product_details['subCategory'] = self.sub_cat_name
            product_details['subSubCategory'] = self.sub_sub_cat_name
            product_details['colors'] = [color['val'] for color in product_info['variations']['attributes'][0]['vals']]
            product_details['sizes'] = [size['val'] for size in product_info['variations']['attributes'][-1]['vals']]

            for num in product_details['productID']:
                if int(num) == 0:
                    product_details['productID'] = product_details['productID'][1:]
                else:
                    break

            regex_pattern = r'(?<=window.POWER_REVIEWS_CONFIG = {)[^}]*'
            result = re.search(regex_pattern, str(soup))
            reviews_request_data = "".join(result[0].replace('\n', '').split(' '))
            reviews_request_data = {var.split(':')[0]: var.split(':')[1].replace('"', '') for var in
                                    reviews_request_data.split(',') if var != ""}

            reviews_link = reviews_link.format(merchant_id=reviews_request_data['merchant_id'],
                                               locale=reviews_request_data['locale'],
                                               product_id=product_details['productID'],
                                               api_key=reviews_request_data['api_key'])

            self.session.headers.update({'User-Agent': get_random_useragent()})
            reviews_data = self.session.get(reviews_link).json()

            product_details['reviews_count'] = reviews_data['paging']['total_results']

            self.data.append(product_details)
            time.sleep(0.25)
        except:
            pass

    def get_request(self, url):
        self.session.headers.update({'User-Agent': get_random_useragent()})
        response = self.session.get(url)
        soup = bs(response.text, 'lxml')

        return soup

    def save_data(self):
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

    def scroll_page(self):
        speed = 10000
        current_scroll_position, new_height = 0, 1
        while current_scroll_position <= new_height:
            current_scroll_position += speed
            self.driver.execute_script("window.scrollTo(0, {});".format(current_scroll_position))
            # Wait to load page
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")


gap = GAP()
gap.parse()
