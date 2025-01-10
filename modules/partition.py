import socket
import os
import psutil
from modules import logger

def get_disk_space_usage(device):
    try:
        # Get disk usage information using psutil
        partition = psutil.disk_usage(device)

        # Create a dictionary with relevant information
        disk_space_info = {
            'host': socket.gethostname(),
            'device': device,
            'Total': partition.total,
            'Used': partition.used,
            'Free': partition.free,
            'Percent': partition.percent
        }

        return disk_space_info

    except Exception as e:
        return {"Error": str(e)}

def get_disk_usage_for_mount_points(mnt_directory='/mnt'):
    try:
        # Get a list of items (mount points) inside the specified directory
        mount_points = [item for item in os.listdir(mnt_directory) if os.path.ismount(os.path.join(mnt_directory, item))]
        data = []
        data.append(get_disk_space_usage('/'))

        if not os.getenv("STORAGE_SERVER"):
            return data

        # Get and print disk space usage for each mount point
        for mount_point in mount_points:
            full_path = os.path.join(mnt_directory, mount_point)
            data.append(get_disk_space_usage(full_path))

        return data

    except Exception as e:
        logger.debug(f"Error: {e}")


def collect_data():
    try:
        mnt_directory = '/mnt'
        return get_disk_usage_for_mount_points(mnt_directory)
    except Exception as e:
        logger.debug(str(e))
    return {}


if __name__ == "__main__":
    print(collect_data())

