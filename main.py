import os
import time
import logging
import configparser
import requests
import sys
import xml.etree.ElementTree as ET
import pandas as pd
import pytz
from entsoe import EntsoePandasClient

logging.basicConfig(level=logging.INFO)

# Read configuration file
config = configparser.ConfigParser()
config.read('config.ini')

# CONSTANTS
API_KEY = os.getenv('API_KEY', config.get('DEFAULT', 'API_KEY'))
COUNTRY = os.getenv('COUNTRY', config.get('DEFAULT', 'COUNTRY'))
FILENAME = os.getenv('FILENAME', config.get('DEFAULT', 'FILENAME'))
UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', config.get('DEFAULT', 'UPDATE_INTERVAL')))
TIMEZONE = os.getenv('TIMEZONE', config.get('DEFAULT', 'TIMEZONE', fallback='Europe/Amsterdam'))
CHARGE_HOURS = int(os.getenv('CHARGE_HOURS', config.get('DEFAULT', 'CHARGE_HOURS', fallback='4')))

# Define API key in PandasClient
entsoe_client = EntsoePandasClient(API_KEY)

def calculate_best_hours(xml_data, charge_duration):
    """
    This function calculates the best hours to charge the car based on the provided XML data and charge duration.
    It returns the start and end times of the best charge period.
    """
    logging.info('Calculating best time to charge car.')
    
    # Parse the XML data
    root = ET.fromstring(xml_data)

    # Extract the prices and their corresponding times
    times_prices = [(row.find('index').text, float(row.find('price').text)) for row in root.findall('row')]

    # Calculate the total price for each possible charge period
    total_prices = [sum(price for time, price in times_prices[i:i+charge_duration]) for i in range(len(times_prices) - charge_duration + 1)]

    # Find the start time of the charge period with the lowest total price
    min_price_index = total_prices.index(min(total_prices))
    start_time = times_prices[min_price_index][0]
    end_time = times_prices[min_price_index + charge_duration][0]

    return start_time, end_time

def get_current_and_tomorrow_datetime():
    """
    This function returns the current datetime and the datetime 24 hours from now.
    """
    # Get the current date and time
    current_datetime = pd.Timestamp.now(tz=pytz.timezone(TIMEZONE))

    # Get the date and time 24 hours from now
    tomorrow_datetime = current_datetime + pd.DateOffset(days=1)

    return current_datetime, tomorrow_datetime

def fetch_new_data():
    """
    This function fetches new data from the API and writes it to a file.
    """
    logging.info('Fetching new data.')
    
    current_datetime, tomorrow_datetime = get_current_and_tomorrow_datetime()

    # Query day ahead prices for a specific country, e.g., Netherlands
    prices = entsoe_client.query_day_ahead_prices(COUNTRY, start=current_datetime, end=tomorrow_datetime)

    # Convert the Series to a DataFrame
    prices_df = prices.to_frame()

    # Rename the column to a valid XML tag name
    prices_df = prices_df.rename(columns={0: 'price'})

    # Convert the DataFrame to an XML string
    prices_xml = prices_df.to_xml()

    # Write the XML string to a file
    with open(FILENAME, 'w') as f:
        f.write(prices_xml)

    logging.info('New data fetched and written to file.')

try:
    # Check if the file exists and is not older than 4 hours
    if not os.path.exists(FILENAME) or time.time() - os.path.getmtime(FILENAME) > UPDATE_INTERVAL:
        logging.info('File is older than 4 hours or does not exist. Fetching new data.')
        fetch_new_data()
    else:
        logging.info('File is newer than 4 hours. No need to fetch new data.')
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        logging.error('Failed to fetch new data. Please check your API key.')
        sys.exit(1)
    else:
        logging.error('An error occurred while fetching new data: ' + str(e))

# Read the contents of prices.xml
with open(FILENAME, 'r') as file:
    xml_data = file.read()

start_time, end_time = calculate_best_hours(xml_data, CHARGE_HOURS)
output = f"START:{start_time} STOP:{end_time}"

print(output)