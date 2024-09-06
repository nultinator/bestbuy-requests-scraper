import os
import csv
import requests
import json
import logging
from urllib.parse import urlencode
from bs4 import BeautifulSoup
import concurrent.futures
from dataclasses import dataclass, field, fields, asdict

API_KEY = ""

with open("config.json", "r") as config_file:
    config = json.load(config_file)
    API_KEY = config["api_key"]


## Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scrape_search_results(keyword, location, retries=3):
    formatted_keyword = keyword.replace(" ", "+")
    url = f"https://www.bestbuy.com/site/searchpage.jsp?st={formatted_keyword}"
    tries = 0
    success = False
    
    while tries <= retries and not success:
        try:
            response = requests.get(url)
            logger.info(f"Recieved [{response.status_code}] from: {url}")
            if response.status_code != 200:
                raise Exception(f"Failed request, Status Code {response.status_code}")
                
            soup = BeautifulSoup(response.text, "html.parser")            
            div_cards = soup.find_all("div", class_="shop-sku-list-item")

            for div_card in div_cards:
                sponsored = False
                sponsored_tag = div_card.find("div", class_="is-sponsored")
                if sponsored_tag:
                    sponsored = True

                name = div_card.find("h4", class_="sku-title").text
                price_holder = div_card.select_one("div[data-testid='customer-price']")
                price = price_holder.select_one("span[aria-hidden='true']").text
                model_holder = div_card.find("div", class_="sku-model")
                model_info_array = model_holder.find_all("span", class_="sku-value")
                model_number = model_info_array[0].text
                sku_number = model_info_array[1].text
                rating_holder = div_card.find("div", class_="ratings-reviews")
                href = rating_holder.find("a")
                link = "n/a"
                if href:
                    link = f"https://www.bestbuy.com{href.get('href')}"
                    
                rating_text = rating_holder.find("p", class_="visually-hidden").text
                rating = 0.0
                if rating_text != "Not Yet Reviewed":
                    rating = rating_text.split(" ")[1]

                search_data = {
                    "name": name,
                    "url": link,
                    "price": price,
                    "model_number": model_number,
                    "sku": sku_number,
                    "rating": rating,
                    "spoonsored": sponsored
                }
                print(search_data)
                
            logger.info(f"Successfully parsed data from: {url}")
            success = True
        
                    
        except Exception as e:
            logger.error(f"An error occurred while processing page {url}: {e}, retries left {retries-tries}")
            tries+=1

    if not success:
        raise Exception(f"Max Retries exceeded: {retries}")


if __name__ == "__main__":

    MAX_RETRIES = 3
    MAX_THREADS = 5
    PAGES = 1
    LOCATION = "us"

    logger.info(f"Crawl starting...")

    ## INPUT ---> List of keywords to scrape
    keyword_list = ["gpu"]
    aggregate_files = []

    ## Job Processes
    for keyword in keyword_list:
        scrape_search_results(keyword, LOCATION, retries=MAX_RETRIES)
        
    logger.info(f"Crawl complete.")