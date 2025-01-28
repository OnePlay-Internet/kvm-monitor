#!/bin/bash

# Exit on any error
set -e

# Ensure the script is run as root
if [ "$(id -u)" -ne 0 ]; then
    echo "You are NOT root. Please run this script as root."
    exit 1
fi

cd /root 2>/dev/null

# kvmtop installation
echo "Installing kvmtop..."

# Download kvmtop
wget https://github.com/cha87de/kvmtop/releases/download/2.1.3/kvmtop_2.1.3_linux_amd64.deb

# Install kvmtop
dpkg -i kvmtop_2.1.3_linux_amd64.deb || true

# Check and install missing dependencies
echo "Checking and installing dependencies..."
echo "deb http://security.ubuntu.com/ubuntu focal-security main" | tee -a /etc/apt/sources.list
echo "deb http://archive.ubuntu.com/ubuntu/ focal main restricted universe multiverse" | tee -a /etc/apt/sources.list
echo "deb http://archive.ubuntu.com/ubuntu/ focal-updates main restricted universe multiverse" | tee -a /etc/apt/sources.list
echo "deb http://security.ubuntu.com/ubuntu/ focal-security main restricted universe multiverse" | tee -a /etc/apt/sources.list

apt update
apt upgrade -y
apt install libncurses5 -y

# Verify kvmtop installation
kvmtop --version

# Clone the kvm-monitor repository and set up
echo "Cloning and setting up kvm-monitor..."
git clone https://github.com/oneplay-internet/kvm-monitor.git
cd kvm-monitor

# Copy the service file to systemd
cp kvm-monitor.service /etc/systemd/system

# Configure InfluxDB
echo "Configuring InfluxDB..."
read -p "Enter your Influx URL: " influx_url
read -p "Enter your Influx Token: " influx_token
read -p "Enter your Influx Org: " influx_org
read -p "Enter your Influx Bucket: " influx_bucket

cat <<EOF > .env
INFLUX_URL=$influx_url
INFLUX_TOKEN=$influx_token
INFLUX_ORG=$influx_org
INFLUX_BUCKET=$influx_bucket
DISK_PATH=$(fdisk -l | head -n 1 | cut -d' ' -f2 | tr -d ':')
EOF

# Set up the Python environment
echo "Setting up Python virtual environment..."
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

deactivate

# Enable and start the kvm-monitor service
echo "Enabling and starting kvm-monitor service..."
systemctl daemon-reload
systemctl enable --now kvm-monitor.service

echo "kvm-monitor installed and running!"
