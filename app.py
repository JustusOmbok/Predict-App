from flask import Flask, render_template
import requests
import logging
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import random

chrome_options = Options()
chrome_options.add_argument('--ignore-certificate-errors')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
# Suppress only the single InsecureRequestWarning from urllib3 needed for development
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

@app.route('/')
def index():
    url = 'https://ke.sportpesa.com/en/sports-betting/football-1/'
    predictions = get_predictions_for_matches(url)
    return render_template('index.html', predictions=predictions)

def get_match_data(url):
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        matches = []

        # Select all match rows
        match_rows = soup.select('.event-row.event-row-header')

        for match_row in match_rows:
            # Extract market names
            market_names_divs = match_row.select('.event-market-name span')
            if market_names_divs:
                market_names = [market_name.get_text(strip=True) for market_name in market_names_divs]
                if len(market_names) >= 2:
                    # Assume the first two market names are the team names
                    home_team = market_names[0]
                    away_team = market_names[1]
                    
                    matches.append({
                        'home_team': home_team,
                        'away_team': away_team
                    })
                else:
                    print("Warning: Not enough market name data found in match row.")
            else:
                print("Warning: Market names section not found in match row.")
        
        return matches

    except requests.RequestException as e:
        print(f"Error fetching match data: {e}")
        return []

def get_tarot_prediction_with_selenium():
    try:
        url = "https://www.astrology.com/tarot/yes-no.html"
        
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        
        time.sleep(5)
        
        # Click on a random tarot card
        cards = driver.find_elements(By.CSS_SELECTOR, '.card')
        if cards:
            random.choice(cards).click()
        
        time.sleep(5)
        
        result_div = driver.find_element(By.CLASS_NAME, 'yes-no-result')
        if result_div:
            answer = result_div.text.strip()
            driver.quit()
            return answer
        else:
            print("Error: 'yes-no-result' div not found in the HTML.")
            driver.quit()
            return "No prediction"
    except Exception as e:
        print(f"Error fetching Tarot prediction: {e}")
        return "Error"

def interpret_tarot(answer):
    return 'yes' if answer.lower() == 'yes' else 'no'

def predict_match_outcome():
    tarot_result = get_tarot_prediction_with_selenium()
    interpreted_result = interpret_tarot(tarot_result)
    return interpreted_result

def get_predictions_for_matches(url):
    matches = get_match_data(url)
    predictions = []
    
    for match in matches:
        home_team = match['home_team']
        away_team = match['away_team']
        prediction = predict_match_outcome()
        predictions.append((home_team, away_team, prediction))
    
    return predictions

if __name__ == '__main__':
    app.run(debug=True)
