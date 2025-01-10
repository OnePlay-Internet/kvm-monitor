#!/bin/bash

# Exit on any error
set -e

# kvmtop installation
echo "Installing kvmtop..."

# Download kvmtop
wget https://github.com/cha87de/kvmtop/releases/download/2.1.3/kvmtop_2.1.3_linux_amd64.deb

# Install kvmtop
sudo dpkg -i kvmtop_2.1.3_linux_amd64.deb

# Check for missing libncurses5.so and add repositories if necessary
if ! ldconfig -p | grep -q "libncurses5.so"; then
    echo "Missing libncurses5.so, adding repositories..."

    # Add repositories to /etc/apt/sources.list
    echo "deb http://security.ubuntu.com/ubuntu focal-security main" | sudo tee -a /etc/apt/sources.list
    echo "deb http://archive.ubuntu.com/ubuntu/ focal main restricted universe multiverse" | sudo tee -a /etc/apt/sources.list
    echo "deb http://archive.ubuntu.com/ubuntu/ focal-updates main restricted universe multiverse" | sudo tee -a /etc/apt/sources.list
    echo "deb http://security.ubuntu.com/ubuntu/ focal-security main restricted universe multiverse" | sudo tee -a /etc/apt/sources.list

    # Update package lists and install dependencies
    sudo apt update
    sudo apt upgrade -y
    sudo apt-get install libncurses5 libncurses5:i386 -y

    # If the i386 package fails, remove it and install only libncurses5
    if [ $? -ne 0 ]; then
        echo "Removing libncurses5:i386 due to installation failure..."
        sudo apt-get remove libncurses5:i386 -y
        sudo apt-get install libncurses5 -y
    fi
fi

# Verify kvmtop installation
kvmtop --version

# Clone the kvm-monitor repo and install
echo "Cloning kvm-monitor repository..."

git clone https://github.com/oneplay-internet/kvm-monitor.git
cd kvm-monitor

# Copy the service file to systemd
echo "Setting up kvm-monitor service..."
sudo cp kvm-monitor.service /etc/systemd/system

# Prompt for InfluxDB configurations
echo "Configuring InfluxDB..."

# Get InfluxDB URL, Token, Org, and Bucket
printf "Tell me your Influx URL: "
read influx_url
echo "INFLUX_URL=$influx_url" >> .env

printf "Tell me your Influx Token: "
read influx_token
echo "INFLUX_TOKEN=$influx_token" >> .env

printf "Tell me your Influx Org: "
read influx_org
echo "INFLUX_ORG=$influx_org" >> .env

printf "Tell me your Influx Bucket: "
read influx_bucket
echo "INFLUX_BUCKET=$influx_bucket" >> .env

# Get the disk path
echo "Fetching disk path..."
echo "DISK_PATH=$(fdisk -l | head -n 1 | cut -d' ' -f2 | tr -d ':')" >> .env

# Set up the Python environment
echo "Setting up Python virtual environment..."
python3 -m venv env
source env/bin/activate
pip3 install -r requirements.txt

# Enable and start the kvm-monitor service
echo "Enabling and starting kvm-monitor service..."
sudo systemctl daemon-reload
sudo systemctl enable --now kvm-monitor.service

echo "kvm-monitor installed and running!"
