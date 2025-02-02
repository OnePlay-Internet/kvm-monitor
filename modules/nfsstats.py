import subprocess, re, json
from modules import logger

# Define a function to parse the data
def parse_nfsiostat(data):
    # Extract the NFS server information
    server_info = re.search(r"(\S+):(/[^ ]+)\s+mounted on\s+([^\n]+)", data)
    server_address, nfs_mount, mount_point = server_info.groups() if server_info else (None, None, None)

    # Extract the ops/s and rpc bklog
    ops_rpc_bklog = re.search(r"ops/s\s+rpc bklog\n\s+([0-9.]+)\s+([0-9.]+)", data)
    ops_per_sec, rpc_bklog = ops_rpc_bklog.groups() if ops_rpc_bklog else (None, None)

    # Extract read data
    read_data = re.search(r"read:\s+ops/s\s+kB/s\s+kB/op\s+retrans\s+avg RTT \(ms\)\s+avg exe \(ms\)\s+avg queue \(ms\)\s+errors\n\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9]+)\s+\([0-9.]+\%\)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9]+)", data)
    read_ops_per_sec, read_kb_per_sec, read_kb_per_op, read_retrans, read_avg_rtt, read_avg_exe, read_avg_queue, read_errors = read_data.groups() if read_data else (None, None, None, None, None, None, None, None)

    # Extract write data
    write_data = re.search(r"write:\s+ops/s\s+kB/s\s+kB/op\s+retrans\s+avg RTT \(ms\)\s+avg exe \(ms\)\s+avg queue \(ms\)\s+errors\n\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9]+)\s+\([0-9.]+\%\)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9]+)", data)
    write_ops_per_sec, write_kb_per_sec, write_kb_per_op, write_retrans, write_avg_rtt, write_avg_exe, write_avg_queue, write_errors = write_data.groups() if write_data else (None, None, None, None, None, None, None, None)

    # Construct the dictionary with parsed data
    nfsiostat_json = {
        "server_address": server_address,
        "nfs_mount": nfs_mount,
        "mount_point": mount_point,
        "ops_per_sec": ops_per_sec,
        "rpc_bklog": rpc_bklog,
        "read": {
            "ops_per_sec": read_ops_per_sec,
            "kb_per_sec": read_kb_per_sec,
            "kb_per_op": read_kb_per_op,
            "retrans": read_retrans,
            "avg_rtt": read_avg_rtt,
            "avg_exe": read_avg_exe,
            "avg_queue": read_avg_queue,
            "errors": read_errors
        },
        "write": {
            "ops_per_sec": write_ops_per_sec,
            "kb_per_sec": write_kb_per_sec,
            "kb_per_op": write_kb_per_op,
            "retrans": write_retrans,
            "avg_rtt": write_avg_rtt,
            "avg_exe": write_avg_exe,
            "avg_queue": write_avg_queue,
            "errors": write_errors
        }
    }

    return nfsiostat_json



def get_nfs_io_stats():
    # Get NFS IO Stats
    output = subprocess.check_output(["nfsiostat"], shell=True).decode('utf-8')
    return json.dumps(parse_nfsiostat(output))
 

def collect_data():
    try:
        return get_nfs_io_stats()
    except Exception as e:
        logger.debug(str(e))
    return {}


if __name__=="__main__":
    print(collect_data())
