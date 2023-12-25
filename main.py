import os
import time
import logging
import sys
from config import FILENAME, UPDATE_INTERVAL, START_STOP_CHARGE_ADDRESS, modbus_client, CHARGE_HOURS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM
from utils import fetch_new_data, calculate_best_hours, send_modbus_command, send_telegram_notification, start_charging, stop_charging, determine_start_end_time, fetch_and_determine_times
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)

def main():
    try:
        # Check if the file exists and is not older than 4 hours
        if not os.path.exists(FILENAME) or time.time() - os.path.getmtime(FILENAME) > UPDATE_INTERVAL:
            logging.info('File is older than 4 hours or does not exist. Fetching new data.')
            fetch_new_data()  # Fetch new data if file is older than 4 hours or does not exist
        else:
            logging.info('File is newer than 4 hours. No need to fetch new data.')
    except Exception as e:
        logging.error('An error occurred while fetching new data: ' + str(e))
        sys.exit(1)  # Exit the program if an error occurs

    # Determine the start and end times for charging
    start_time, end_time = determine_start_end_time()

    # Set up the scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(start_charging, 'date', run_date=start_time)  # Schedule the start_charging job
    scheduler.add_job(stop_charging, 'date', run_date=end_time)  # Schedule the stop_charging job
    scheduler.add_job(fetch_and_determine_times, 'cron', hour=14, minute=15)  # Schedule the fetch_and_determine_times job to run at 14:15 every day
    scheduler.start()  # Start the scheduler

    # Print the scheduled jobs
    print("Scheduled jobs:")
    print(datetime.now())
    for job in scheduler.get_jobs():
        print(f"Job ID: {job.id}, Next Run Time: {job.next_run_time}, Function: {job.func.__name__}")

    try:
        # Keep the program running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Interrupted by user. Exiting...")
        scheduler.shutdown()  # Shut down the scheduler if the program is interrupted

if __name__ == "__main__":
    main()  # Run the main function