import os
import configparser
from pymodbus.client import ModbusTcpClient
from entsoe import EntsoePandasClient

config = configparser.ConfigParser()
config.read('config.ini')

API_KEY = os.getenv('API_KEY', config.get('DEFAULT', 'API_KEY'))
COUNTRY = os.getenv('COUNTRY', config.get('DEFAULT', 'COUNTRY'))
FILENAME = os.getenv('FILENAME', config.get('DEFAULT', 'FILENAME'))
UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', config.get('DEFAULT', 'UPDATE_INTERVAL')))
TIMEZONE = os.getenv('TIMEZONE', config.get('DEFAULT', 'TIMEZONE', fallback='Europe/Amsterdam'))
CHARGE_HOURS = int(os.getenv('CHARGE_HOURS', config.get('DEFAULT', 'CHARGE_HOURS', fallback='4')).split('#')[0])

# Split the FETCH_RECALCULATE_TIME string into hours and minutes and convert them to integers
FETCH_RECALCULATE_TIME = os.getenv('FETCH_RECALCULATE_TIME', config.get('DEFAULT', 'FETCH_RECALCULATE_TIME', fallback='14:15')).split('#')[0]
hour, minute = map(int, FETCH_RECALCULATE_TIME.split(':'))
FETCH_RECALCULATE_TIME = (hour, minute)

# Telegram setup
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', config.get('DEFAULT', 'TELEGRAM_BOT_TOKEN'))
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', config.get('DEFAULT', 'TELEGRAM_CHAT_ID'))
TELEGRAM = os.getenv('TELEGRAM', config.get('DEFAULT', 'TELEGRAM')).lower() == 'true'

# Modbus setup
MODBUS_HOST = os.getenv('MODBUS_HOST', config.get('DEFAULT', 'MODBUS_HOST')).split('#')[0].strip()
MODBUS_PORT = int(os.getenv('MODBUS_PORT', config.get('DEFAULT', 'MODBUS_PORT', fallback='502')))
START_STOP_CHARGE_ADDRESS = int(os.getenv('START_CHARGE_ADDRESS', config.get('DEFAULT', 'START_CHARGE_ADDRESS', fallback='5010')))

modbus_client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)

# Define API key in PandasClient
entsoe_client = EntsoePandasClient(API_KEY)