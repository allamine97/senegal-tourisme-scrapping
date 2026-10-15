
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging

import psycopg
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

URL_CIBLE = (
    "https://www.google.com/travel/things-to-do/see-all"
    "?g2lb=2502548%2C4258168%2C4270442%2C4271060%2C4306835"
    "%2C4308226%2C4317915%2C4322823%2C4328159%2C4344615"
    "%2C4371334%2C4401769%2C4419364%2C4433754%2C4437439"
    "%2C4444000%2C4447566%2C4270859%2C4284970%2C4291517"
    "%2C4412693&hl=fr-BJ&gl=bj&un=1&dest_mid=%2Fm%2F06srk"
    "&dest_state_type=sattd&dest_src=ts&sa=X"
    "#ttdm=14.679927_-17.319260_10&ttdmf=%252Fm%252F04mn6q"
)

session = requests.Session()
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
})


def get_connection():
    """Create a PostgreSQL connection using environment variables."""
    return psycopg.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=os.getenv("PG_PORT", "5432"),
        dbname=os.getenv("PG_DATABASE", "senegal"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", "passer1234")
    )


def get_site_data(elm_site):
    """Extract the name, rating, description and photo URL."""

    name_element = elm_site.find("div", class_="skFvHc")
    rating_element = elm_site.find("span", class_="KFi5wf")
    description_element = elm_site.find("div", class_="nFoFM")
    image_element = elm_site.find("img", class_="R1Ybne YH2pd")

    nom = name_element.get_text(strip=True) if name_element else ""
    note_text = (
        rating_element.get_text(strip=True)
        if rating_element else ""
    )
    description = (
        description_element.get_text(" ", strip=True)
        if description_element else ""
    )

    # Google may use a decimal comma, such as "4,4".
    note = None
    if note_text:
        try:
            note = float(note_text.replace(",", "."))
        except ValueError:
            logging.warning(
                "Could not convert rating %r for %r",
                note_text, nom
            )

    # Google may place the image URL in different attributes.
    url_photo = ""
    if image_element:
        url_photo = (
            image_element.get("data-src")
            or image_element.get("src")
            or ""
        )

    return {
        "nom": nom,
        "note": note,
        "description": description,
        "url_photo": url_photo
    }


def get_all_site_data(soup):
    """Extract all tourism-site cards from the HTML."""
    data = []
    site_elements = soup.find_all("div", class_="Ld2paf")

    for element in site_elements:
        site = get_site_data(element)

        # Ignore cards without a usable name.
        if site["nom"]:
            data.append(site)

    return data


def scrape_sites():
    """Download the page and scrape the tourism sites."""
    response = session.get(URL_CIBLE, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    sites = get_all_site_data(soup)

    if not sites:
        logging.warning(
            "No tourism sites were found. "
            "Google may have changed the page structure, "
            "or the results may require JavaScript."
        )

    logging.info("Number of sites extracted: %d", len(sites))
    return sites


def save_sites(sites):
    """Insert scraped tourism sites into PostgreSQL."""
    if not sites:
        logging.warning("No data to insert.")
        return

    sql = """
        INSERT INTO sites (nom, note, description, url_photo)
        VALUES (%s, %s, %s, %s)
    """

    values = [
        (
            site["nom"],
            site["note"],
            site["description"],
            site["url_photo"]
        )
        for site in sites
    ]

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(sql, values)

    logging.info("Inserted %d sites into PostgreSQL.", len(values))


def main():
    try:
        sites = scrape_sites()

        # Display the extracted records for verification.
        for site in sites:
            print(site)

        save_sites(sites)

    except requests.RequestException as error:
        logging.error("HTTP request failed: %s", error)
    except psycopg.Error as error:
        logging.error("PostgreSQL operation failed: %s", error)
    except Exception:
        logging.exception("Unexpected error occurred.")


if __name__ == "__main__":
    main()
