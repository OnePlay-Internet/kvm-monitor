# System Monitoring Scripts

Modified for Monitoring End to End KVM + Libvirt Machines

## Prerequisites

Make sure you have the following installed on your system:

- Python 3.x
- InfluxDB
- [InfluxDB Python Client](https://github.com/influxdata/influxdb-client-python)

## VM Preparation

Install `kvmtop`
```commandline
wget https://github.com/cha87de/kvmtop/releases/download/2.1.3/kvmtop_2.1.3_linux_amd64.deb
sudo dpkg -i kvmtop_2.1.3_linux_amd64.deb
```
Try kvmtop it may fail with error saying missing package libncurses5.so
To fix it add below lines to `/etc/apt/sources.list` 
```commandline
deb http://security.ubuntu.com/ubuntu focal-security main
deb http://archive.ubuntu.com/ubuntu/ focal main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu/ focal-updates main restricted universe multiverse
deb http://security.ubuntu.com/ubuntu/ focal-security main restricted universe multiverse
```
And execute below commands:
```commandline
sudo apt update
sudo apt upgrade
sudo apt-get install libncurses5 libncurses5:i386
```
It will resolve this issue, try `kvmtop` command in terminal and verify everything working as expected

Note: If you got stuck with the above error then, remove `libncurses5:i386` and install only `libncurses5` (Sample Error message: E: Unable to locate package libncurses5:i386)


## Usage

1. Set up your InfluxDB configuration by creating a `.env` file with the following variables:

    ```env
    INFLUX_URL="https://your-influxdb-url:8086"
    INFLUX_TOKEN="your-influxdb-token"
    INFLUX_ORG="your-influxdb-organization"
    INFLUX_BUCKET="your-influxdb-bucket"
    DISK_PATH="disk-path-to-be-monitored"
    ```
2. Run the script:

    ```bash
    python system_monitor.py
    ```


