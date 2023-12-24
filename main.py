import os
import time
import logging
import sys
from datetime import datetime, timedelta
from config import FILENAME, UPDATE_INTERVAL, START_STOP_CHARGE_ADDRESS, modbus_client, CHARGE_HOURS
from utils import fetch_new_data, calculate_best_hours
from dateutil.parser import parse

logging.basicConfig(level=logging.INFO)

def send_modbus_command(address, value):
    """
    This function sends a command to a Modbus address.
    """
    modbus_client.write_register(address, value)

def calculate_sleep_duration(target_time):
    now = datetime.now()
    future = datetime(now.year, now.month, now.day, target_time.hour, target_time.minute, target_time.second)
    if future < now:
        future += timedelta(days=1)
    return (future - now).total_seconds()

def main():
    try:
        # Check if the file exists and is not older than 4 hours
        if not os.path.exists(FILENAME) or time.time() - os.path.getmtime(FILENAME) > UPDATE_INTERVAL:
            logging.info('File is older than 4 hours or does not exist. Fetching new data.')
            fetch_new_data()
        else:
            logging.info('File is newer than 4 hours. No need to fetch new data.')
    except Exception as e:
        logging.error('An error occurred while fetching new data: ' + str(e))
        sys.exit(1)

    # Read the contents of prices.xml
    with open(FILENAME, 'r') as file:
        xml_data = file.read()

    start_time, end_time = calculate_best_hours(xml_data, CHARGE_HOURS)

    # Convert strings to datetime objects
    start_time = parse(start_time)
    end_time = parse(end_time)

    output = f"START:{start_time} STOP:{end_time}"

    print(output)

    while True:
        try:
            # Calculate sleep duration until start time and sleep
            sleep_duration = calculate_sleep_duration(start_time)
            time.sleep(sleep_duration)

            # Start charging
            send_modbus_command(START_STOP_CHARGE_ADDRESS, 1)

            # Calculate sleep duration until end time and sleep
            sleep_duration = calculate_sleep_duration(end_time)
            time.sleep(sleep_duration)

            # Stop charging
            send_modbus_command(START_STOP_CHARGE_ADDRESS, 0)

        except KeyboardInterrupt:
            print("Program stopped by user.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break

if __name__ == "__main__":
    main()