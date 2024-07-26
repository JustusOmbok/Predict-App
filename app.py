import requests
import random
from flask import Flask, render_template, request, jsonify
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

def get_tarot_prediction(driver):
    url = "https://www.astrology.com/tarot/yes-no.html"
    driver.get(url)

    try:
        # Wait for all cards to be loaded and visible
        cards = WebDriverWait(driver, 90).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.card.card-yes-no-tarot'))
        )
        
        if not cards:
            logging.error("No tarot cards found.")
            return "No prediction", "Unknown", "No description available"

        # Select a random card
        card_to_click = random.choice(cards)
        driver.execute_script("arguments[0].scrollIntoView(true);", card_to_click)
        time.sleep(2)  # Allow the scroll to complete
        driver.execute_script("arguments[0].click();", card_to_click)

        # Wait for the result to be visible using the provided XPath
        result_element = WebDriverWait(driver, 90).until(
            EC.visibility_of_element_located((By.XPATH, '/html/body/main/div/div/div/div[1]/div[2]/p[1]/b'))
        )
        result_text = result_element.text.strip()

        logging.info(f"Tarot Result: {result_text}")

        return result_text
    except Exception as e:
        logging.error(f"Error fetching Tarot prediction: {e}")
        return "No prediction", "Unknown", "No description available"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    home_team = request.form['home_team']
    away_team = request.form['away_team']

    driver = setup_chrome_driver()
    prediction = get_tarot_prediction(driver)
    driver.quit()

    return jsonify({
        'home_team': home_team,
        'away_team': away_team,
        'prediction': prediction
    })

if __name__ == '__main__':
    app.run(debug=True)
