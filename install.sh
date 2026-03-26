#!/usr/bin/env bash
set -e

echo "=== Aggiornamento pacchetti ==="
sudo apt update

echo "=== Installazione dipendenze di sistema ==="
sudo apt install -y python3-venv python3-pip redis-server chromium-browser chromium-chromedriver

echo "=== Abilitazione Redis ==="
sudo systemctl enable redis-server
sudo systemctl start redis-server

echo "=== Creazione virtualenv ==="
python3 -m venv venv
source venv/bin/activate

echo "=== Installazione dipendenze Python ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Creazione cartelle profili ==="
mkdir -p /home/azureuser/chrome-profiles/master
mkdir -p /home/azureuser/chrome-profiles/master-opener
mkdir -p /home/azureuser/chrome-profiles/worker-01
mkdir -p /home/azureuser/chrome-profiles/worker-02
mkdir -p /home/azureuser/chrome-profiles/worker-03

echo "=== Setup completato ==="
