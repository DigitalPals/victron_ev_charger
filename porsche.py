import asyncio
from pyporscheconnectapi.connection import Connection
from pyporscheconnectapi.client import Client
from config import PORSCHE_EMAIL, PORSCHE_PASSWORD

async def get_vehicle_battery_soc(email: str, password: str) -> None:
    conn = Connection(email, password)
    client = Client(conn)

    vehicles = await client.getVehicles()
    for vehicle in vehicles:
        # Using connection.get will automatically add auth headers
        data = await conn.get(f"https://api.porsche.com/service-vehicle/se/sv_SE/vehicle-data/{vehicle['vin']}/stored")
        battery_soc = data['batteryLevel']['value']
        await conn.close()
        return battery_soc  # Return battery soc

def get_battery_soc():
    return asyncio.run(get_vehicle_battery_soc(PORSCHE_EMAIL, PORSCHE_PASSWORD))