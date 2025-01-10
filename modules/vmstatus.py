import socket
import traceback
from threading import Thread
import inotify.adapters
from modules import logger

def parse_data(log):
	log_parts = log.split(':')

	if log_parts[5] != 'qmstart' and log_parts[5] != 'qmstop':
		return

	log_data = {
		'host': socket.gethostname(),
		'status': log_parts[5],
		'vmid': log_parts[6],
		'details': log_parts[8].strip()
	}

def collect_data_continuously():
	log_file="/var/log/pve/tasks/index"
	i = inotify.adapters.Inotify()
	i.add_watch(log_file)

	try:
		for event in i.event_gen(yield_nones=False):
			(_, type_names, path, filename) = event

			if "IN_MODIFY" in type_names:
				with open(log_file, 'r') as file:
					lines = file.readlines()
					last_line = lines[-1].strip()
					t1 = Thread(target=parse_data, args=(last_line,))
					t1.run()
	except Exception:
		logger.debug(f"Failed to capture vm_status {traceback.format_exc()}")

	finally:
		i.remove_watch(log_file)

# if __name__=="__main__":
# 	collect_data()
