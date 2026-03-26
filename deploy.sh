#!/usr/bin/env bash
set -e

echo "=== Copia file systemd ==="
sudo cp systemd/whatsapp-master.service /etc/systemd/system/
sudo cp systemd/worker@.service /etc/systemd/system/

echo "=== Reload systemd ==="
sudo systemctl daemon-reload

echo "=== Enable services ==="
sudo systemctl enable whatsapp-master
sudo systemctl enable worker@01
sudo systemctl enable worker@02
sudo systemctl enable worker@03

echo "=== Restart services ==="
sudo systemctl restart whatsapp-master
sudo systemctl restart worker@01
sudo systemctl restart worker@02
sudo systemctl restart worker@03

echo "=== Stato servizi ==="
sudo systemctl --no-pager --full status whatsapp-master worker@01 worker@02 worker@03
