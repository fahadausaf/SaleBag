from bs4 import BeautifulSoup as bs
import concurrent.futures
import pandas as pd
import requests
import cchardet
import random
import time
import os


def get_random_useragent() -> str:
    """
    This method returns a random app name from the "new_agent.json" as user-agent
    :return: (str)
    """

    with open(r'user_agent.txt', 'r') as f:
        user_agents = f.read()

    user_agents = user_agents.split('\n')
    rand_index = random.randint(0, len(user_agents) - 1)
    return user_agents[rand_index]


class NEXT:

    def __init__(self):
        self.session = requests.Session()
        self.main_url = "https://www.next.co.uk"

        self.data = []
        self.MAX_THREADS = 24
        self.category_name = ""
        self.sub_category_name = ""
        self.sub_sub_category_name = ""
        self.output_file_path = "data/output.json"

    def parse(self):
        soup = self.get_request(self.main_url)
        categories = soup.findAll('li', class_='Primarynavlinks')
        for category in categories:
            self.category_name = category.text

            if self.category_name not in ['SALE', 'HOME', 'BRANDS', 'SPORTS', 'GIFTS & FLOWERS']:
                self.get_categories(self.main_url + category.find('a')['href'])

    def get_categories(self, url):
        soup = self.get_request(url)
        sub_categories = soup.find('div', id='collapseSidebarLinks').findAll('div',
                                                                             class_='sidebar-sec col-sm-12 col-md-3 col-lg-12')
        for sub_category in sub_categories:
            self.sub_category_name = sub_category.find('label').text

            a_tags = sub_category.findAll('a')
            for a_tag in a_tags:
                self.sub_sub_category_name = a_tag.text
                link = self.main_url + a_tag['href']

                print("Scraping stared", self.category_name, self.sub_category_name, self.sub_sub_category_name, link)
                start_time = time.time()
                self.get_product_listing_links(link)
                print("--- %s seconds ---" % (time.time() - start_time))
                print("Scraping completed", self.category_name, self.sub_category_name, self.sub_sub_category_name,
                      link)

    def get_product_listing_links(self, url):
        next_products = 24
        first = True
        while True:
            try:
                if first:
                    soup = self.get_request(url)
                    first = False
                else:
                    link = url + "/isort-score-minprice-0-maxprice-100000-srt-{0}".format(next_products)
                    soup = self.get_request(link)

                a_tags = soup.findAll('a', class_='TitleText')

                links = [a_tag['href'] if 'https' in a_tag['href'] else 'https:' + a_tag['href'] for a_tag in a_tags]

                if len(links) < 1:
                    break
                else:
                    threads = min(self.MAX_THREADS, len(links))
                    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
                        executor.map(self.get_product_info, links)
                    self.save_data()

                next_products += 24
            except:
                break

    def get_product_info(self, link):
        soup = self.get_request(link)

        product_data = dict()

        try:
            product_data["productName"] = soup.find('div', class_='Title').text.strip()
        except:
            product_data["productName"] = ""

        try:
            product_data["price"] = soup.find('div', class_='nowPrice').text.strip()
        except:
            product_data["price"] = ""

        try:
            product_data["productNumber"] = soup.find('div', class_='ItemNumber').text
        except:
            product_data["productNumber"] = ""

        product_data["categoryName"] = self.category_name
        product_data["subCategoryName"] = self.sub_category_name
        product_data["subSubCategoryName"] = self.sub_sub_category_name

        try:
            product_data["rating"] = soup.find('b', class_='rating').text
        except:
            product_data["rating"] = ""

        try:
            product_data["reviews"] = soup.find('span', class_='basedOn').text
        except:
            product_data["reviews"] = ""

        try:
            product_data["colors"] = soup.find('select', class_='colourList').getText(separator=u' ').strip().replace(
                '\n', ',').split(',')
        except:
            product_data["colors"] = []

        try:
            product_data["fits"] = [li.text.strip() for li in soup.find('ul', class_='fitChips').findAll('li')]
        except:
            product_data["fits"] = []

        try:
            product_data["sizes"] = [(size.text, size['data-stockstatus']) for size in
                                     soup.find('select', class_='SizeSelector').findAll('option')[1:]]
        except:
            product_data["sizes"] = []

        try:
            product_data["description"] = soup.find('div', id='ToneOfVoice').text
        except:
            product_data["description"] = ""

        image_cdn = 'https://xcdn.next.co.uk/COMMON/Items/Default/Default/Publications/G68/shotview/63/'
        images = []
        try:
            for i in soup.find('div', class_='ThumbNailNavClip').findAll('img'):
                try:
                    src = i['src']
                    if 'placeholder' not in src:
                        if '-' not in src:
                            images.append(image_cdn + src.split('/')[-1][:3] + '-' + src.split('/')[-1][3:])
                        else:
                            images.append(image_cdn + src.split('/')[-1])
                except:
                    'images'
        except:
            pass

        product_data["images"] = images

        product_data['url'] = link

        self.data.append(product_data)

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

    def get_request(self, link):
        self.session.headers.update({'User-Agent': get_random_useragent()})
        response = self.session.get(link)
        time.sleep(random.randint(1, 2))

        soup = bs(response.text, 'lxml')

        return soup


next_ = NEXT()
next_.parse()
