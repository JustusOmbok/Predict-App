from flask import Flask, render_template
import requests
import logging
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
import time
import random

# Configure logging
logging.basicConfig(level=logging.INFO)

# Suppress only the single InsecureRequestWarning from urllib3
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Initialize Flask app
app = Flask(__name__)

def setup_chrome_driver(headless=True):
    """Setup and return a Chrome WebDriver instance."""
    options = Options()
    options.add_argument("--headless" if headless else "--no-headless")
    options.add_argument("--ignore-certificate-errors")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def scrape_match_data(driver, url):
    """Scrape football match data from the provided URL."""
    driver.get(url)
    time.sleep(5)  # Wait for the page to load completely

    # Wait for a specific element to ensure the page is loaded
    try:
        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.CLASS_NAME, "adsclick")))
    except TimeoutException:
        logging.error("Page took too long to load.")
        return []

    page_source = driver.page_source
    print(page_source)
    bs_obj = BeautifulSoup(page_source, "lxml")

    matches = []
    countries = bs_obj.find_all("div", {"class": "event__title--type"})
    home_teams = bs_obj.find_all("div", {"class": "event__participant event__participant--home"})
    away_teams = bs_obj.find_all("div", {"class": "event__participant event__participant--away"})

    for country, home_team, away_team in zip(countries, home_teams, away_teams):
        matches.append({
            "country": country.text.strip(),
            "home_team": home_team.text.strip(),
            "away_team": away_team.text.strip()
        })

    return matches

def get_tarot_prediction():
    """Fetch and return a tarot card prediction."""
    url = "https://www.astrology.com/tarot/yes-no.html"
    driver = setup_chrome_driver(headless=False)  # Set headless to False for debugging

    try:
        driver.get(url)
        time.sleep(5)

        # Click on a random tarot card
        cards = driver.find_elements(By.CSS_SELECTOR, '.card')
        if cards:
            random.choice(cards).click()

        time.sleep(5)

        card_name = driver.find_element(By.CLASS_NAME, 'tarot-card-name').text.strip()
        result = driver.find_element(By.CLASS_NAME, 'yes-no-result').text.strip()
        description = driver.find_element(By.CLASS_NAME, 'tarot-card-description').text.strip()
        return card_name, result, description
    except Exception as e:
        logging.error(f"Error fetching Tarot prediction: {e}")
        return "No prediction", "Unknown", "No description available"
    finally:
        driver.quit()

def interpret_tarot(answer):
    """Interpret the tarot prediction result."""
    return 'yes' if answer.lower() == 'yes' else 'no'

def get_predictions_for_matches(url):
    """Fetch match data and predict outcomes for each match."""
    driver = setup_chrome_driver()
    matches = scrape_match_data(driver, url)
    predictions = []

    for match in matches:
        card_name, tarot_result, card_description = get_tarot_prediction()
        prediction = interpret_tarot(tarot_result)
        predictions.append((
            match['home_team'],
            match['away_team'],
            card_name,
            prediction,
            card_description
        ))

    driver.quit()
    return predictions

@app.route('/')
def index():
    url = 'https://www.flashscore.com/football/'
    predictions = get_predictions_for_matches(url)
    return render_template('index.html', predictions=predictions)

if __name__ == '__main__':
    app.run(debug=True)
