import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from openai import OpenAI
import json
import requests

# import requests

SBR_WS_CDP = 'wss://brd-customer-hl_dc842eb8-zone-real_estate_browser:zfd36w1amt2d@brd.superproxy.io:9222'
BASE_URL = "https://zoopla.co.uk"
LOCATION = "London"
API_KEY =  "AIzaSyD7_v-68hNwRucbiUnhQ6OdRKu66wrMbys"


client = OpenAI(
    api_key="sk-proj-WDkFvM4XYnDpQXmHNwpGT3BlbkFJcmCCKMu8sUfeiXFRwFfQ")


def extract_picture(picture_sections):
    picture_sources = []
    for picture in picture_sections.find_all('picture'):
        for source in picture.find_all('source'):
            source_type = source.get('type', '').split('/')[-1]
            pic_url = source.get('srcset', '').split(',')[0].split(' ')[0]

            if source_type == 'webp' and '1024' in pic_url:
                picture_sources.append(pic_url)
    return picture_sources


# def extract_property_details(input):
#     print("Extracting property details....")
#     command = """
#         You are a data extractor model and you have been tasked with extracting information about the apartment for me into json
#         Here is the div for the property details:
        
#         {input_command}
#         {{
#             "price": "",
#             "address": "",
#             "bedrooms": "",
#             "bathrooms": "",
#             "receptions": "",
#             "EPC Rating": "",
#             "tenure": "",
#             "time_remaining_on_lease": ""
#             "service_charge":""
#             "countil_tax_band": "",
#             "ground_rent": ""
#         }}
#     """.format(input_command = input)
    
#     response = client.chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages= [
#             {
#                 "role": "user",
#                 "content": command
#             }
#         ]
#     )
#     res = response.choices[0].message.content
#     json_data = json.loads(res)
#     return json_data


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

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        res = response.json()
        # extracted_data = json.loads(res['candidates'][0]['content'])
        res = res['candidates'][0]['content']
        json_string = res['parts'][0]['text']
        json_string = json_string.replace('```json\n', '').replace('\n```', '')
        extracted_data = json.loads(json_string)
        return extracted_data
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
    
    
    
    
async def run(pw):
    print('Connecting to Scraping Browser...')
    browser = await pw.chromium.connect_over_cdp(SBR_WS_CDP)
    try:
        page = await browser.new_page()
        print(f'Connected! Navigating to {BASE_URL}...')
        await page.goto(BASE_URL)

        # enter London to search bar
        await page.fill('input[name="autosuggest-input"]', LOCATION)
        await page.keyboard.press("Enter")
        print("Waiting for results....")
        await page.wait_for_load_state("load")

        content = await page.inner_html('div[data-testid="regular-listings"]')
        soup = BeautifulSoup(content, 'html.parser')

        items = soup.findAll("div", class_="dkr2t83")

        for idx, div in enumerate(items):

            data = {}

            data.update(
                {'address': div.find("address").text,
                 'title': div.find("h2").text,
                 'link': BASE_URL+div.find("a")['href']}
            )

            # Get data in detail
            print(f"Navigating to the listing page... {data['link']}")
            await page.goto(data['link'])
            await page.wait_for_load_state("load")

            content = await page.inner_html('div[data-testid="listing-details-page"]')
            soup = BeautifulSoup(content, 'html.parser')

            picture_section = soup.find(
                'section', {'aria-labelledby': 'listing-gallery-heading'})
            pictures = extract_picture(picture_section)
            data['pictures'] = pictures

            # extract detail
            property_details = soup.select_one('div[class="_14bi3x331"]')
            property_details = extract_property_details(property_details)

            floor_plan = extract_floor_plan(soup)
            
            data.update(property_details)
            data.update(floor_plan)
            print(data)
            break

        # CAPTCHA handling: If you're expecting a CAPTCHA on the target page, use the following code snippet to check the status of Scraping Browser's automatic CAPTCHA solver
        # client = await page.context.new_cdp_session(page)
        # print('Waiting captcha to solve...')
        # solve_res = await client.send('Captcha.waitForSolve', {
        #     'detectTimeout': 10000,
        # })
        # print('Captcha solve status:', solve_res['status'])
        print('Navigated! Scraping page content...')
        # html = await page.content()
        # print(html)
    finally:
        await browser.close()


async def main():
    async with async_playwright() as playwright:
        await run(playwright)


if __name__ == '__main__':
    asyncio.run(main())
