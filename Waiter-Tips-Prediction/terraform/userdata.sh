#!/bin/bash
sudo apt update -y
cd /home/ubuntu
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt install python3.9 -y
alias python3=python3.9
sudo apt install awscli -y
mkdir Waiter-Tips-Prediction
echo 'export PATH="${HOME}:${PATH}"' >> .bashrc
echo 'alias python3=python3.9' >> .bashrc
echo 'export PGPASSWORD=password' >> .bashrc
source .bashrc
sudo apt install python3-pip -y
aws s3 cp s3://s3b-tip-predictor/config/requirements.txt ./Waiter-Tips-Prediction
aws s3 cp s3://s3b-tip-predictor/config/prometheus-config.yml ./Waiter-Tips-Prediction
aws s3 cp s3://s3b-tip-predictor/config/start.sh ./Waiter-Tips-Prediction
chmod +x ./Waiter-Tips-Prediction/start.sh
sudo pip install -r ./Waiter-Tips-Prediction/requirements.txt
sudo apt-get install -y apt-transport-https
sudo apt-get install -y software-properties-common wget
sudo wget -q -O /usr/share/keyrings/grafana.key https://packages.grafana.com/gpg.key
echo "deb [signed-by=/usr/share/keyrings/grafana.key] https://packages.grafana.com/oss/deb stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
sudo apt-get update
sudo apt-get install grafana -y
sudo systemctl daemon-reload
sudo systemctl start grafana-server
sudo systemctl enable grafana-server.service
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql.service
echo 'export AIRFLOW_HOME=/home/ubuntu/Waiter-Tips-Prediction' >> .bashrc
source .bashrc
sudo apt-get install build-essential procps curl file git -y