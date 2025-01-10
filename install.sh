#!/bin/sh

git clone https://github.com/bugswriter/pve2influx.git
cd pve2influx
cp pve2influx.service /etc/systemd/system

printf "Tell me your Influx URL: "
read influx_url
echo "INFLUX_URL=$influx_url" >> .env

printf "Tell me your Influx Token: "
read influx_token
echo "INFLUX_TOKEN=$influx_token" >> .env

printf "Tell me your Influx Org: "
read influx_org
echo "INFLUX_ORG=$influx_org" >> .env

printf "Tell me your Influx Bucket : "
read influx_bucket
echo "INFLUX_BUCKET=$influx_bucket" >> .env

echo "DISK_PATH=$(fdisk -l | head -n 1 | cut -d' ' -f2 | tr -d ':')" >> .env


python3 -m venv env
. env/bin/activate
pip3 install -r requirements.txt

systemctl daemon-reload
systemctl enable --now pve2influx.service
echo "pve2influx installed !!!"
