import asyncio
import random
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
# from openai import OpenAI
import json
import requests
from kafka import KafkaProducer
from datetime import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.common.proxy import *
# import undetected_chromedriver as uc
import seleniumwire.undetected_chromedriver as uc


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
    print("Extracting property details....")
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
    print("Extracting floor plan....")
    plan = {}
    floor_plan = soup.find("div", {"data-testid": "floorplan-thumbnail-0"})
    if floor_plan:
        floor_plan_src = floor_plan.find("picture").find("source")['srcset']
        plan["floor plan"] = floor_plan_src.split(' ')[0]
    return plan


# async def run(pw, producer):
#     print('Connecting to Scraping Browser...')
#     # browser = await pw.chromium.connect_over_cdp(SBR_WS_CDP)
#     # browser = await pw.webkit.launch()
#     # browser = await pw.chromium.launch()
#     # browser = await pw.firefox.launch()
#     browser =await pw.chromium.launch(headless=True)  # Chạy ở chế độ nền
#     context =await browser.new_context(
#         user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
#         accept_downloads=True,
#         javascript_enabled=False,
#         # ignore_https_errors=True,
#         # bypass_csp=True,
#     )

#     try:
#         # page = await browser.new_page()
#         page =await context.new_page()

#         print(f'Connected! Navigating to {BASE_URL}...')
#         await page.goto(BASE_URL)
#         await page.wait_for_load_state('load')

#         # enter London to search bar
#         await page.fill('input[name="autosuggest-input"]', LOCATION, timeout=60000)
#         await page.keyboard.press("Enter")
#         print("Waiting for results....")
#         await page.wait_for_load_state("load")
#         await page.wait_for_load_state('networkidle')

#         with open(f"test_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.html", "w", encoding="utf-8") as f:
#             f.write(await page.content())

#         content = await page.inner_html('div[data-testid="regular-listings"]')

#         soup = BeautifulSoup(content, 'html.parser')
#         # soup = soup.find("div", {"data-testid": "regular-listings"})

#         items = soup.findAll("div", class_="dkr2t83")

#         for idx, div in enumerate(items):

#             data = {}

#             data.update(
#                 {'address': div.find("address").text,
#                  'title': div.find("h2").text,
#                  'link': BASE_URL+div.find("a")['href']}
#             )

#             # Get data in detail
#             print(f"Navigating to the listing page... {data['link']}")
#             await page.goto(data['link'])
#             await page.wait_for_load_state("load")

#             content = await page.inner_html('div[data-testid="listing-details-page"]')
#             soup = BeautifulSoup(content, 'html.parser')

#             picture_section = soup.find(
#                 'section', {'aria-labelledby': 'listing-gallery-heading'})
#             pictures = extract_picture(picture_section)
#             data['pictures'] = pictures

#             # extract detail
#             property_details = soup.select_one('div[class="_14bi3x331"]')
#             property_details = extract_property_details(property_details)

#             floor_plan = extract_floor_plan(soup)

#             data.update(property_details)
#             data.update(floor_plan)

#             print(data)
#             break

#             # print("Sending data to kafka...")
#             # producer.send("properties", value=json.dumps(data).encode('utf-8'))
#             # print("Data sent to kafka!")

#             # break

#         # CAPTCHA handling: If you're expecting a CAPTCHA on the target page, use the following code snippet to check the status of Scraping Browser's automatic CAPTCHA solver
#         # client = await page.context.new_cdp_session(page)
#         # print('Waiting captcha to solve...')
#         # solve_res = await client.send('Captcha.waitForSolve', {
#         #     'detectTimeout': 10000,
#         # })
#         # print('Captcha solve status:', solve_res['status'])
#         print('Navigated! Scraping page content...')
#         # html = await page.content()
#         # print(html)
#     finally:
#         await browser.close()


async def run(producer):

    ## Set chrome Options
    chrome_options = uc.ChromeOptions()

    ## Disable loading images for faster crawling
    options.add_argument('--blink-settings=imagesEnabled=false')

    # Tùy chọn cho Chrome
    options = Options()
    # options.add_argument("--headless=new")  # Chạy Chrome ở chế độ nền (headless)
    # options.add_argument("--enable-javascript")

    # myProxy = "149.215.113.110:70"
    # proxy = Proxy({
    #     'proxyType': ProxyType.MANUAL,
    #     'httpProxy': myProxy,
    #     'sslProxy': myProxy,
    #     'noProxy': ''})
    # options.proxy = proxy

    # Khởi tạo trình duyệt Chrome
    driver = webdriver.Chrome(options=options)

    try:
        print(f"Navigating to {BASE_URL}")
        # Truy cập URL
        driver.get(
            "https://www.zoopla.co.uk/for-sale/property/london/?q=London&results_sort=newest_listings&search_source=home")

        # Chờ Cloudflare hoàn thành thử thách (điều chỉnh thời gian chờ nếu cần)
        driver.implicitly_wait(60)

        # time.sleep(10)

        # Lấy HTML sau khi vượt qua Cloudflare
        html = driver.page_source

        with open(f"zoopla_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.html", "w", encoding="utf-8") as f:
            f.write(html)

        soup = BeautifulSoup(html, 'html.parser')
        soup = soup.find("div", {"data-testid": "regular-listings"})

        items = soup.findAll("div", class_="dkr2t83")

        for idx, div in enumerate(items):

            data = {}

            data.update(
                {'address': div.find("address").text,
                 'title': div.find("h2").text,
                 'link': BASE_URL+div.find("a")['href']}
            )

            print(data)

            # # Get data in detail
            # print(f"Navigating to the listing page... {data['link']}")
            # driver.get(data['link'])
            # # await page.wait_for_load_state("load")
            # driver.implicitly_wait(30)

            # content = driver.find_element(By.CSS_SELECTOR, "div[data-testid='listing-details-page']")
            # soup = BeautifulSoup(content, 'html.parser')

            # picture_section = soup.find(
            #     'section', {'aria-labelledby': 'listing-gallery-heading'})
            # pictures = extract_picture(picture_section)
            # data['pictures'] = pictures

            # # extract detail
            # property_details = soup.select_one('div[class="_14bi3x331"]')
            # property_details = extract_property_details(property_details)

            # floor_plan = extract_floor_plan(soup)

            # data.update(property_details)
            # data.update(floor_plan)

            # print(data)
            # break

        print('Navigated! Scraping page content...')

    finally:
        driver.quit()


async def main():
    # producer = KafkaProducer(bootstrap_servers=["localhost:9092"], max_block_ms=5000)
    producer = "None"
    # async with async_playwright() as playwright:
    #     await run(playwright, producer)
    await run(producer)


if __name__ == '__main__':
    asyncio.run(main())
