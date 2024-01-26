import os
import configparser
from pymodbus.client import ModbusTcpClient
from entsoe import EntsoePandasClient

config = configparser.ConfigParser()

if os.path.exists('private.ini'):
    config.read('private.ini')
else:
    config.read('config.ini')

API_KEY = config.get('DEFAULT', 'API_KEY').split('#')[0].strip()
COUNTRY = config.get('DEFAULT', 'COUNTRY').split('#')[0].strip()
FILENAME = config.get('DEFAULT', 'FILENAME').split('#')[0].strip()
UPDATE_INTERVAL = int(config.get('DEFAULT', 'UPDATE_INTERVAL').split('#')[0].strip())
TIMEZONE = config.get('DEFAULT', 'TIMEZONE', fallback='Europe/Amsterdam').split('#')[0].strip()
CHARGE_HOURS = int(config.get('DEFAULT', 'CHARGE_HOURS', fallback='4').split('#')[0].strip())

# Split the FETCH_RECALCULATE_TIME string into hours and minutes and convert them to integers
FETCH_RECALCULATE_TIME = config.get('DEFAULT', 'FETCH_RECALCULATE_TIME', fallback='14:15').split('#')[0].replace('"', '').strip()
hour, minute = map(int, FETCH_RECALCULATE_TIME.split(':'))
FETCH_RECALCULATE_TIME = (hour, minute)

# Telegram setup
TELEGRAM_BOT_TOKEN = config.get('DEFAULT', 'TELEGRAM_BOT_TOKEN').split('#')[0].strip()
TELEGRAM_CHAT_ID = config.get('DEFAULT', 'TELEGRAM_CHAT_ID').split('#')[0].strip()
TELEGRAM = config.get('DEFAULT', 'TELEGRAM').lower() == 'true'.split('#')[0].strip()

# Modbus setup
MODBUS_HOST = config.get('DEFAULT', 'MODBUS_HOST').split('#')[0].strip()
MODBUS_PORT = int(config.get('DEFAULT', 'MODBUS_PORT', fallback='502').split('#')[0].strip())
START_STOP_CHARGE_ADDRESS = int(config.get('DEFAULT', 'START_CHARGE_ADDRESS', fallback='5010').split('#')[0].strip())

modbus_client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)

# Define API key in PandasClient
entsoe_client = EntsoePandasClient(API_KEY)