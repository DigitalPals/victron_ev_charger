# Victron EV Smart Charging
Victron EV Smart Charging is a Python-based tool designed to optimize electric vehicle charging costs. It fetches current and next day electricity prices, analyzes trends, and schedules charging sessions for your EV during the lowest rate periods. This ensures you benefit from the most cost-effective charging times, reducing your expenses and maximizing efficiency without manual monitoring.

## Getting Started
These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites
You need to have Python installed on your machine. 

### Installing
Clone the repository
```bash
git clone https://github.com/DigitalPals/victron_ev_charger
```

Navigate to the project directory
```bash
cd victron_ev_charger
```

Install the required packages
```bash
pip install -r requirements.txt
```
## Configuring
Before running the script, ensure all settings are properly configured.

### config.ini
Modify `config.ini to include` the ENTSO-E `API_KEY` and the `MODBUS_HOST` address for the Victron Energy EV charging station.

### Victron Energy EV charging station settings
Access the charging station's web application and navigate to `Settings -> EVCS ModbusTCP Server`. Either add the script-running machine to the whitelist or disable IP address whitelist state to allow connections.

## Usage
Running the script
You can run the script using the following command (To stop the script, press Ctrl-C):

```bash
python main.py
```