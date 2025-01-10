import os
import influxdb_client

from dotenv import load_dotenv
from influxdb_client.client.write_api import SYNCHRONOUS

load_dotenv()

INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")

client = influxdb_client.InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)


def create_influxdb_point(measurement, data):
    point = influxdb_client.Point(measurement)
    for key, value in data.items():
        if key == 'host':
            # hotfix for dot in hostname
            point = point.tag(key, value.split('.')[0])
        if key == 'vm_name':
            point = point.tag(key, value)
        else:
            point = point.field(key, value)

    return point
