import os
import socket
import subprocess
import ujson
from modules import logger

def get_nvme_disk_names():
    try:
        command_output = subprocess.check_output(['lsblk', '-o', 'NAME,SIZE,MOUNTPOINT'])
        output_string = command_output.decode('utf-8')
        lines = output_string.split('\n')
        nvme_disks = [line.split()[0] for line in lines if 'nvme' in line]
        return nvme_disks

    except subprocess.CalledProcessError as e:
        logger.debug(f"Error: {e}")
        return []

def get_disk_stats(disk_path):
    try:
        output = subprocess.check_output(
            ['sudo', 'smartctl', '-j', '-a', disk_path], text=True)
        if output and output.startswith('{ "'):
            data = ujson.loads(output)
            return data
    except subprocess.CalledProcessError as e:
        logger.debug(f"Command failed with exit status {e.returncode}")
        if e.output and e.output.startswith('{\n'):
            data = ujson.loads(e.output)
            return data
    except Exception as e:
        logger.debug(str(e))
    return {}

def get_smartctl_data(disk_path):

    if disk_path is None:
        logger.debug("DISK_PATH environment variable is not set.")
        return None

    smart_data = get_disk_stats(disk_path)

    # Extract relevant values from the JSON data
    hostname = socket.gethostname()
    temperature = smart_data.get('temperature', {}).get('current', 0)
    available_spare = smart_data.get('nvme_smart_health_information_log', {}).get('available_spare', 0)
    percentage_used = smart_data.get('nvme_smart_health_information_log', {}).get('percentage_used', 0)
    data_units_read = smart_data.get('nvme_smart_health_information_log', {}).get('data_units_read', 0)
    data_units_written = smart_data.get('nvme_smart_health_information_log', {}).get('data_units_written', 0)
    host_read_commands = smart_data.get('nvme_smart_health_information_log', {}).get('host_reads', 0)
    host_write_commands = smart_data.get('nvme_smart_health_information_log', {}).get('host_writes', 0)
    power_cycles = smart_data.get('nvme_smart_health_information_log', {}).get('power_cycles', 0)
    power_on_hours = smart_data.get('nvme_smart_health_information_log', {}).get('power_on_hours', 0)
    unsafe_shutdowns = smart_data.get('nvme_smart_health_information_log', {}).get('unsafe_shutdowns', 0)
    media_and_data_integrity_errors = smart_data.get('nvme_smart_health_information_log', {}).get('media_errors', 0)

    return {
        "host": hostname,
        "disk": disk_path,
        "temperature": int(temperature),
        "available_spare": int(available_spare),
        "wearout": int(percentage_used),
        "data_units_read": int(data_units_read),
        "data_units_written": int(data_units_written),
        "host_read_commands": int(host_read_commands),
        "host_write_commands": int(host_write_commands),
        "power_cycles": int(power_cycles),
        "power_on_hours": int(power_on_hours),
        "unsafe_shutdowns": int(unsafe_shutdowns),
        "media_and_data_integrity_errors": int(media_and_data_integrity_errors)
    }


def collect_data():
    try:
        if os.getenv("STORAGE_SERVER"):
            disks = get_nvme_disk_names()
            disk_data = []
            for disk in disks:
                disk_data.append(get_smartctl_data(f"/dev/{disk}"))

            return disk_data

        disk_path = os.getenv("DISK_PATH")
        return get_smartctl_data(disk_path)
    except Exception as e:
        logger.debug(str(e))
    return {}


if __name__=="__main__":
    logger.debug(collect_data())
