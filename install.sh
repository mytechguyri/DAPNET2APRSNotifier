#!/bin/bash
sudo apt-get -y install python3-pip
sudo pip3 install -r requirements.txt
sudo cp ./DAPNET2APRSNotifier /usr/local/bin/DAPNET2APRSNotifier
sudo chown mmdvm:mmdvm /usr/local/bin/DAPNET2APRSNotifier
sudo chmod +x /usr/local/bin/DAPNET2APRSNotifier
sudo cp ./dapnet2aprs /etc/dapnet2aprs
sudo chown mmdvm:mmdvm /etc/dapnet2aprs
sudo cp ./dapnet2aprs.service /lib/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable dapnet2aprs
sudo nano /etc/dapnet2aprs
