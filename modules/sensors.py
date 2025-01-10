import socket
import json
import subprocess

from modules import logger


def get_sensor_data():
    # Run the 'sensors -j' command
    sensors_command = 'sensors -j'
    output_bytes = subprocess.check_output(sensors_command, shell=True)

    # Decode the output from bytes to a string
    sensors_output = output_bytes.decode('utf-8')

    # Parse the JSON output
    sensor_data = json.loads(sensors_output)

    # Extract values into a dictionary
    return {
	"host": socket.gethostname(),
        "disk temp": sensor_data.get("nvme-pci-0100", {}).get("Composite", {}).get("temp1_input"),
        "cpu tctl": sensor_data.get("k10temp-pci-00c3", {}).get("Tctl", {}).get("temp1_input"),
        "cpu tccd1": sensor_data.get("k10temp-pci-00c3", {}).get("Tccd1", {}).get("temp3_input"),
        "cpu tccd2": sensor_data.get("k10temp-pci-00c3", {}).get("Tccd2", {}).get("temp4_input"),
    }


def collect_data():
    try:
        return get_sensor_data()
    except Exception as e:
        logger.debug(str(e))
    return {}


if __name__=="__main__":
    print(collect_data())
