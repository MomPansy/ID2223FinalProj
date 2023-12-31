import aiohttp
import asyncio
import pandas as pd
from bs4 import BeautifulSoup
import re 
from datetime import datetime
from gcloud_utils import gcloud_helper
from flask import request
import csv

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

    return statement, inner_link, date, source, label

def write_data_to_csv(data, file_name, mode='a'):
    """
    Write data directly to a CSV file without using Pandas.

    :param data: List of tuples or list of lists containing the data.
    :param file_name: Name of the CSV file.
    :param mode: File open mode ('w' for write, 'a' for append).
    """
    with open(file_name, mode, newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if mode == 'w':  # Write header only if it's a new file
            writer.writerow(['statement', 'link', 'date', 'source', 'label'])
        writer.writerows(data)
import asyncio
from datetime import datetime
import csv

# Ensure all your previously defined functions are imported or included here

async def main():
    url = 'https://www.politifact.com/factchecks/list'
    today = datetime.now().strftime('%Y-%m-%d')
    daily_file_name = f'scraped_data_{today}.csv'
    historical_data_file_name = 'data_full.csv'  # Name of the historical data file on Google Drive

    try:
        print("Starting data collection for the first page")
        data = await parse_main_page(url)
        
        # Write the scraped data to a daily CSV file
        write_data_to_csv(data, daily_file_name, mode='w')
        print(f"Data collection complete. Data saved in file: {daily_file_name}")

        # Read the daily file's content to prepare for concatenation
        with open(daily_file_name, 'r', newline='', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            daily_data = list(csv_reader)  # Convert to list of lists (each row is a list)

        # Call the function to concatenate and save to Google Drive
        gcloud_helper.cloud_function_entry_point(daily_data, historical_data_file_name)

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
    df = asyncio.run(main())
    gcloud_helper.cloud_function_entry_point(df)

    return 'Data collection and processing complete.'
