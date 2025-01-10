import socket
from modules import logger


def get_system_uptime_seconds():
    try:
        with open('/proc/uptime', 'r') as f:
            # Read the first line from /proc/uptime
            uptime_seconds = float(f.readline().split()[0])
            return int(uptime_seconds)

    except Exception as e:
        logger.debug(f"Error reading uptime: {e}")
    return 0

def collect_data():
    try:
        hostname = socket.gethostname()
        uptime_seconds = get_system_uptime_seconds()
        return {
            "host": hostname,
            "uptime": uptime_seconds
        }
    except Exception as e:
        logger.debug(str(e))
    return {}


if __name__=="__main__":
	print(collect_data())
