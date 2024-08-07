import asyncio
import random
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
import requests
from kafka import KafkaProducer
from datetime import time
from datetime import datetime
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By



# import requests

SBR_WS_CDP = 'wss://brd-customer-hl_dc842eb8-zone-real_estate_browser:zfd36w1amt2d@brd.superproxy.io:9222'
BASE_URL = "https://zoopla.co.uk"
LOCATION = "London"
API_KEY = "AIzaSyD7_v-68hNwRucbiUnhQ6OdRKu66wrMbys"


def extract_picture(picture_sections):
    picture_sources = []
    for picture in picture_sections.find_all('picture'):
        for source in picture.find_all('source'):
            source_type = source.get('type', '').split('/')[-1]
            pic_url = source.get('srcset', '').split(',')[0].split(' ')[0]

            if source_type == 'webp' and '1024' in pic_url:
                picture_sources.append(pic_url)
    return picture_sources


def extract_property_details(input):
    # print("Extracting property details....")
    prompt = f"""
        You are a data extractor model and you have been tasked with extracting information about the apartment for me into JSON.
        Here is the div for the property details:

        {input}

        Return a JSON object with the following format:
        {{
            "price": "",
            "address": "",
            "bedrooms": "",
            "bathrooms": "",
            "receptions": "",
            "EPC Rating": "",
            "tenure": "",
            "time_remaining_on_lease": "",
            "service_charge": "",
            "countil_tax_band": "",
            "ground_rent": ""
        }}
    """

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=" + API_KEY
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    retries = 3
    backoff_factor = 2

    for attempt in range(retries):
        response = requests.post(url, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            res = response.json()
            res = res['candidates'][0]['content']
            json_string = res['parts'][0]['text']
            json_string = json_string.replace(
                '```json\n', '').replace('\n```', '')
            extracted_data = json.loads(json_string)
            return extracted_data
        elif response.status_code == 503 and attempt < retries - 1:
            sleep_time = backoff_factor ** attempt
            print(f"Error: {response.status_code}. Retrying in {sleep_time} seconds...")
            time.sleep(sleep_time)
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None


def extract_floor_plan(soup):
    # print("Extracting floor plan....")
    plan = {}
    floor_plan = soup.find("div", {"data-testid": "floorplan-thumbnail-0"})
    if floor_plan:
        floor_plan_src = floor_plan.find("picture").find("source")['srcset']
        plan["floor plan"] = floor_plan_src.split(' ')[0]
    return plan


async def run(producer):
    # Set chrome options
    chrome_options = uc.ChromeOptions()
    
    # Disable loading images for faster crawling
    chrome_options.add_argument('--blink-settings=imagesEnabled=false')
    
    # Run Chrome in headless mode (detached)
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    # Use a realistic user-agent
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36')
    
    # Initialize undetected Chrome driver
    driver = uc.Chrome(options=chrome_options)
    
    try:
        print(f"Navigating to {BASE_URL}")
        # Access URL
        driver.get("https://www.zoopla.co.uk/for-sale/property/london/?q=London&results_sort=newest_listings&search_source=home")
        
        # Wait for Cloudflare to complete the challenge (adjust wait time if needed)
        driver.implicitly_wait(10)
        
        # Get HTML after passing Cloudflare
        html = driver.page_source
        
        
        soup = BeautifulSoup(html, 'html.parser')
        soup = soup.find("div", {"data-testid": "regular-listings"})
        
        items = soup.findAll("div", class_="dkr2t83")
        
        all_data = []
        for idx, div in enumerate(items):
            data = {}
            data.update(
                {'address': div.find("address").text,
                 'title': div.find("h2").text,
                 'link': BASE_URL + div.find("a")['href']}
            )
            
            
            # Introduce a delay to mimic human behavior
            time.sleep(random.uniform(1, 3))
            
            # Get data in detail
            print(f"Navigating to the details page... {data['link']}")
            driver.get(data['link'])
            driver.implicitly_wait(10)
            
            # Find the element using the CSS selector
            content = driver.find_element(By.CSS_SELECTOR, "div[data-testid='listing-details-page']")
            soup = BeautifulSoup(content.get_attribute('innerHTML'), 'html.parser')
            
            picture_section = soup.find('section', {'aria-labelledby': 'listing-gallery-heading'})
            pictures = extract_picture(picture_section)
            data['pictures'] = pictures
            
            # Extract detail
            property_details = soup.select_one('div[class="_14bi3x331"]')
            property_details = extract_property_details(property_details)
            
            floor_plan = extract_floor_plan(soup)
            
            data.update(property_details)
            data.update(floor_plan)

            # print("Sending data to kafka...")
            producer.send("properties", value=json.dumps(data).encode('utf-8'))

            all_data.append(data)

        print("Data sent to kafka!")
        # with open(f"zoopla_data_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.json", "w", encoding="utf-8") as f:
        #     json.dump(all_data, f, ensure_ascii=False, indent=4)
        
        print('Navigated! Scraping page content...')
    
    finally:
        print("Quitting driver...")
        driver.quit()


async def main():
    producer = KafkaProducer(bootstrap_servers=["localhost:9092"], max_block_ms=5000)
    # async with async_playwright() as playwright:
    #     await run(playwright, producer)
    await run(producer)


if __name__ == '__main__':
    asyncio.run(main())
