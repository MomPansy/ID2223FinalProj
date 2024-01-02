import aiohttp
import asyncio
import pandas as pd
from bs4 import BeautifulSoup
import re 
from datetime import datetime
from flask import request
import csv
import hopsworks

async def fetch_page(session, url):
    print(f"Fetching URL: {url}")
    async with session.get(url) as response:
        return await response.text()

async def parse_main_page(url):
    async with aiohttp.ClientSession() as session:
        print(f"Processing main page: {url}")
        main_page_content = await fetch_page(session, url)
        soup = BeautifulSoup(main_page_content, 'html.parser')
        links = soup.find_all('li', attrs={'class': 'o-listicle__item'})
        print(f"Found {len(links)} links to process")
        tasks = [parse_inner_page(session, link) for link in links]
        return await asyncio.gather(*tasks)

async def parse_inner_page(session, link_element):
    base_link = "https://www.politifact.com"
    inner_link = base_link + link_element.find("div", attrs={'class': 'm-statement__quote'}).find('a')['href'].strip()
    print(f"Processing inner link: {inner_link}")
    inner_page_content = await fetch_page(session, inner_link)
    inner_soup = BeautifulSoup(inner_page_content, 'html.parser')

    try:
        statement_tag = inner_soup.find("div", attrs={'class': 'm-statement__quote'})
        print("Statement tag found:", statement_tag is not None)
        statement = statement_tag.text.strip() if statement_tag else 'N/A'

        date_element = inner_soup.find('div', attrs={'class': 'm-statement__desc'})
        print("Date element found:", date_element is not None)
        if date_element:
            date_match = re.search(r"(\w+\s\d{1,2},\s\d{4})", date_element.text)
            if date_match:
                date_str = date_match.group(1)
                # Parse the date string into a datetime object
                date_obj = datetime.strptime(date_str, '%B %d, %Y')
                # Format the date as YYYY-MM-DD
                date = date_obj.strftime('%Y-%m-%d')
            else:
                date = 'N/A'
        else:
            date = 'N/A'
        print(date)
        source_tag = inner_soup.find('div', attrs={'class': 'm-statement__meta'}).find('a')
        print("Source tag found:", source_tag is not None)
        source = source_tag.text.strip() if source_tag else 'N/A'

        label_tag = inner_soup.find('div', attrs={'class': 'm-statement__content'}).find('img',
                                                                                        attrs={
                                                                                            'class': 'c-image__original'})
        print("Label tag found:", label_tag is not None)
        label = label_tag.get('alt').strip() if label_tag else 'N/A'
        
    except Exception as e:
        print(f"Error processing inner link {inner_link}: {e}")
        return 'N/A', inner_link, 'N/A', 'N/A', 'N/A'

    return (statement, inner_link, date, source, label)

async def main():
    project = hopsworks.login()
    fs = project.get_feature_store()

    fg = fs.get_feature_group(name="finalproj",version=1)
    url = 'https://www.politifact.com/factchecks/list'

    try:
        print("Starting data collection for the first page")
        data = await parse_main_page(url)
        df = pd.DataFrame(data, columns = ['statement', 'inner_link', 'date', 'source', 'label'])
        fg.insert(df)

    except Exception as e:
        print('Error occurred:', e)

    print("Process completed.")

def scrape_politifact(request):
    """
    This function is triggered by HTTP request.
    """
    request_json = request.get_json(silent=True)
    request_args = request.args

    # Run the main async function
    asyncio.run(main())

    return 'Data collection and processing complete.'
