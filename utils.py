import logging
import xml.etree.ElementTree as ET
import pandas as pd
import pytz
from config import CHARGE_HOURS, TIMEZONE, entsoe_client, COUNTRY

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