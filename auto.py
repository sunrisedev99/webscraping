from bs4 import BeautifulSoup
import requests
import csv
import cloudscraper
import os
from concurrent.futures import ThreadPoolExecutor


max_workers = os.cpu_count()
print('max_workers:   ', max_workers)

domain = "Your domain"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
}

session = requests.session()
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False
    },
    sess=session
)


def listToString(s):
    str1 = ""
    for ele in s:
        str1 += " " + ele
    return str1

def isnumber(value):
    if isinstance(value, (int, float, complex)):
        return True
    try:
        float(value)
        return True
    except ValueError:
        return False


def fetch_url(page_number):
    url = f"{domain}/guns/{category}/?page={page_number}&sort=AvgCustomerReview"
    print("url:   ", url)
    res = scraper.get(url, headers=headers)
    res.raise_for_status()  # Check for HTTP errors
    if res.status_code == 200:
        soup = BeautifulSoup(res.text, 'html.parser')

        products = soup.find_all('div', class_="category-slider__item pl-item col-xl-4 col-6")
        if products:
            print("discovered product count is ", len(products))
            for item in products:
                product_url = item.find('a', class_="category-slider__item__img")["href"]
                image_url = item.find('img')["src"]

                writer.writerow([ category, domain + product_url, domain + image_url ])
        else:
            print("products is not found!")


with open('brownells.csv', mode='w', encoding='utf-8', newline='', errors='replace') as file:
    writer = csv.writer(file)
    
    categories = [ "rifles", "handguns", "shotguns", "blackpowder" ]
    for category in categories:
        category_url = f"{domain}/guns/{category}/?sort=AvgCustomerReview"
        print(f'==========>  category_url: {category_url} <====================')
        response = scraper.get(category_url, headers=headers)
        if response.status_code == 200:
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')

            pages = soup.find('span', class_="pl-count desktop-show")
            pages = pages.find('span', class_="pl-count-totalcount")
            if pages:
                total = int(pages.text.strip())
                print('total:  ', total)
                per_page = 32
                cnt = (total + per_page - 1) // per_page
                # with ThreadPoolExecutor(max_workers=max_workers) as executor:
                #     executor.map(fetch_url, range(1, cnt, 1))
                fetch_url(cnt)
            else:
                print(f"Failed: there is no pages that you are looking")
        else:
            print(f"Failed: {response.status_code}")
