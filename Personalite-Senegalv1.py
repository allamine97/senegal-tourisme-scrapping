
#!/usr/bin/env python3
# coding: utf-8

import os
import re
import logging
from urllib.parse import urljoin

import requests
import psycopg
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

BASE_URL = "https://www.jesuismort.com"
SOURCE_URL = (
    "https://www.jesuismort.com/cimetiere/"
    "senegalais-et-senegalaise"
)

# --------------------------------------------------
# PostgreSQL connection
# --------------------------------------------------

def get_connection():
    """Create a PostgreSQL connection using environment variables."""
    return psycopg.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=os.getenv("PG_PORT", "5432"),
        dbname=os.getenv("PG_DATABASE", "senegal"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", "passer1234")
    )


# --------------------------------------------------
# HTTP session
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
# Personality scraper
# --------------------------------------------------

class PersonnalityData:

    def __init__(self):
        self.soup = BeautifulSoup(
            fetch_html(SOURCE_URL),
            "html.parser",
        )
        self.base_url = BASE_URL

    @staticmethod
    def clean_li_data(element):
        text = re.sub(r"\s+", " ", element.get_text(" ", strip=True))
        return text.split(":")[-1].strip()

    def get_data(self):
        list_data = []

        links = self.soup.find_all(
            "a",
            class_="linkCelebrity",
        )

        logging.info("Found %d personality links.", len(links))

        for link in links:
            href = link.get("href")

            if not href:
                continue

            url = urljoin(self.base_url, href)

            try:
                data = self.get_info(url)

                if data:
                    list_data.append(data)

            except (
                requests.RequestException,
                AttributeError,
                IndexError,
                TypeError,
            ) as exc:
                logging.warning(
                    "Skipping personality page %s: %s",
                    url,
                    exc,
                )

        return list_data

    def get_info(self, url):
        soup = BeautifulSoup(fetch_html(url), "html.parser")

        name_element = soup.find(id="page_h1")
        description_element = soup.find(
            "div",
            class_="iconBlock",
        )
        biography_element = soup.find(id="biographie")
        photo_element = soup.find("img", class_="photo")

        if name_element is None:
            logging.warning("Missing personality name on %s", url)
            return None

        nom = name_element.get_text(" ", strip=True)

        description = (
            description_element.get_text(" ", strip=True)
            if description_element else ""
        )

        biographie = (
            biography_element.get_text(" ", strip=True)
            if biography_element else ""
        )
        biographie = re.sub(r"\s+", " ", biographie)

        url_photo = (
            urljoin(self.base_url, photo_element.get("src", ""))
            if photo_element else ""
        )

        identities = soup.find_all(
            "div",
            class_="tombStart_infoList",
        )

        domaine = ""
        date_naissance = ""
        date_deces = ""

        # Preserve the source script's field positions,
        # while avoiding crashes on incomplete pages.
        if len(identities) > 1:
            activity_items = identities[1].find_all("li")
            if activity_items:
                domaine = self.clean_li_data(activity_items[-1])

        if len(identities) > 3:
            birth_items = identities[3].find_all("li")
            if birth_items:
                date_naissance = self.clean_li_data(birth_items[0])

        if len(identities) > 4:
            death_items = identities[4].find_all("li")
            if death_items:
                date_deces = self.clean_li_data(death_items[0])

        return {
            "nom": nom,
            "domaine": domaine,
            "description": description,
            "biographie": biographie,
            "date_naissance": date_naissance,
            "date_deces": date_deces,
            "url_photo": url_photo,
        }


# --------------------------------------------------
# Save scraped records to PostgreSQL
# --------------------------------------------------

def save_persons(data):
    if not data:
        logging.warning("No personality records to insert.")
        return

    sql = """
        INSERT INTO persons (
            nom,
            domaine,
            description,
            biographie,
            date_naissance,
            date_deces,
            url_photo
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    values = [
        (
            person["nom"],
            person["domaine"],
            person["description"],
            person["biographie"],
            person["date_naissance"],
            person["date_deces"],
            person["url_photo"],
        )
        for person in data
    ]

    # One transaction for the batch.
    # If an insert fails, the batch is rolled back.
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(sql, values)

    logging.info(
        "Successfully inserted %d personality records.",
        len(values),
    )


# --------------------------------------------------
# Main application
# --------------------------------------------------

def main():
    try:
        data = PersonnalityData().get_data()

        logging.info(
            "Successfully scraped %d personality records.",
            len(data),
        )

        save_persons(data)

    except requests.RequestException:
        logging.exception("Unable to fetch the source website.")

    except psycopg.Error:
        logging.exception("PostgreSQL operation failed.")
        raise


if __name__ == "__main__":
    main()
