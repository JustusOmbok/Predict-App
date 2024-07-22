import random
from flask import Flask, render_template
import requests
import logging
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO)

# Suppress only the single InsecureRequestWarning from urllib3
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Initialize Flask app
app = Flask(__name__)

def setup_chrome_driver(headless=False):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), 
        options=chrome_options
    )
    return driver

def scrape_match_data(driver, url):
    """Scrape football match data from the provided URL."""
    driver.get(url)
    time.sleep(5)  # Wait for the page to load completely

    try:
        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#live-table")))
    except TimeoutException:
        logging.error("Page took too long to load.")
        return []

    page_source = driver.page_source
    bs_obj = BeautifulSoup(page_source, "lxml")

    matches = []
    live_table = bs_obj.select_one("#live-table")

    if not live_table:
        logging.error("Could not find live table")
        return []

    match_elements = live_table.select(".event__match--static")

    logging.info(f"Found {len(match_elements)} matches")

    target_date = "17.08."

    for match in match_elements:
        home_team = match.select_one(".event__homeParticipant")
        away_team = match.select_one(".event__awayParticipant")
        match_link = match.select_one(".eventRowLink")["href"]
        match_date = match.select_one(".event__time").text.strip() if match.select_one(".event__time") else "No date"

        if match_date.startswith(target_date):  # Check if the match date is 17.08.2024
            matches.append({
                "home_team": home_team.text.strip() if home_team else "No home team",
                "away_team": away_team.text.strip() if away_team else "No away team",
                "link": match_link,
                "date_time": match_date
            })

    logging.info(f"Found {len(matches)} round matches")
    return matches


def get_tarot_prediction(driver):
    url = "https://www.astrology.com/tarot/yes-no.html"
    driver.get(url)

    try:
        # Wait for all cards to be loaded and visible
        cards = WebDriverWait(driver, 60).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.card.card-yes-no-tarot'))
        )
        
        if not cards:
            logging.error("No tarot cards found.")
            return "No prediction", "Unknown", "No description available"

        # Select a random card
        card_to_click = random.choice(cards)
        driver.execute_script("arguments[0].scrollIntoView(true);", card_to_click)
        time.sleep(1)  # Allow the scroll to complete
        driver.execute_script("arguments[0].click();", card_to_click)

        # Wait for results to be visible
        card_name = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'tarot-card-name'))
        ).text.strip()
        result = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'yes-no-result'))
        ).text.strip()
        description = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'tarot-card-description'))
        ).text.strip()
        
        return card_name, result, description
    except Exception as e:
        logging.error(f"Error fetching Tarot prediction: {e}")
        return "No prediction", "Unknown", "No description available"

def interpret_tarot(answer):
    """Interpret the tarot prediction result."""
    return 'yes' if answer.lower() == 'yes' else 'no'

def get_predictions_for_matches(url):
    """Fetch match data and predict outcomes for each match."""
    driver = setup_chrome_driver()
    matches = scrape_match_data(driver, url)
    predictions = []

    for match in matches:
        card_name, tarot_result, card_description = get_tarot_prediction(driver)
        prediction = interpret_tarot(tarot_result)
        predictions.append({
            'home_team': match['home_team'],
            'away_team': match['away_team'],
            'link': match['link'],
            'date_time': match['date_time'],
            'card_name': card_name,
            'prediction': prediction,
            'description': card_description
        })

    driver.quit()
    return predictions

@app.route('/')
def index():
    url = 'https://www.flashscore.com/football/england/premier-league/fixtures/'
    predictions = get_predictions_for_matches(url)
    return render_template('index.html', predictions=predictions)

if __name__ == '__main__':
    app.run(debug=True)
