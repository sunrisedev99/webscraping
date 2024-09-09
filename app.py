from bs4 import BeautifulSoup # type: ignore
import requests # type: ignore
import csv
import cloudscraper # type: ignore
import re
import os
from concurrent.futures import ThreadPoolExecutor

max_workers = os.cpu_count()

domain = "Your domain"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

session = requests.session()
# session = HTMLSession()
scraper = cloudscraper.create_scraper(
    interpreter="nodejs",
    delay=10,
    browser={
        'browser': 'firefox',
        'platform': 'windows',
        'mobile': False
    },
    sess=session
)


def listToString(s):
    str1 = ""
    index = 0
    for ele in s:
        index += 1
        if index > 1:
            str1 += " "
        str1 += ele
    return str1

def isnumber(value):
    if isinstance(value, (int, float, complex)):
        return True
    try:
        float(value)
        return True
    except ValueError:
        return False

def extract_substring(value):
    result = ''
    for char in value:
        if char.isdigit() or char == '+' or char == '.':  # Consider digits and '+'
            result += char
        else:
            break  # Stop once a non-numeric character (except '+') is found
    return result

def extract_number_only(value):
    result = ''
    for char in value:
        if char.isdigit() or char == '.':  # Consider digits and '+'
            result += char
        else:
            break  # Stop once a non-numeric character (except '+') is found
    return result



def fetch_url(row):
    print('url:  ', row[1])
    res = scraper.get(row[1], headers=headers)
    res.raise_for_status()  # Check for HTTP errors
    soup = BeautifulSoup(res.text, 'html.parser')

    if res.status_code == 200:
        data_item = {
            "category": row[0],
            "upc": "",   # just string with numbers
            "name": "",
            "model": "",
            "caliber": "",
            "weight": "",   # number weight in oz
            "barrel_length": "",   # number in inch
            "overall_length": "",   # number in inch
            "capacity": "",   # ex. "magazine chamber"
            "action": "",
            "material": "",
            "finish": "",
            "sight_type": "",
            "safety_features": "",
            "product_description": "",
            "color": "",
            "gauge": "",
            "frame_size": "",
            "stock_material": "",
            "stock_type": "",
            "magazines_included": "",  #  integer count of included magazines
            "raw_data": "",
            "brand": "",   # {data: {"name": ""}}
            "state_compliance": [], # ex, {alaska:true, wosinton: false}
            "images": [],   # {"urls": [], "ids": [1234, 567]}
        }
        
        product_name = soup.find_all('span', class_="h5 pdp-info__title d-block")
        if product_name:
            data_item["name"] = product_name[len(product_name)-1].text.strip()

        product_brand = soup.find('span', class_="subtitle-2 font-weight-bolder d-block")
        if product_brand:
            data_item["brand"] = product_brand.get_text(strip=True)
        
        image_urls = soup.find_all('div', class_="swiper-slide pdp-slide__thumb-slide")
        if image_urls:
            for image_url in image_urls:
                image_url = image_url.find('img')
                if image_url:
                    data_item["images"].append(domain + image_url['src'])

        upc_data = soup.find('div', class_="pdp-info__attr")
        if upc_data:
            upc_data = upc_data.find('div', class_="pdp-info__attr-item pdp-info__attr-upc flex-center")
            if upc_data:
                upc = upc_data.find('div', class_="pdp-info__attr-value").get_text(strip=True)
                data_item["upc"] = upc
        

        if (data_item["upc"] != "" and data_item["name"] != ""):

            print("upc information:   ", row[1])

            paragraphs = soup.find('div', class_="pdp-tabs__content show-full")
            if paragraphs:
                description = paragraphs.find_all('div')
                if description:
                    description = "\n".join(paragraph.get_text(strip=True) for paragraph in description)
                    data_item["product_description"] = description
                else:
                    description = paragraphs.get_text(strip=True)
                    data_item["product_description"] = description


            # if len(data_item["images"]) == 0:
            #     data_item["images"].append(row[2])


            container = soup.find('div', class_='pdp-tabs__main')
            container = container.find_all('div', class_='pdp-tabs__content-item')
            if container:
                data_item["raw_data"] = container
                for item in container:
                    try:
                        name = item.find('div', class_="pdp-tabs__content-title").get_text(strip=True)
                        value = item.find('div', class_="pdp-tabs__content-value").get_text(strip=True)
                        print("(name, value) ===>   ", name, value)

                        if name == 'Model Name:':
                            data_item["model"] = value
                        elif name == 'Caliber':
                            data_item["caliber"] = value
                        elif name == 'Item Weight (lbs):':
                            data_item["weight"] = float(value) * 16
                        elif name == 'Barrel Length:':
                            data_item["barrel_length"] = value
                        elif name == 'Length':
                            data_item["overall_length"] = value
                        elif name == 'Magazine Capacity:':
                            data_item["capacity"] = value
                        # elif name == 'Cartridge Capacity:':
                        #     data_item["capacity"] = value
                        elif name == 'Action Type:':
                            data_item["action"] = value
                        elif name == 'Material':
                            data_item["material"] = value
                        elif name == 'Finish:':
                            data_item["finish"] = value
                        elif name == 'Front Sight Type:':
                            data_item["sight_type"] = value
                        elif name == 'Safety':
                            data_item["safety_features"] = value
                        elif name == 'Color:':
                            data_item["color"] = value
                        elif name == 'Gauge':
                            data_item["gauge"] = value
                        elif name == 'frame_size':
                            data_item["frame_size"] = value
                        elif name == 'Stock Material:':
                            data_item["stock_material"] = value
                        elif name == 'Stock Style:':
                            data_item["stock_type"] = value
                        elif name == 'Magazine Included:':
                            data_item["magazines_included"] = value
                        elif name == 'state_compliance':
                            data_item["state_compliance"] = value

                    except Exception as e:
                        print(f'----> ERROR: ({name}, {value}) <----------------------------')


            # print("product:   ", data_item)
            writer.writerow([
                data_item["category"],
                data_item["upc"],
                data_item["name"],
                data_item["model"],
                data_item["caliber"],
                data_item["weight"],
                data_item["barrel_length"],
                data_item["overall_length"],
                data_item["capacity"],
                data_item["action"],
                data_item["material"],
                data_item["finish"],
                data_item["sight_type"],
                data_item["safety_features"],
                data_item["product_description"],
                data_item["color"],
                data_item["gauge"],
                data_item["frame_size"],
                data_item["stock_material"],
                data_item["stock_type"],
                data_item["magazines_included"],
                data_item["raw_data"],
                data_item["brand"],
                listToString(data_item["state_compliance"]),
                listToString(data_item["images"]),
                row[1]
            ])
        else:
            print("No UPC ============================> ", row[1])
    else:
        print("<============== Connection Error ==================>")

# categories = ['handguns', 'rifles', 'shotguns']
with open('./result/brownells_final.csv', mode='w', encoding='utf-8', newline='', errors='replace') as file:
    writer = csv.writer(file)
    csv_headers = [
        "category",
        "upc",
        "name",
        "model",
        "caliber",
        "weight",
        "barrel_length",
        "overall_length",
        "capacity",
        "action",
        "material",
        "finish",
        "sight_type",
        "safety_features",
        "product_description",
        "color",
        "gauge",
        "frame_size",
        "stock_material",
        "stock_type",
        "magazines_included",
        "raw_data",
        "brand",
        "state_compliance",
        "images",
        "url"
    ]
    writer.writerow(csv_headers)
    
    with open('brownells.csv', mode='r', newline='', encoding='utf-8', errors='replace') as file:
        csv_reader = csv.reader(file)   # Create a CSV reader object
        
        print('max_workers:   ', max_workers)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(fetch_url, csv_reader)

     

print("Completed successfully")