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

    response =  {
        "host": socket.gethostname(),
        "power_usage_watts": 0,
        "disk temp": 0,
        "cpu tctl": 0,
        "cpu tccd1": 0,
        "cpu tccd2": 0,
    }

    for k in sensor_data.keys():

        # parse power if any
        if k.startswith("power_meter"):
            if sensor_data[k].get("power0", None) is not None:
                response["power_usage_watts"] = sensor_data[k].get("power0", {}).get("power0_average", 0)
            else:
                response["power_usage_watts"] = sensor_data[k].get("power1", {}).get("power1_average", 0)
        
        # parse nvme if any
        elif k.startswith("nvme-pci"):
            response["disk temp"] = sensor_data[k].get("Composite", {}).get("temp1_input", 0)
        
        # parse amd cpu power from cpu 0
        elif k.startswith("k10temp-pci-00"):
            response["cpu tctl"] = sensor_data[k].get("Tctl", {}).get("temp1_input", 0)
            response["cpu tccd1"] = sensor_data[k].get("Tccd1", {}).get("temp3_input", 0)
            response["cpu tccd2"] = sensor_data[k].get("Tccd2", {}).get("temp4_input", 0)

        # parse cpu power of intel cpu from cpu 0
        elif k == "coretemp-isa-0000":
            response["cpu tctl"] = sensor_data[k].get("Package id 0", {}).get("temp1_input", 0)

    return response


def collect_data():
    try:
        return get_sensor_data()
    except Exception as e:
        logger.debug(str(e))
    return {}


if __name__=="__main__":
    print(collect_data())
