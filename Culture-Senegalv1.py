
#!/usr/bin/env python3
# coding: utf-8

import os
import re
import logging
import requests
import psycopg

from bs4 import BeautifulSoup, NavigableString
from dotenv import load_dotenv

from psycopg.rows import dict_row

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

# --------------------------------------------------
# PostgreSQL connection
# --------------------------------------------------

def get_connection():
    return psycopg.connect(
        host=os.environ["PG_HOST"],
        port=int(os.getenv("PG_PORT", "5432")),
        dbname=os.environ["PG_DATABASE"],
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        connect_timeout=10,
    )


# --------------------------------------------------
# HTTP helper
# --------------------------------------------------

session = requests.Session()
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (compatible; SenegalCultureResearch/1.0)"
    )
})


def fetch_html(url):
    response = session.get(url, timeout=20)
    response.raise_for_status()
    return response.text


# --------------------------------------------------
# Ethnie scraper
# --------------------------------------------------

class EthnieData:

    def __init__(self):
        url = "https://www.axl.cefan.ulaval.ca/afrique/senegal.htm"

        self.soup = BeautifulSoup(fetch_html(url), "html.parser")
        self.data_type = "ETHNIE"

        self.description_template = (
            "L'ethnie {} compte une population d'environ {}, "
            "ce qui correspond à {} de la population nationale. "
            "Leur langue maternelle est le {}."
        )

    def get_data(self):
        list_data = []

        table = self.soup.find(id="table4")

        if table is None:
            logging.warning("Ethnie table #table4 was not found.")
            return list_data

        table_lines = table.find_all("tr")[1:-2]

        for line in table_lines:
            data = self.get_info(line)
            if data:
                list_data.append(data)

        return list_data

    def get_info(self, line):
        td_list = [
            re.sub(r"\s+", " ", element.get_text(" ", strip=True))
            for element in line.contents
            if not isinstance(element, NavigableString)
        ]

        # Preserve the original scraper's removal of the final cell.
        if len(td_list) < 5:
            return None

        td_list = td_list[:-1]

        if len(td_list) < 4:
            return None

        nom, population, pourcentage, langue = td_list[:4]

        description = self.description_template.format(
            nom, population, pourcentage, langue
        )

        return {
            "type": self.data_type,
            "url_photo": "",
            "nom": nom,
            "description": description,
        }


# --------------------------------------------------
# Google search scraper
# --------------------------------------------------

class GoogleCultureData:

    def __init__(self, url, data_type, card_class):
        self.soup = BeautifulSoup(fetch_html(url), "html.parser")
        self.data_type = data_type
        self.card_class = card_class

    def get_data(self):
        list_data = []

        cards = self.soup.find_all("a", class_=self.card_class)

        for card in cards:
            try:
                data = self.get_info(card)
                if data and data["nom"]:
                    list_data.append(data)
            except (requests.RequestException, AttributeError, TypeError) as exc:
                logging.warning(
                    "Skipping a %s result: %s", self.data_type, exc
                )

        return list_data

    def get_description(self, url):
        if not url:
            return ""

        if url.startswith("/"):
            url = "https://www.google.com" + url

        soup = BeautifulSoup(fetch_html(url), "html.parser")
        element = soup.find("div", attrs={"data-attrid": "description"})

        return element.get_text(" ", strip=True) if element else ""

    def get_info(self, card):
        image = card.find("img")
        url_photo = image.get("src", "") if image else ""

        names = card.find_all("div", class_="FozYP")
        nom = " ".join(
            element.get_text(" ", strip=True) for element in names
        ).strip()

        description = ""

        try:
            description = self.get_description(card.get("href", ""))
        except requests.RequestException as exc:
            logging.warning("Could not fetch description for %s: %s", nom, exc)

        return {
            "type": self.data_type,
            "url_photo": url_photo,
            "nom": nom,
            "description": description,
        }


# --------------------------------------------------
# Author scraper
# --------------------------------------------------

class AuteurData(GoogleCultureData):

    def __init__(self):
        url = (
            "https://www.google.com/search"
            "?q=s%C3%A9n%C3%A9gal+auteur"
        )
        super().__init__(url, "AUTEUR", "ct5Ked")


# --------------------------------------------------
# Singer scraper
# --------------------------------------------------

class ChanteurData(GoogleCultureData):

    def __init__(self):
        url = (
            "https://www.google.com/search"
            "?q=s%C3%A9n%C3%A9gal+chanteur"
        )
        super().__init__(url, "CHANTEUR", "BVG0Nb")


# --------------------------------------------------
# PostgreSQL insert
# --------------------------------------------------

def save_cultures(data):
    if not data:
        logging.info("No records to insert.")
        return

    sql = """
        INSERT INTO cultures (type, url_photo, nom, description)
        VALUES (%s, %s, %s, %s)
    """

    values = [
        (
            item["type"],
            item["url_photo"],
            item["nom"],
            item["description"],
        )
        for item in data
    ]

    # A single transaction for this batch.
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(sql, values)

    logging.info("Inserted %d records into cultures.", len(values))


# --------------------------------------------------
# Main application
# --------------------------------------------------

def main():
    culture_data = []

    scrapers = [
        ("authors", AuteurData),
        ("singers", ChanteurData),
        ("ethnic groups", EthnieData),
    ]

    for label, scraper_class in scrapers:
        try:
            records = scraper_class().get_data()
            culture_data.extend(records)
            logging.info("Scraped %d %s records.", len(records), label)
        except requests.RequestException as exc:
            logging.exception("Failed to scrape %s: %s", label, exc)

    if culture_data:
        save_cultures(culture_data)
    else:
        logging.warning("No culture data collected; nothing was inserted.")


if __name__ == "__main__":
    main()
