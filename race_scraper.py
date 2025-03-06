from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import time
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
from collections import defaultdict

def scrape_race_results(search_name):
    # Install ChromeDriver
    chromedriver_autoinstaller.install()
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Setup Chrome driver with options
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Navigate to the website
        driver.get("https://raceview.net/")
        
        # Wait for search input to be present and click it
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "theQueryText"))
        )
        search_input.clear()
        search_input.send_keys(search_name)
        
        # Find and click search button
        search_button = driver.find_element(By.ID, "btnSearch")
        search_button.click()
        
        # Wait for results table to load
        time.sleep(2)  # Give some time for the table to populate
        
        # Get the page source after results load
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find the results table
        results_table = soup.find('table', class_='resultsTable')
        
        if not results_table:
            return {"error": "No results found"}
        
        # Get headers
        headers = []
        for header in results_table.find_all('td', class_='resultsTableHeader'):
            headers.append(header.text.strip())
        
        # Get results
        results = []
        for row in results_table.find_all('tr', class_='resultsTableRow'):
            cells = row.find_all('td')
            result = {}
            for i, cell in enumerate(cells):
                if i < len(headers):
                    # Get text content, handling links if present
                    cell_text = cell.find('a').text if cell.find('a') else cell.text
                    result[headers[i]] = cell_text.strip()
            if result:
                results.append(result)
        
        # Group results by distance (מקצה) and find best times
        distance_results = defaultdict(list)
        for result in results:
            distance = result.get('מקצה', '')
            if distance:
                distance_results[distance].append(result)
        
        # Find best result for each distance
        best_results = {}
        for distance, races in distance_results.items():
            # Sort by time (תוצאה)
            sorted_races = sorted(races, key=lambda x: x.get('תוצאה', '99:99:99'))
            best_results[distance] = sorted_races[0]
        
        return {
            "best_results_by_distance": best_results
        }
        
    finally:
        driver.quit()

if __name__ == "__main__":
    # Search for יהודה גבאי
    search_name = "יהודה גבאי"
    results = scrape_race_results(search_name)
    
    # Print results in a formatted JSON
    print("\nBest Results for each Distance:")
    print(json.dumps(results, ensure_ascii=False, indent=2)) 