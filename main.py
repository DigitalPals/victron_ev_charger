import os
import time
import logging
import sys
import requests
from datetime import datetime, timedelta, timezone
from config import FILENAME, UPDATE_INTERVAL, START_STOP_CHARGE_ADDRESS, modbus_client, CHARGE_HOURS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM
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

def send_telegram_notification(message):
    """
    Send a message to a specific Telegram chat.

    Args:
    message (str): The message to send.
    """

    if not TELEGRAM:
        print('Telegram notifications are disabled.')
        logging.info('Telegram notifications are disabled.')
        return
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message
    }
    response = requests.post(url, data=data)
    return response.json()

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

    while True:
        try:
            # Read the current value of START_STOP_CHARGE_ADDRESS at startup
            current_value = modbus_client.read_holding_registers(START_STOP_CHARGE_ADDRESS, 1)
            print(f"Current value of START_STOP_CHARGE_ADDRESS: {current_value.registers[0]}")

            # Calculate sleep duration until start time and sleep
            sleep_duration = calculate_sleep_duration(start_time)
            time.sleep(sleep_duration)

            # Start charging
            send_modbus_command(START_STOP_CHARGE_ADDRESS, 1)
            send_telegram_notification('Charging started') #send Telegram notification

            # Calculate sleep duration until end time and sleep
            sleep_duration = calculate_sleep_duration(end_time)
            time.sleep(sleep_duration)

            # Stop charging
            send_modbus_command(START_STOP_CHARGE_ADDRESS, 0)
            send_telegram_notification('Charging ended') #send Telegram notification

        except KeyboardInterrupt:
            print("Program stopped by user.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break

if __name__ == "__main__":
    main()