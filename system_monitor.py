import os
import time
import json
import importlib
import traceback

import schedule

from connection import create_influxdb_point, write_api, INFLUX_BUCKET, INFLUX_ORG
from modules import MONITORING_INTERVAL, logger


def load_config():
    with open('config/modules_config.json', 'r') as f:
        config = json.load(f)
    return config.get("modules", [])


def run_module(module_name):
    try:
        module = importlib.import_module(f"modules.{module_name}")
        data = module.collect_data()

        if module_name == 'kvm_monitor':
            return
        if data:
            if isinstance(data, list):
                # If collect data return multiple records
                for record in data:
                    point = create_influxdb_point(module_name, record)
                    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
                    logger.debug(f"writing record for {module_name} finished.")

            else:
                point = create_influxdb_point(module_name, data)
                write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
                logger.debug(f"writing record for {module_name} finished.")
    except Exception as e:
        logger.debug(traceback.format_exc())



if __name__ == '__main__':
    modules_config = load_config()
    for module_config in modules_config:
        module_name = module_config["name"]
        # interval_seconds = module_config.get("interval_seconds", False)

        schedule.every(MONITORING_INTERVAL).seconds.do(
            run_module, module_name=module_name)

    while True:
        schedule.run_pending()
        time.sleep(1)
