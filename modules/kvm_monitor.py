import os
import subprocess
from threading import Thread
from xml.etree import ElementTree

import inotify.adapters
import libvirt
import psutil

import ujson
import time
import traceback

from connection import create_influxdb_point, write_api, INFLUX_BUCKET, INFLUX_ORG
from modules import MONITORING_INTERVAL, logger

VM_STATE_DEFINITION = {
    libvirt.VIR_DOMAIN_NOSTATE: "no_state",
    libvirt.VIR_DOMAIN_RUNNING: "running",
    libvirt.VIR_DOMAIN_BLOCKED: "blocked",
    libvirt.VIR_DOMAIN_PAUSED: "paused",
    libvirt.VIR_DOMAIN_SHUTDOWN: "shutdown",
    libvirt.VIR_DOMAIN_SHUTOFF: "shutoff",
    libvirt.VIR_DOMAIN_CRASHED: "crashed",
    libvirt.VIR_DOMAIN_PMSUSPENDED: "suspended_by_power_manager"
}

def get_vms_with_state():
    try:
        output_lines = subprocess.check_output(['virsh', 'list', '--all']).decode('utf-8').strip().split('\n')
        vm_stats = []
        keys = output_lines[0].split('   ')
        keys = [key.lower().strip() for key in keys]
        for line in output_lines[2:]:
            values = line.split('   ')
            vm_stat = dict()
            vm_stat[keys[0]] = values[0].strip()
            vm_stat[keys[1]] = values[1].strip()
            vm_stat[keys[2]] = values[2].strip()
            vm_stats.append(vm_stat)
        return vm_stats
    except Exception as e:
        logger.debug(traceback.format_exc())
        return []


def get_kvm_stats():
    try:
        output = subprocess.check_output(
            ['sudo', '-S', 'kvmtop', '--cpu', '--mem', '--disk', '--net', '--io', '--host',
             '--printer=json', '--runs=1'], input=f'{os.getenv("ROOT_PASS")}\n', text=True)
        if output and output.startswith('{ "'):
            data = ujson.loads(output)
            return data
    except Exception as e:
        logger.debug(traceback.format_exc())
    return {}


def sync_data_to_influx_db(data):
    try:
        point = create_influxdb_point('kvm_stats', data)
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        logger.debug(f"writing record for kvm_stats finished.")
    except Exception as e:
        logger.debug(traceback.format_exc())
        return


def group_data_points(key_prefix, source_data):
    return {key: source_data[key] for key in source_data if key.startswith(key_prefix)}


def filter_and_group_host_stats(hostname, host_uuid, data):
    try:
        to_return = {}
        host_key_groups = {"cpu_": "cpustat", "ram_": "memory", "disk_": "disk", "net_": "nics", "psi_": "psistat"}
        for key in host_key_groups:
            data_group = group_data_points(key_prefix=key, source_data=data)
            if data_group:
                if host_key_groups[key] == "memory":
                    for k, v in data_group.items():
                        data_group[k] = round(v / (1024*1024), 2)
                if host_key_groups[key] == "cpustat":
                    data_group['cpu_usage'] = psutil.cpu_percent(interval=MONITORING_INTERVAL)
                data_group.update({"host": hostname, "host_uuid": host_uuid})
                to_return[host_key_groups[key]] = data_group
        return to_return
    except Exception as e:
        logger.debug(traceback.format_exc())
        return {}


def filter_and_group_vm_stats(hostname, host_uuid, data):
    try:
        to_return = {}
        vm_name = data.get('name', "")
        vm_id = data.get('UUID', "")
        host_key_groups = {"cpu_": "cpustat", "ram_": "memory", "disk_": "disk", "net_": "nics", "io_": "iostat", }
        for key in host_key_groups.keys():
            data_group = group_data_points(key_prefix=key, source_data=data)
            if key == 'cpu_':
                data_group.update({'state': data.get('state')})
            if host_key_groups[key] == "memory":
                for k, v in data_group.items():
                    data_group[k] = round(v / (1024 * 1024), 2)
            if data_group:
                data_group.update({"host": hostname, "host_uuid": host_uuid, "vm_name": vm_name, "vm_id": vm_id})
                to_return[f"vm_{host_key_groups[key]}"] = data_group
        return to_return
    except Exception as e:
        logger.debug(traceback.format_exc())
        return {}


def send_data_to_influxdb(data):
    for key, value in data.items():
        if value:
            point = create_influxdb_point(key, value)
            write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
            logger.debug(f"writing record for {key} finished.")
    else:
        logger.debug('Uploaded all data points from kvm_monitor')


def merge_lists_of_dicts(list1, list2, key):
    # Create a dictionary to hold merged results
    merged_dict = {}

    # Add dictionaries from the first list to the merged_dict
    for item in list1:
        merged_dict[item[key]] = item

    # Update the merged_dict with dictionaries from the second list
    for item in list2:
        if item[key] in merged_dict:
            # If the key exists, merge the dictionaries
            merged_dict[item[key]].update(item)
        else:
            # If the key does not exist, add the new item
            merged_dict[item[key]] = item

    # Convert merged_dict back to a list
    return list(merged_dict.values())


def send_data(log):
    try:
        vms_list = get_vms_with_state()
        domains = log.get('domains', [])
        if not domains:
            for vm in vms_list:
                vm_stat = dict()
                vm_stat['name'] = vm.get('name')
                vm_stat['state'] = vm.get('state')
                domains.append(vm_stat)
        else:
            for domain in domains:
                domain.update({'state': 'running'})

        hostname = log.get("host", {}).get("host_name")
        host_uuid = log.get("host", {}).get("host_uuid")
        host, vms = get_vms_and_host_stats()
        log['host'].update(host)
        host_data = filter_and_group_host_stats(hostname, host_uuid, data=log.get('host'))
        send_data_to_influxdb(host_data)
        combined_vms = merge_lists_of_dicts(domains, vms, 'name')
        for vm_stats in combined_vms:
            if vm_stats.get('state') == 'running':
                send_data_to_influxdb(filter_and_group_vm_stats(hostname, host_uuid, data=vm_stats))
        return True
    except Exception as e:
        logger.debug(traceback.format_exc())
        return


def collect_data_continuously():
    log_file = "/home/vignesh/dev/kvmtop.logs"
    i = inotify.adapters.Inotify()
    i.add_watch(log_file)

    try:
        for event in i.event_gen(yield_nones=False):
            (_, type_names, path, filename) = event

            if "IN_MODIFY" in type_names:
                with open(log_file, 'r') as file:
                    lines = file.readlines()
                    last_line = lines[-1].strip()
                    t1 = Thread(target=send_data, args=(last_line,))
                    t1.run()

    finally:
        i.remove_watch(log_file)


def get_vm_last_known_cpu_time(vm_name):
    try:
        with open(f'./{vm_name}.dat', 'r') as f:
            time_and_cpu_time = f.read()
            if time_and_cpu_time:
                timestamp, cpu_time = [float(data) for data in time_and_cpu_time.split(',')]
                return timestamp, cpu_time
            return time.time(), 0.0
    except FileNotFoundError:
        return time.time(), 0.0


def set_vm_last_known_cpu_time(vm_name, cpu_time, timestamp):
    try:
        with open(f'./{vm_name}.dat', 'w') as f:
            return f.write(f"{timestamp}, {cpu_time}")
    except FileNotFoundError:
        return 0


def get_cpu_usage_percentage(vm):
    last_timestamp, prev_cpu_time = get_vm_last_known_cpu_time(vm.name())
    cpu_stats = vm.getCPUStats(True)[0]
    user_time = cpu_stats['user_time'] / 1000000000  # Convert from nanoseconds to seconds
    system_time = cpu_stats['system_time'] / 1000000000
    total_cpu_time = user_time + system_time

    # Calculate the CPU time used since the last measurement
    cpu_time_used = total_cpu_time - prev_cpu_time

    # Get the number of virtual CPUs
    v_cpus = vm.vcpus()[0]
    no_v_cpus = len(v_cpus)

    # Calculate CPU usage percentage
    current_time = time.time()
    duration = round(current_time - last_timestamp)
    if duration and no_v_cpus:
        cpu_usage_percentage = (cpu_time_used / (duration * no_v_cpus)) * 100  # 1 second interval
    else:
        cpu_usage_percentage = 0.0

    set_vm_last_known_cpu_time(vm.name(), total_cpu_time, current_time)

    return cpu_usage_percentage


def get_vms_and_host_stats():
    conn = libvirt.open("qemu:///system")
    try:
        stats = conn.getInfo()
        host_information = {
            "cpu_model": stats[0],
            "ram_total": stats[1]/1024,
            "cpu_cores": stats[2],
            "cpu_max_freq": stats[3],
            "cpu_numa_nodes": stats[4],
            "cpu_sockets_per_node": stats[5],
            "cpu_cores_per_socket": stats[6],
            "cpu_max_threads_per_core": stats[7]
        }
        vms = conn.listAllDomains()
        vm_stats = []
        if vms:
            for vm in vms:
                state, max_mem, mem, no_of_cpu, cpu_time = vm.info()
                stats = {
                    "cpu_cores": no_of_cpu,
                    "cpu_time": cpu_time / 1000000000,
                    "state": VM_STATE_DEFINITION.get(state),
                    "name": vm.name(),
                    "ram_max": max_mem,
                    "ram_actual": mem,
                }
                if state == libvirt.VIR_DOMAIN_RUNNING:
                    cpu_usage_percentage = get_cpu_usage_percentage(vm)
                    stats["cpu_usage"] = cpu_usage_percentage
                    mem_stat = vm.memoryStats()
                    for key, value in mem_stat.items():
                        stats.update({
                            f"ram_{key}": value
                        })

                    tree = ElementTree.fromstring(vm.XMLDesc())
                    disks = [path.get('file', '') for path in tree.findall("devices/disk/source")]
                    total_read_bytes, total_write_bytes = 0, 0
                    total_read_req, total_write_req, total_no_errors = 0, 0, 0
                    for disk in disks:
                        (rd_req, rd_bytes, wr_req, wr_bytes, err) = vm.blockStats(disk)
                        # stats.update({
                        #     "disk_id": disk,
                        #     'disk_no_read_req': rd_req,
                        #     'disk_read_bytes': rd_bytes,
                        #     'disk_no_write_req': wr_req,
                        #     'disk_write_bytes': wr_bytes,
                        #     'disk_no_errors': err,
                        # })
                        total_read_bytes += rd_bytes
                        total_write_bytes += wr_bytes
                        total_read_req += rd_req
                        total_write_req += wr_req
                        total_no_errors += total_no_errors
                    stats.update({
                        'io_read_bytes': total_read_bytes,
                        'io_write_bytes': total_write_bytes,
                        'io_read_req': total_read_req,
                        'io_write_req': total_write_req,
                        'io_no_errors': total_no_errors,
                    })

                    interface = tree.find("devices/interface/target").get("dev")
                    net_stats = vm.interfaceStats(interface)
                    stats.update({
                        'net_read_bytes': net_stats[0],
                        'net_read_packets': net_stats[1],
                        'net_read_errors': net_stats[2],
                        'net_read_drops': net_stats[3],
                        'net_write_bytes': net_stats[4],
                        'net_write_packets': net_stats[5],
                        'net_write_errors': net_stats[6],
                        'net_write_drops': net_stats[7],
                    })

                vm_stats.append(stats)

        return host_information, vm_stats

    except Exception as e:
        logger.debug(traceback.format_exc())
    finally:
        conn.close()




def collect_data():
    try:
        data = get_kvm_stats()
        return send_data(data)
    except Exception as e:
        logger.debug(traceback.format_exc())
    return False


if __name__ == "__main__":
    collect_data()
