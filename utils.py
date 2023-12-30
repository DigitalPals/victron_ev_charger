import logging
import xml.etree.ElementTree as ET
import pandas as pd
import pytz
import requests
from config import CHARGE_HOURS, TIMEZONE, entsoe_client, COUNTRY, FILENAME, UPDATE_INTERVAL, START_STOP_CHARGE_ADDRESS, modbus_client, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM
from dateutil.parser import parse
from datetime import datetime, timedelta, timezone

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
    total_prices = [sum(price for time, price in times_prices[i:i+charge_duration+1]) for i in range(len(times_prices) - charge_duration)]

    # Find the start time of the charge period with the lowest total price
    min_price_index = total_prices.index(min(total_prices))
    start_time = times_prices[min_price_index][0]

    # Calculate the end time
    if min_price_index + charge_duration < len(times_prices):
        end_time = times_prices[min_price_index + charge_duration][0]
    else:
        # If the end time is out of range, set it to the last time in the list
        end_time = times_prices[-1][0]

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
    
    # Get the current date and time
    now = datetime.now()

    # Set current_datetime to the current time
    current_datetime = now

    # Set tomorrow_datetime to the end of tomorrow
    tomorrow_datetime = (now + timedelta(days=1)).replace(hour=23, minute=59, second=59)

    # Convert the datetime objects to timezone-aware pandas Timestamp objects
    current_datetime = pd.Timestamp(current_datetime).tz_localize('UTC')
    tomorrow_datetime = pd.Timestamp(tomorrow_datetime).tz_localize('UTC')

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

def send_modbus_command(address, value):
    """
    This function sends a command to a Modbus address.
    """
    modbus_client.write_register(address, value)

def send_telegram_notification(message):
    """
    Send a message to a specific Telegram chat.

    Args:
    message (str): The message to send.
    """

    if not TELEGRAM:
        logging.info('Telegram notifications are disabled.')
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    response = requests.post(url, data=data)
    return response.json()

def start_charging():
    send_modbus_command(START_STOP_CHARGE_ADDRESS, 1)
    send_telegram_notification('Charging started') #send Telegram notification

def stop_charging():
    send_modbus_command(START_STOP_CHARGE_ADDRESS, 0)
    send_telegram_notification('Charging ended') #send Telegram notification

def determine_start_end_time():
    # Read the contents of prices.xml
    with open(FILENAME, 'r') as file:
        xml_data = file.read()

    start_time, end_time = calculate_best_hours(xml_data, CHARGE_HOURS)

    # Convert strings to datetime objects
    start_time = parse(start_time)
    end_time = parse(end_time)

    # Format start_time and end_time as strings
    start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
    end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

    # Assuming start_time and end_time are datetime objects
    start_time_str = start_time.strftime("%H:%M")
    end_time_str = end_time.strftime("%H:%M")

    # Get the current time
    now = datetime.now(timezone.utc)

    # Determine if charging starts today or tomorrow
    if start_time.date() > now.date():
        start_day = "tomorrow"
    else:
        start_day = "today"

    output = f"Charging will start {start_day} at {start_time_str} and stop at {end_time_str}"
    send_telegram_notification(output) #send Telegram notification
    print(output)

    return start_time, end_time

def fetch_and_determine_times(scheduler):
    fetch_new_data()
    start_time, end_time = determine_start_end_time()

    # Reschedule the start_charging and stop_charging jobs
    for job in scheduler.get_jobs():
        if job.func == start_charging:
            job.reschedule(trigger='date', run_date=start_time)
        elif job.func == stop_charging:
            job.reschedule(trigger='date', run_date=end_time)

    return start_time, end_time